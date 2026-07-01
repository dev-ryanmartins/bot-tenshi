import json
import os
from datetime import UTC, datetime

import discord

from database import get_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, SEP


DATA_FILE = "data/permissoes_canais.json"
COR_DOURADO = 0x9E7815
COR_IMPERIAL = 0x2C3E50
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


BOT_TEXT_PERMS = {
    "view_channel": "Ver canal",
    "send_messages": "Enviar mensagens",
    "send_messages_in_threads": "Enviar em threads",
    "embed_links": "Enviar embeds",
    "read_message_history": "Ler historico",
    "add_reactions": "Adicionar reacoes",
    "attach_files": "Anexar arquivos",
    "use_external_emojis": "Usar emojis externos",
}

BOT_MOD_TEXT_PERMS = {
    **BOT_TEXT_PERMS,
    "manage_messages": "Gerenciar mensagens",
}

BOT_VOICE_PERMS = {
    "view_channel": "Ver canal",
    "connect": "Conectar",
    "speak": "Falar",
}

PERFIS_CANAL = {
    "publico": "Chat aberto para membros; bot pode responder, enviar embeds e registrar eventos.",
    "staff": "Canal restrito a equipe; bot pode operar moderacao, auditoria e relatorios.",
    "fichas": "Canal de criacao/aprovacao de ficha; bot e aprovadores trabalham juntos.",
    "cerimonial": "Canal de ritos, casamento, clero e eventos formais.",
    "correio": "Canal de correio e comunicacoes; bot e monitores organizam mensagens.",
    "logs": "Canal de registros administrativos; bot escreve e equipe acompanha.",
}


def _agora() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat()


def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


def _nome_total(channel) -> str:
    categoria = getattr(getattr(channel, "category", None), "name", None)
    return f"{categoria or ''} {channel.name}".lower()


def _perfil_sugerido(channel) -> str:
    nome = _nome_total(channel)
    if any(t in nome for t in ("log", "registro", "auditoria")):
        return "logs"
    if any(t in nome for t in ("staff", "admin", "modera", "equipe", "chancelaria")):
        return "staff"
    if any(t in nome for t in ("ficha", "aprova", "personagem", "registro-rpg")):
        return "fichas"
    if any(t in nome for t in ("casamento", "matrimonio", "matrimônio", "clero", "igreja", "rito", "cerimonia", "cerimônia")):
        return "cerimonial"
    if "correio" in nome:
        return "correio"
    return "publico"


def _is_textual(channel) -> bool:
    return isinstance(channel, (discord.TextChannel, discord.ForumChannel))


def _is_voice(channel) -> bool:
    return isinstance(channel, (discord.VoiceChannel, discord.StageChannel))


def _required_bot_perms(channel, perfil: str | None = None) -> dict[str, str]:
    perfil = perfil or _perfil_sugerido(channel)
    if _is_voice(channel):
        return BOT_VOICE_PERMS
    if perfil in {"staff", "logs"}:
        return BOT_MOD_TEXT_PERMS
    return BOT_TEXT_PERMS


def _missing_permissions(channel, member: discord.Member, perfil: str | None = None) -> list[str]:
    perms = channel.permissions_for(member)
    missing = []
    for attr, label in _required_bot_perms(channel, perfil).items():
        if not getattr(perms, attr, False):
            missing.append(label)
    return missing


def _overwrite_from_required(channel, perfil: str | None = None) -> discord.PermissionOverwrite:
    overwrite = discord.PermissionOverwrite()
    for attr in _required_bot_perms(channel, perfil):
        setattr(overwrite, attr, True)
    return overwrite


def _staff_roles(guild: discord.Guild) -> list[discord.Role]:
    termos = ("fundador", "imperador", "rei", "rainha", "staff", "admin", "adm", "moderador", "mod", "aprovador", "clero")
    roles = []
    for role in guild.roles:
        nome = role.name.lower()
        if any(t in nome for t in termos) or role.permissions.administrator or role.permissions.manage_guild:
            roles.append(role)
    return roles


