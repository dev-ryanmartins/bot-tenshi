"""Automação segura de canais temáticos para os sistemas do Tenshi Bot."""

import re

import discord

from utils import IMPERADOR_ID, RODAPE_IMPERIAL


CANAIS_SISTEMA = (
    ("📜", "comandos-tenshi", "Central de comandos", "Use `tenshi ajuda` ou `/ajuda` para navegar por todos os sistemas."),
    ("🎭", "fichas-rpg", "Fichas e personagens", "Comandos principais: `tenshi status`, `tenshi criar-ficha`, `tenshi set-status`."),
    ("💰", "mercado-imperial", "Economia e mercado", "Use `tenshi mercado`, `tenshi carteira`, `tenshi banco` e `tenshi casas`."),
    ("🎓", "tenshi-academy", "Academia Imperial", "Use `tenshi grade-academia`, `tenshi matricular` e `tenshi professores`."),
    ("👨‍👩‍👧", "familia-imperial", "Família e parentescos", "Use `tenshi arvore-familiar`, `tenshi meu-parentesco` e `tenshi parentesco`."),
    ("⚔️", "aventuras-rpg", "Missões e combates", "Use `tenshi missao`, `tenshi duelo`, `tenshi treinar` e `tenshi cronica`."),
    ("🎉", "eventos-tenshi", "Eventos do servidor", "Canal para cerimônias, festas, invasões e eventos narrativos."),
    ("🛠️", "suporte-tenshi", "Suporte do bot", "Informe aqui comandos com erro e dúvidas sobre os sistemas de Tenshi."),
)


def _admin(member) -> bool:
    if member.id == IMPERADOR_ID:
        return True
    perms = getattr(member, "guild_permissions", None)
    return bool(perms and perms.administrator)


def _slug(texto: str) -> str:
    texto = texto.casefold().replace("_", "-").replace(" ", "-")
    return re.sub(r"[^a-z0-9áàâãéêíóôõúç-]", "", texto).strip("-")


def _prefixo_visual(guild: discord.Guild) -> str:
    for canal in guild.text_channels:
        partes = canal.name.split("・")
        if len(partes) >= 3 and partes[0].strip():
            return partes[0].strip()
    return "tenshi"


def _nome_canal(prefixo: str, emoji: str, nome: str) -> str:
    return f"{prefixo}・{emoji}・{_slug(nome)}"[:100]


class AutomacaoServidor:
    def __init__(self, bot):
        self.bot = bot

    async def handle_organizar_canais(self, message, args):
        if not _admin(message.author):
            await message.channel.send(embed=self._embed("🚫 Acesso restrito", "Somente administradores podem organizar os canais.", 0x8B1E1E))
            return
        if not message.guild.me or not message.guild.me.guild_permissions.manage_channels:
            await message.channel.send(embed=self._embed("⚠️ Permissão necessária", "Conceda ao bot **Gerenciar Canais**.", 0xB45309))
            return

        guild = message.guild
        categoria = discord.utils.find(lambda item: "sistemas tenshi" in item.name.casefold(), guild.categories)
        if categoria is None:
            categoria = await guild.create_category("🏛️・Sistemas Tenshi", reason="Organização automática dos sistemas do Tenshi Bot")

        prefixo = _prefixo_visual(guild)
        criados, existentes = [], []
        for emoji, slug, titulo, descricao in CANAIS_SISTEMA:
            nome = _nome_canal(prefixo, emoji, slug)
            canal = discord.utils.get(guild.text_channels, name=nome) or discord.utils.find(
                lambda item: item.name == slug or item.name.endswith(f"・{slug}"),
                guild.text_channels,
            )
            if canal:
                existentes.append(canal.mention)
                continue
            canal = await guild.create_text_channel(
                nome,
                category=categoria,
                topic=f"{titulo} • {descricao}"[:1024],
                reason="Estrutura temática solicitada pela administração",
            )
            criados.append(canal.mention)
            await canal.send(embed=self._embed(f"{emoji} {titulo}", descricao, 0x6D28D9))

        await message.channel.send(embed=self._embed(
            "🏛️ Estrutura Tenshi organizada",
            f"**Categoria:** {categoria.name}\n"
            f"**Novos canais:** {', '.join(criados) if criados else 'Nenhum — tudo já estava pronto.'}\n"
            f"**Já existentes:** {', '.join(existentes) if existentes else 'Nenhum'}\n\n"
            "A execução é idempotente: repetir o comando não duplica canais.",
            0x1A5C2E,
        ))

    @staticmethod
    def _embed(titulo: str, descricao: str, cor: int) -> discord.Embed:
        embed = discord.Embed(title=titulo, description=descricao, color=cor)
        embed.set_footer(text=RODAPE_IMPERIAL)
        return embed
