"""Painel visual e navegável para os pergaminhos de ajuda do Tenshi Bot."""

import re

import discord
from discord import app_commands
from discord.ext import commands

from utils import AJUDA_TEXTO, RODAPE_IMPERIAL, SITE_URL


COR_AJUDA = 0x6D28D9
PADRAO_TITULO = re.compile(r"^\*\*(.+?)\*\*(?:\s+.*)?$")


def categorias_ajuda(texto: str = AJUDA_TEXTO) -> list[tuple[str, str]]:
    """Divide o texto mestre em categorias pequenas o bastante para embeds."""
    try:
        categorias: list[tuple[str, str]] = []
        titulo: str | None = None
        linhas: list[str] = []
        for linha in texto.strip().splitlines():
            encontrado = PADRAO_TITULO.match(linha.strip())
            if encontrado:
                novo_titulo = encontrado.group(1).strip()
                if "PERGAMINHOS IMPERIAIS" in novo_titulo:
                    continue
                if titulo:
                    categorias.append((titulo, "\n".join(linhas).strip()))
                titulo, linhas = novo_titulo, []
            elif titulo and linha.strip() not in {"", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"}:
                linhas.append(linha.rstrip())
        if titulo:
            categorias.append((titulo, "\n".join(linhas).strip()))
        return [(nome, corpo[:4000]) for nome, corpo in categorias if corpo]
    except Exception as e:
        print(f"Erro ao processar categorias de ajuda: {e}")
        # Retornar categorias básicas em caso de erro
        return [
            ("🏛️ Central de Comandos", "Use `/ajuda` para ver todos os comandos disponíveis."),
            ("🔧 Utilitários", "ping, servidor, top, backup, bandeira, brasao, historia-tenshi, base-historica, status-ia, aniversario"),
            ("🛡️ Proteção Imperial", "protecao-imperial, ativar-protecao, desativar-protecao, confianca, remover-confianca, bloquear-servidor, desbloquear-servidor, atividade-suspeita"),
            ("🤝 Sistema de Parcerias", "parceria, historico-parcerias"),
            ("🔒 Moderação de Conteúdo", "config-moderacao, bloquear-link, desbloquear-link, adicionar-dominio-confianca, remover-dominio-confianca"),
        ]


AJUDA_CATEGORIAS = categorias_ajuda()


def embed_inicio(guild=None, user=None) -> discord.Embed:
    embed = discord.Embed(
        title="🏛️ Central de Comandos — Tenshi",
        description=(
            "Escolha uma categoria no menu para abrir seus pergaminhos.\n\n"
            "⌨️ **Prefixos:** `tenshi comando` ou `Tenshi, comando`\n"
            "⚙️ **Painéis:** menus, botões e formulários aparecem quando necessários\n"
            f"🌐 **Guia:** {SITE_URL}"
        ),
        color=COR_AJUDA,
    )
    nomes = [nome for nome, _ in AJUDA_CATEGORIAS]
    metade = (len(nomes) + 1) // 2
    embed.add_field(name="📜 Categorias", value="\n".join(f"• {nome}" for nome in nomes[:metade]), inline=True)
    embed.add_field(name="📚 Continuação", value="\n".join(f"• {nome}" for nome in nomes[metade:]), inline=True)
    embed.add_field(
        name="🔎 Atalhos úteis",
        value="`tenshi ajuda` • `tenshi comandos` • `tenshi meu-parentesco` • `tenshi ping`",
        inline=False,
    )
    embed.set_footer(text=f"{len(AJUDA_CATEGORIAS)} categorias • {RODAPE_IMPERIAL}")
    if guild and getattr(guild, "icon", None):
        embed.set_thumbnail(url=guild.icon.url)
    if user:
        embed.set_author(name=f"Pergaminhos de {user.display_name}", icon_url=user.display_avatar.url)
    return embed


def embed_categoria(indice: int) -> discord.Embed:
    titulo, corpo = AJUDA_CATEGORIAS[indice]
    embed = discord.Embed(title=titulo, description=corpo, color=COR_AJUDA)
    embed.set_footer(text=f"Pergaminho {indice + 1}/{len(AJUDA_CATEGORIAS)} • {RODAPE_IMPERIAL}")
    return embed


class CategoriaAjudaSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome[:100], value=str(indice), description="Abrir esta categoria")
            for indice, (nome, _) in enumerate(AJUDA_CATEGORIAS)
        ]
        super().__init__(placeholder="Escolha uma categoria de comandos", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.indice = int(self.values[0])
        await interaction.response.edit_message(embed=embed_categoria(self.view.indice), view=self.view)


class PainelAjudaView(discord.ui.View):
    def __init__(self, autor_id: int):
        super().__init__(timeout=300)
        self.autor_id = autor_id
        self.indice: int | None = None
        self.add_item(CategoriaAjudaSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.autor_id:
            return True
        await interaction.response.send_message("Abra seu próprio painel com `tenshi ajuda`.", ephemeral=True)
        return False

    @discord.ui.button(label="Anterior", emoji="◀️", style=discord.ButtonStyle.secondary, row=1)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.indice = (self.indice - 1) % len(AJUDA_CATEGORIAS) if self.indice is not None else len(AJUDA_CATEGORIAS) - 1
        await interaction.response.edit_message(embed=embed_categoria(self.indice), view=self)

    @discord.ui.button(label="Início", emoji="🏛️", style=discord.ButtonStyle.primary, row=1)
    async def inicio(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.indice = None
        await interaction.response.edit_message(embed=embed_inicio(), view=self)

    @discord.ui.button(label="Próximo", emoji="▶️", style=discord.ButtonStyle.secondary, row=1)
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.indice = (self.indice + 1) % len(AJUDA_CATEGORIAS) if self.indice is not None else 0
        await interaction.response.edit_message(embed=embed_categoria(self.indice), view=self)

    @discord.ui.button(label="Fechar", emoji="✖️", style=discord.ButtonStyle.danger, row=1)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(
            embed=discord.Embed(title="📕 Pergaminhos recolhidos", description="Use `tenshi ajuda` quando precisar novamente.", color=0x3F3F46),
            view=None,
        )


async def enviar_ajuda(message) -> None:
    try:
        await message.channel.send(
            embed=embed_inicio(message.guild, message.author),
            view=PainelAjudaView(message.author.id),
        )
    except Exception as e:
        print(f"Erro ao enviar ajuda: {e}")
        # Fallback simples se houver erro
        embed = discord.Embed(
            title="🏛️ Central de Comandos — Tenshi",
            description=f"Use o comando `/ajuda` para ver todos os comandos disponíveis.\n\n🌐 Guia: {SITE_URL}",
            color=COR_AJUDA,
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)


class AjudaCog(commands.Cog):
    """Disponibiliza a mesma central também no comando de barra /ajuda."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ajuda", description="Abre a central interativa com todos os comandos do Tenshi.")
    async def ajuda_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=embed_inicio(interaction.guild, interaction.user),
            view=PainelAjudaView(interaction.user.id),
            ephemeral=True,
        )
