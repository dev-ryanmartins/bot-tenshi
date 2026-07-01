import json
import os
from datetime import UTC, datetime

import discord

from database import get_user
from ia_router import ia_relatorio
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, SEP


DATA_FILE = "data/cargos_funcoes.json"
COR_DOURADO = 0x9E7815
COR_IMPERIAL = 0x2C3E50
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


PERMISSOES_RELEVANTES = {
    "administrator": "Administrador",
    "manage_guild": "Gerenciar servidor",
    "manage_roles": "Gerenciar cargos",
    "manage_channels": "Gerenciar canais",
    "manage_messages": "Gerenciar mensagens",
    "ban_members": "Banir membros",
    "kick_members": "Expulsar membros",
    "moderate_members": "Moderar membros",
    "manage_webhooks": "Gerenciar webhooks",
    "mention_everyone": "Mencionar everyone",
}

SECOES_PADRAO = [
    ("⚜️", "Coroa e Soberania"),
    ("🛡️", "Administracao e Staff"),
    ("⚖️", "Moderacao e Juridico"),
    ("📜", "Operacoes e Comunidade"),
    ("🎁", "Beneficios e Progressao"),
    ("👥", "Membros e Identidade"),
]


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


def _permissoes_role(role: discord.Role) -> list[str]:
    return [label for attr, label in PERMISSOES_RELEVANTES.items() if getattr(role.permissions, attr, False)]


def _categoria_role(role: discord.Role) -> str:
    nome = role.name.lower()
    perms = role.permissions
    if any(t in nome for t in ("fundador", "imperador", "rei", "rainha", "coroa")):
        return "Coroa e Soberania"
    if perms.administrator or any(t in nome for t in ("staff", "admin", "adm", "moderador")):
        return "Administracao e Staff"
    if perms.ban_members or perms.kick_members or perms.moderate_members or any(t in nome for t in ("aprovador", "monitor", "ficha")):
        return "Moderacao e Juridico"
    if any(t in nome for t in ("evento", "aniversariante", "planejador", "designer", "correio")):
        return "Operacoes e Comunidade"
    if any(t in nome for t in ("vip", "boost", "bost", "xp")):
        return "Beneficios e Progressao"
    return "Membros e Identidade"


def _funcao_padrao(role: discord.Role) -> str:
    nome = role.name.lower()
    perms = _permissoes_role(role)
    if "fundador" in nome:
        return "Autoridade originaria do servidor, preserva direcao, continuidade e identidade da Casa."
    if "rei" in nome or "imperador" in nome:
        return "Autoridade soberana para decretos, cargos, cerimonias reais e direcao administrativa."
    if "rainha" in nome:
        return "Autoridade ao lado da Coroa, apoio cerimonial, governanca e representacao da Casa."
    if "staff" in nome:
        return "Equipe operacional do servidor: suporte, ordem, acolhimento e execucao de protocolos."
    if "aprovador" in nome or "ficha" in nome:
        return "Analisa, corrige e aprova fichas para manter equilibrio narrativo do RPG."
    if "designer" in nome:
        return "Cuida de identidade visual, artes, banners, embeds e padrao estetico do Imperio."
    if "correio" in nome:
        return "Monitora e organiza o correio narrativo, registros e comunicacoes internas."
    if "evento" in nome or "planejador" in nome:
        return "Planeja eventos, cronicas, chamadas, cerimonias e atividades coletivas."
    if "vip" in nome or "boost" in nome or "bost" in nome:
        return "Cargo de beneficio, destaque ou progressao, sem autoridade administrativa por padrao."
    if perms:
        return f"Cargo com permissões sensiveis: {', '.join(perms)}. Requer supervisao administrativa."
    return "Cargo de identidade, titulo, progressao ou pertencimento narrativo."


def _role_snapshot(role: discord.Role) -> dict:
    return {
        "id": str(role.id),
        "nome": role.name,
        "posicao": role.position,
        "cor": str(role.color),
        "mencionavel": role.mentionable,
        "gerenciado": role.managed,
        "membros": len(role.members),
        "permissoes": _permissoes_role(role),
        "categoria": _categoria_role(role),
        "funcao": _funcao_padrao(role),
    }


