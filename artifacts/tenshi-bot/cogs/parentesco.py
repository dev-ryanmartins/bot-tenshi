"""Vínculos familiares pessoais e cargos estéticos do servidor."""

import json
import os
import unicodedata
from datetime import UTC, datetime

import discord

from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL


DATA_FILE = "data/cargos_parentesco.json"
VINCULOS = {
    "membro": ("Membro", "👤"),
    "filho": ("Filho", "👦"),
    "filha": ("Filha", "👧"),
    "irmao": ("Irmão", "👨"),
    "irma": ("Irmã", "👩"),
    "familiar": ("Familiar", "👨‍👩‍👧"),
}
PREFIXO_CARGO = "” ͎ᵎ  ⊰"


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(char for char in texto if not unicodedata.combining(char))


def _slug(texto: str) -> str:
    return "_".join(_normalizar(texto).split())


def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as arquivo:
        json.dump(data, arquivo, ensure_ascii=False, indent=2)


def nome_cargo_estetico(nome: str, emoji: str) -> str:
    return f"{PREFIXO_CARGO} {emoji}  {nome.strip()}"[:100]


def _registro_guild(guild_id: int) -> tuple[dict, dict]:
    data = _load()
    registro = data.setdefault(str(guild_id), {"roles": {}})
    registro.setdefault("roles", {})
    registro.setdefault("grupos", {})
    return data, registro


def _cargo_mapeado(guild: discord.Guild, role_id) -> discord.Role | None:
    try:
        return guild.get_role(int(role_id)) if role_id else None
    except (TypeError, ValueError):
        return None


def _buscar_cargo_existente(guild: discord.Guild, nome: str) -> discord.Role | None:
    alvo = _normalizar(nome)
    for role in guild.roles:
        if role.is_default() or role.managed:
            continue
        role_nome = _normalizar(role.name).strip()
        if role_nome == alvo or role_nome.endswith(f"  {alvo}") or role_nome.endswith(f" {alvo}"):
            return role
    return None


def _template_estetico(guild: discord.Guild, registro: dict) -> discord.Role | None:
    for role_id in registro["roles"].values():
        role = _cargo_mapeado(guild, role_id)
        if role:
            return role
    termos = tuple(_normalizar(item[0]) for item in VINCULOS.values())
    for role in reversed(guild.roles):
        if role.is_default() or role.managed:
            continue
        nome = _normalizar(role.name)
        if any(nome.endswith(termo) for termo in termos):
            return role
    return None


async def garantir_cargo_estetico(guild: discord.Guild, nome: str, emoji: str) -> discord.Role:
    """Obtém ou cria cargo sem permissões, usando a estética Tenshi e a cor familiar existente."""
    data, registro = _registro_guild(guild.id)
    chave = _slug(nome)
    cargo = _cargo_mapeado(guild, registro["roles"].get(chave)) or _buscar_cargo_existente(guild, nome)
    if cargo:
        registro["roles"][chave] = str(cargo.id)
        _save(data)
        return cargo

    template = _template_estetico(guild, registro)
    cor = template.color if template and template.color.value else discord.Color(0x9E7815)
    cargo = await guild.create_role(
        name=nome_cargo_estetico(nome, emoji),
        color=cor,
        permissions=discord.Permissions.none(),
        mentionable=True,
        hoist=False,
        reason=f"Cargo familiar estético criado pelo Tenshi Bot: {nome}",
    )
    if template:
        try:
            cargo = await cargo.edit(position=template.position, reason="Alinhamento com os cargos familiares") or cargo
        except discord.HTTPException:
            pass
    registro["roles"][chave] = str(cargo.id)
    _save(data)
    return cargo