def _aprovador_roles(guild: discord.Guild) -> list[discord.Role]:
    termos = ("aprovador", "ficha", "staff", "admin", "moderador", "clero")
    return [role for role in guild.roles if any(t in role.name.lower() for t in termos) or role.permissions.administrator]


def _clero_roles(guild: discord.Guild) -> list[discord.Role]:
    termos = ("clero", "padre", "celebrante", "rei", "rainha", "fundador", "staff", "admin")
    return [role for role in guild.roles if any(t in role.name.lower() for t in termos) or role.permissions.administrator]


class PermissoesCanais:
    def __init__(self, bot):
        self.bot = bot

    def _is_admin(self, member: discord.Member) -> bool:
        if member.id == IMPERADOR_ID:
            return True
        try:
            if member.guild_permissions.administrator or member.guild_permissions.manage_channels:
                return True
        except Exception:
            pass
        return bool(get_user(member.id).get("co_soberano"))

    def _audit_guild(self, guild: discord.Guild) -> dict:
        me = guild.me
        canais = []
        for channel in guild.channels:
            if isinstance(channel, discord.CategoryChannel):
                continue
            if not (_is_textual(channel) or _is_voice(channel)):
                continue
            perfil = _perfil_sugerido(channel)
            missing = _missing_permissions(channel, me, perfil) if me else ["Bot nao encontrado no servidor"]
            canais.append({
                "id": str(channel.id),
                "nome": channel.name,
                "categoria": getattr(getattr(channel, "category", None), "name", None),
                "tipo": "voz" if _is_voice(channel) else "texto",
                "perfil": perfil,
                "faltando": missing,
                "ok": not missing,
            })
        return {
            "guild_id": str(guild.id),
            "guild_name": guild.name,
            "updated_at": _agora(),
            "canais": canais,
        }

    def _save_audit(self, guild: discord.Guild, audit: dict):
        data = _load()
        data[str(guild.id)] = audit
        _save(data)

    async def handle_auditoria_permissoes(self, message, args):
        if not self._is_admin(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "Somente administracao imperial pode auditar permissoes.", COR_PERIGO))
            return
        audit = self._audit_guild(message.guild)
        self._save_audit(message.guild, audit)
        faltando = [c for c in audit["canais"] if not c["ok"]]
        por_perfil: dict[str, int] = {}
        for c in audit["canais"]:
            por_perfil[c["perfil"]] = por_perfil.get(c["perfil"], 0) + 1
        resumo = "\n".join(f"**{perfil}:** {qtd}" for perfil, qtd in sorted(por_perfil.items()))
        problemas = "\n".join(
            f"**#{c['nome']}** ({c['perfil']}): {', '.join(c['faltando'][:5])}"
            for c in faltando[:12]
        ) or "Nenhuma permissao essencial faltando para o bot."
        await message.channel.send(embed=_embed(
            "Auditoria de Permissoes dos Chats",
            f"**Canais analisados:** {len(audit['canais'])}\n"
            f"**Canais com falta:** {len(faltando)}\n\n"
            f"{resumo}\n\n{SEP}\n{problemas}\n\n"
            f"Para corrigir apenas o acesso do bot: `Tenshi, corrigir-permissoes-bot`",
            COR_DOURADO if faltando else COR_SUCESSO,
        ))

    async def handle_corrigir_permissoes_bot(self, message, args):
        if not self._is_admin(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "Somente administracao imperial pode corrigir permissoes.", COR_PERIGO))
            return
        me = message.guild.me
        if not me:
            await message.channel.send(embed=_embed("Erro", "Nao consegui localizar meu membro no servidor.", COR_PERIGO))
            return
        corrigidos = []
        falhas = []
        for channel in message.guild.channels:
            if isinstance(channel, discord.CategoryChannel):
                continue
            if not (_is_textual(channel) or _is_voice(channel)):
                continue
            perfil = _perfil_sugerido(channel)
            missing = _missing_permissions(channel, me, perfil)
            if not missing:
                continue
            try:
                await channel.set_permissions(
                    me,
                    overwrite=_overwrite_from_required(channel, perfil),
                    reason=f"Permissoes essenciais do Tenshi Bot corrigidas por {message.author}",
                )
                corrigidos.append(channel.name)
            except Exception as exc:
                falhas.append(f"{channel.name}: {str(exc)[:80]}")
        audit = self._audit_guild(message.guild)
        self._save_audit(message.guild, audit)
        desc = (
            f"**Canais corrigidos:** {len(corrigidos)}\n"
            f"{chr(10).join(f'- {c}' for c in corrigidos[:20]) if corrigidos else '- nenhum'}\n\n"
            f"**Falhas:** {len(falhas)}\n"
            f"{chr(10).join(f'- {f}' for f in falhas[:8]) if falhas else '- nenhuma'}"
        )
        await message.channel.send(embed=_embed("Permissoes do Bot Atualizadas", desc[:3800], COR_SUCESSO if not falhas else COR_DOURADO))

    async def handle_mapa_canais(self, message, args):
        audit = self._audit_guild(message.guild)
        por_perfil: dict[str, list[dict]] = {}
        for canal in audit["canais"]:
            por_perfil.setdefault(canal["perfil"], []).append(canal)
        for perfil, canais in por_perfil.items():
            linhas = [f"**#{c['nome']}** — {'OK' if c['ok'] else 'falta: ' + ', '.join(c['faltando'][:3])}" for c in canais[:15]]
            await message.channel.send(embed=_embed(
                f"Mapa de Chats - {perfil.title()}",
                f"{PERFIS_CANAL.get(perfil, 'Perfil administrativo.')}\n\n" + "\n".join(linhas),
                COR_IMPERIAL,
            ))

    async def handle_aplicar_perfil_canal(self, message, args):
        if not self._is_admin(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "Somente administracao imperial pode aplicar perfil em chat.", COR_PERIGO))
            return
        if not message.channel_mentions or len(args) < 2:
            perfis = ", ".join(PERFIS_CANAL)
            await message.channel.send(embed=_embed(
                "Parametro Invalido",
                f"Use: `Tenshi, aplicar-perfil-canal #canal [perfil]`\nPerfis: {perfis}",
                COR_NEUTRO,
            ))
            return
        canal = message.channel_mentions[0]
        perfil = args[-1].lower()
        if perfil not in PERFIS_CANAL:
            await message.channel.send(embed=_embed("Perfil Invalido", f"Perfis validos: {', '.join(PERFIS_CANAL)}", COR_NEUTRO))
            return
        overwrites = {}
        everyone = message.guild.default_role
        if perfil == "publico":
            overwrites[everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        elif perfil in {"staff", "logs"}:
            overwrites[everyone] = discord.PermissionOverwrite(view_channel=False)
            for role in _staff_roles(message.guild):
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        elif perfil == "fichas":
            overwrites[everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            for role in _aprovador_roles(message.guild):
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
        elif perfil == "cerimonial":
            overwrites[everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)
            for role in _clero_roles(message.guild):
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        elif perfil == "correio":
            overwrites[everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            for role in _staff_roles(message.guild):
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)

        if message.guild.me:
            overwrites[message.guild.me] = _overwrite_from_required(canal, perfil)

        try:
            await canal.edit(overwrites=overwrites, reason=f"Perfil {perfil} aplicado por {message.author} via Tenshi Bot")
            await message.channel.send(embed=_embed(
                "Perfil de Chat Aplicado",
                f"**Canal:** {canal.mention}\n**Perfil:** {perfil}\n**Funcao:** {PERFIS_CANAL[perfil]}",
                COR_SUCESSO,
            ))
        except discord.Forbidden:
            await message.channel.send(embed=_embed("Permissao Negada", "Nao tenho permissao/hierarquia para editar este canal.", COR_PERIGO))
        except Exception as exc:
            await message.channel.send(embed=_embed("Erro", f"Nao foi possivel aplicar o perfil: {str(exc)[:120]}", COR_PERIGO))