def gerar_mapa_guild(guild: discord.Guild) -> dict:
    roles = [r for r in sorted(guild.roles, key=lambda x: x.position, reverse=True) if not r.is_default()]
    return {
        "guild_id": str(guild.id),
        "guild_name": guild.name,
        "updated_at": _agora(),
        "roles": {str(role.id): _role_snapshot(role) for role in roles},
        "ia_plano": None,
    }


def salvar_mapa_guild(guild: discord.Guild, mapa: dict):
    data = _load()
    anterior = data.get(str(guild.id), {})
    if anterior.get("ia_plano") and not mapa.get("ia_plano"):
        mapa["ia_plano"] = anterior["ia_plano"]
    data[str(guild.id)] = mapa
    _save(data)


class CargosAdmin:
    def __init__(self, bot):
        self.bot = bot

    def _is_admin(self, member: discord.Member) -> bool:
        if member.id == IMPERADOR_ID:
            return True
        try:
            if member.guild_permissions.administrator or member.guild_permissions.manage_roles or member.guild_permissions.manage_guild:
                return True
        except Exception:
            pass
        return bool(get_user(member.id).get("co_soberano"))

    async def handle_cargos_servidor(self, message, args):
        roles = [r for r in sorted(message.guild.roles, key=lambda x: x.position, reverse=True) if not r.is_default()]
        if not roles:
            await message.channel.send(embed=_embed("Cargos do Servidor", "Nenhum cargo encontrado.", COR_NEUTRO))
            return
        linhas = []
        for role in roles[:40]:
            perms = ", ".join(_permissoes_role(role)[:3]) or "sem permissao sensivel"
            linhas.append(f"**{role.name}** — {len(role.members)} membro(s) — {perms}")
        extra = f"\n\n*+{len(roles) - 40} cargos ocultos nesta pagina.*" if len(roles) > 40 else ""
        await message.channel.send(embed=_embed("Cargos do Servidor", "\n".join(linhas)[:3800] + extra, COR_IMPERIAL))

    async def handle_mapear_cargos(self, message, args):
        if not self._is_admin(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "Somente administracao imperial pode mapear cargos.", COR_PERIGO))
            return
        mapa = gerar_mapa_guild(message.guild)
        salvar_mapa_guild(message.guild, mapa)
        categorias: dict[str, int] = {}
        for role in mapa["roles"].values():
            categorias[role["categoria"]] = categorias.get(role["categoria"], 0) + 1
        resumo = "\n".join(f"**{cat}:** {qtd}" for cat, qtd in categorias.items())
        await message.channel.send(embed=_embed(
            "Mapa de Cargos Atualizado",
            f"Foram registrados **{len(mapa['roles'])} cargos** do servidor.\n\n{resumo}\n\n"
            f"Use `Tenshi, publicar-mapa-cargos` para publicar o manual resumido.",
            COR_DOURADO,
        ))

    async def handle_cargo_info(self, message, args):
        role = message.role_mentions[0] if message.role_mentions else None
        if not role and args:
            nome = " ".join(args).lower()
            role = next((r for r in message.guild.roles if nome in r.name.lower()), None)
        if not role:
            await message.channel.send(embed=_embed("Cargo Nao Encontrado", "Use: `Tenshi, cargo-info @cargo`", COR_NEUTRO))
            return
        snap = _role_snapshot(role)
        await message.channel.send(embed=_embed(
            f"Funcao do Cargo - {role.name}",
            f"**Categoria:** {snap['categoria']}\n"
            f"**Membros:** {snap['membros']}\n"
            f"**Permissoes:** {', '.join(snap['permissoes']) or 'sem permissao sensivel'}\n\n"
            f"**Funcao sugerida:** {snap['funcao']}",
            COR_DOURADO,
        ))

    async def handle_funcao_cargo(self, message, args):
        if not self._is_admin(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "Somente administracao imperial pode alterar funcoes.", COR_PERIGO))
            return
        role = message.role_mentions[0] if message.role_mentions else None
        if not role:
            await message.channel.send(embed=_embed("Parametro Invalido", "Use: `Tenshi, funcao-cargo @cargo [funcao]`", COR_NEUTRO))
            return
        texto = " ".join(a for a in args if not a.startswith("<@&")).strip()
        if not texto:
            await message.channel.send(embed=_embed("Parametro Invalido", "Informe a funcao do cargo.", COR_NEUTRO))
            return
        data = _load()
        guild_data = data.get(str(message.guild.id)) or gerar_mapa_guild(message.guild)
        guild_data.setdefault("roles", {})
        guild_data["roles"].setdefault(str(role.id), _role_snapshot(role))
        guild_data["roles"][str(role.id)]["funcao"] = texto[:700]
        guild_data["roles"][str(role.id)]["updated_at"] = _agora()
        data[str(message.guild.id)] = guild_data
        _save(data)
        await message.channel.send(embed=_embed("Funcao Registrada", f"**{role.name}:** {texto[:900]}", COR_DOURADO))

    async def handle_publicar_mapa(self, message, args):
        data = _load()
        mapa = data.get(str(message.guild.id))
        if not mapa:
            mapa = gerar_mapa_guild(message.guild)
            salvar_mapa_guild(message.guild, mapa)
        por_categoria: dict[str, list[dict]] = {}
        for role in mapa.get("roles", {}).values():
            por_categoria.setdefault(role.get("categoria", "Outros"), []).append(role)
        for categoria, roles in por_categoria.items():
            linhas = [f"**{r['nome']}** — {r.get('funcao', 'sem funcao')}" for r in roles[:12]]
            await message.channel.send(embed=_embed(f"Manual de Cargos - {categoria}", "\n".join(linhas)[:3800], COR_IMPERIAL))
        if mapa.get("ia_plano"):
            await message.channel.send(embed=_embed("Plano de Organizacao por IA", str(mapa["ia_plano"])[:3800], COR_DOURADO))

    async def handle_auditoria_cargos_ia(self, message, args):
        if not self._is_admin(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "Somente administracao imperial pode solicitar auditoria de cargos.", COR_PERIGO))
            return
        mapa = gerar_mapa_guild(message.guild)
        role_lines = []
        for role in mapa["roles"].values():
            role_lines.append(
                f"- {role['nome']} | cat atual: {role['categoria']} | membros: {role['membros']} | perms: {', '.join(role['permissoes']) or 'nenhuma'}"
            )
        prompt = (
            "Voce e a IA administrativa da Casa Tenshi. Organize os cargos do servidor em secoes claras. "
            "Para cada grupo, explique o que cada cargo faz, quais cargos tem risco administrativo, e quais "
            "funcoes devem ficar separadas para evitar confusao. Nao invente permissoes que nao foram listadas. "
            "Use formato com titulos curtos e bullets objetivos."
        )
        resposta = await ia_relatorio(prompt, "\n".join(role_lines)[:12000], max_tokens=1600)
        mapa["ia_plano"] = resposta
        salvar_mapa_guild(message.guild, mapa)
        partes = [resposta[i:i + 3600] for i in range(0, len(resposta), 3600)] or ["Sem resposta da IA."]
        for idx, parte in enumerate(partes[:3], start=1):
            await message.channel.send(embed=_embed(f"Auditoria de Cargos por IA ({idx}/{min(len(partes), 3)})", parte, COR_DOURADO))

    async def handle_criar_secoes_cargos(self, message, args):
        if not self._is_admin(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "Somente administracao imperial pode criar secoes de cargos.", COR_PERIGO))
            return
        criados = []
        existentes = []
        for emoji, nome in SECOES_PADRAO:
            role_name = f"” ͎ᵎ  ⊰ {emoji}  {nome}"
            atual = discord.utils.get(message.guild.roles, name=role_name)
            if atual:
                existentes.append(role_name)
                continue
            try:
                role = await message.guild.create_role(
                    name=role_name[:100],
                    color=discord.Color(0x9E7815),
                    mentionable=False,
                    reason=f"Secao de cargos criada por {message.author} via Tenshi Bot",
                )
                criados.append(role.name)
            except discord.Forbidden:
                await message.channel.send(embed=_embed("Permissao Negada", "Nao tenho permissao/hierarquia para criar secoes de cargos.", COR_PERIGO))
                return
        desc = (
            f"**Criados:** {len(criados)}\n"
            f"{chr(10).join(f'- {c}' for c in criados) if criados else '- nenhum'}\n\n"
            f"**Ja existiam:** {len(existentes)}"
        )
        await message.channel.send(embed=_embed("Secoes de Cargos Preparadas", desc[:3800], COR_DOURADO))