async def garantir_cargo_grupo(guild: discord.Guild, nome: str, emoji: str, grupo: str) -> discord.Role:
    """Cria cargo estético em um grupo independente (prestígio, academia, soberania etc.)."""
    data, registro = _registro_guild(guild.id)
    mapa = registro["grupos"].setdefault(_slug(grupo), {})
    chave = _slug(nome)
    cargo = _cargo_mapeado(guild, mapa.get(chave)) or _buscar_cargo_existente(guild, nome)
    if cargo:
        mapa[chave] = str(cargo.id)
        _save(data)
        return cargo
    template = _template_estetico(guild, registro)
    cor = template.color if template and template.color.value else discord.Color(0x9E7815)
    cargo = await guild.create_role(
        name=nome_cargo_estetico(nome, emoji), color=cor,
        permissions=discord.Permissions.none(), mentionable=True, hoist=False,
        reason=f"Cargo estético do grupo {grupo}: {nome}",
    )
    if template:
        try:
            cargo = await cargo.edit(position=template.position, reason=f"Alinhamento estético: {grupo}") or cargo
        except discord.HTTPException:
            pass
    mapa[chave] = str(cargo.id)
    _save(data)
    return cargo


async def aplicar_cargo_exclusivo(member: discord.Member, nome: str, emoji: str, grupo: str) -> discord.Role:
    data, registro = _registro_guild(member.guild.id)
    mapa = registro["grupos"].setdefault(_slug(grupo), {})
    cargo = await garantir_cargo_grupo(member.guild, nome, emoji, grupo)
    # Recarrega o mapa porque a criação pode ter persistido um novo ID.
    _, atualizado = _registro_guild(member.guild.id)
    mapa = atualizado["grupos"].get(_slug(grupo), mapa)
    ids = {int(role_id) for role_id in mapa.values() if str(role_id).isdigit()}
    antigos = [role for role in member.roles if role.id in ids and role.id != cargo.id]
    if antigos:
        await member.remove_roles(*antigos, reason=f"Cargo exclusivo alterado: {grupo}")
    if cargo not in member.roles:
        await member.add_roles(cargo, reason=f"Cargo {grupo}: {nome}")
    return cargo


async def remover_cargos_grupo(member: discord.Member, grupo: str) -> None:
    _, registro = _registro_guild(member.guild.id)
    mapa = registro["grupos"].get(_slug(grupo), {})
    ids = {int(role_id) for role_id in mapa.values() if str(role_id).isdigit()}
    cargos = [role for role in member.roles if role.id in ids]
    if cargos:
        await member.remove_roles(*cargos, reason=f"Remoção de cargos do grupo {grupo}")


async def aplicar_parentesco(
    member: discord.Member,
    nome: str,
    emoji: str,
    atribuido_por: int | None = None,
    origem: str = "manual",
) -> discord.Role:
    data, registro = _registro_guild(member.guild.id)
    cargo = await garantir_cargo_estetico(member.guild, nome, emoji)
    ids_parentesco = {int(role_id) for role_id in registro["roles"].values() if str(role_id).isdigit()}
    antigos = [role for role in member.roles if role.id in ids_parentesco and role.id != cargo.id]
    if antigos:
        await member.remove_roles(*antigos, reason=f"Vínculo familiar alterado para {nome}")
    if cargo not in member.roles:
        await member.add_roles(cargo, reason=f"Vínculo familiar definido como {nome}")

    user = get_user(member.id)
    user["parentesco"] = nome
    user["parentesco_emoji"] = emoji
    user["cargo_parentesco_id"] = str(cargo.id)
    user["parentesco_origem"] = origem
    user["parentesco_atribuido_por"] = str(atribuido_por) if atribuido_por else None
    user["parentesco_atualizado_em"] = datetime.now(UTC).isoformat()
    save_user(member.id, user)
    return cargo


async def aplicar_membro_inicial(member: discord.Member) -> discord.Role | None:
    if member.bot:
        return None
    user = get_user(member.id)
    vinculo = user.get("parentesco") or "Membro"
    emoji = user.get("parentesco_emoji") or ("👤" if vinculo == "Membro" else "👪")
    origem = user.get("parentesco_origem") or "entrada"
    return await aplicar_parentesco(member, vinculo, emoji, origem=origem)


def _admin(member: discord.Member) -> bool:
    if member.id == IMPERADOR_ID:
        return True
    return bool(getattr(member, "guild_permissions", None) and member.guild_permissions.administrator)


def _embed(titulo: str, descricao: str, cor: int = 0x9E7815) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


class ParentescoPersonalizadoModal(discord.ui.Modal, title="Vínculo personalizado"):
    nome = discord.ui.TextInput(label="Nome do vínculo/cargo", placeholder="Ex.: Tia, Primo, Afilhada", max_length=50)
    emoji = discord.ui.TextInput(label="Emoji", placeholder="Ex.: 👪", required=False, max_length=20)

    def __init__(self, alvo: discord.Member, admin_id: int):
        super().__init__()
        self.alvo = alvo
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _admin(interaction.user):
            await interaction.response.send_message("Somente o administrador que abriu o painel pode concluir.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            cargo = await aplicar_parentesco(
                self.alvo, self.nome.value.strip(), self.emoji.value.strip() or "👪",
                interaction.user.id, "manual",
            )
            await interaction.followup.send(f"{self.alvo.mention} agora possui o vínculo {cargo.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("Não tenho permissão ou hierarquia para criar/aplicar esse cargo.", ephemeral=True)


class ParentescoSelect(discord.ui.Select):
    def __init__(self, alvo: discord.Member, admin_id: int):
        self.alvo = alvo
        self.admin_id = admin_id
        options = [
            discord.SelectOption(label=nome, value=chave, emoji=emoji)
            for chave, (nome, emoji) in VINCULOS.items()
        ]
        options.append(discord.SelectOption(label="Outro vínculo", value="personalizado", emoji="✍️"))
        super().__init__(placeholder="Selecione o vínculo familiar", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _admin(interaction.user):
            await interaction.response.send_message("Este painel pertence a outro administrador.", ephemeral=True)
            return
        escolha = self.values[0]
        if escolha == "personalizado":
            await interaction.response.send_modal(ParentescoPersonalizadoModal(self.alvo, self.admin_id))
            return
        nome, emoji = VINCULOS[escolha]
        await interaction.response.defer(ephemeral=True)
        try:
            cargo = await aplicar_parentesco(self.alvo, nome, emoji, interaction.user.id, "manual")
            await interaction.message.edit(
                embed=_embed("Vínculo familiar definido", f"{self.alvo.mention} agora é **{nome}**.\nCargo: {cargo.mention}", 0x1A5C2E),
                view=None,
            )
            await interaction.followup.send("Cargo aplicado e perfil atualizado.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("Não tenho permissão ou hierarquia para aplicar esse cargo.", ephemeral=True)


class ParentescoView(discord.ui.View):
    def __init__(self, alvo: discord.Member, admin_id: int):
        super().__init__(timeout=180)
        self.add_item(ParentescoSelect(alvo, admin_id))


class MembroSelect(discord.ui.UserSelect):
    def __init__(self, admin_id: int):
        super().__init__(placeholder="Selecione o membro da família")
        self.admin_id = admin_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _admin(interaction.user):
            await interaction.response.send_message("Este painel pertence a outro administrador.", ephemeral=True)
            return
        alvo = self.values[0]
        await interaction.response.edit_message(
            embed=_embed("Definir parentesco", f"Membro selecionado: {alvo.mention}\nEscolha agora o vínculo familiar."),
            view=ParentescoView(alvo, self.admin_id),
        )


class MembroView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=180)
        self.add_item(MembroSelect(admin_id))


class Parentesco:
    def __init__(self, bot):
        self.bot = bot

    async def handle_parentesco(self, message, args):
        if not _admin(message.author):
            await message.channel.send(embed=_embed("Acesso restrito", "Somente administradores podem definir vínculos.", 0x7B1F1F))
            return
        if not message.guild.me or not message.guild.me.guild_permissions.manage_roles:
            await message.channel.send(embed=_embed("Permissão necessária", "Conceda ao bot **Gerenciar Cargos** e mantenha seu cargo acima dos cargos familiares.", 0x7B1F1F))
            return
        if message.mentions:
            alvo = message.mentions[0]
            embed = _embed("Definir parentesco", f"Membro: {alvo.mention}\nEscolha o vínculo familiar abaixo.")
            view = ParentescoView(alvo, message.author.id)
        else:
            embed = _embed("Selecionar membro da família", "Escolha primeiro a pessoa que receberá o vínculo.")
            view = MembroView(message.author.id)
        await message.channel.send(embed=embed, view=view)
