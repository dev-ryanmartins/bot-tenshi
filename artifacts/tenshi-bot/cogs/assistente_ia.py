import time

import discord

from ia_router import ia_soberana
from lei_imperial import prompt_lei_imperial
from utils import RODAPE_IMPERIAL, SEP


COR_DOURADO = 0x9E7815
COR_NEUTRO = 0x3D3D3D


class AssistenteIA:
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns: dict[int, float] = {}

    def _deve_responder(self, message, conteudo_lower: str, prefixo: str) -> bool:
        if conteudo_lower.startswith(prefixo):
            return False
        if isinstance(message.channel, discord.DMChannel):
            return True
        if self.bot.user and self.bot.user in message.mentions:
            return True
        return conteudo_lower.startswith(("tenshi ", "tenshi,", "tenshi?", "ei tenshi", "oi tenshi"))

    async def _responder(self, message, texto: str):
        if self.bot.user:
            texto = texto.replace(self.bot.user.mention, "").strip()
        if not texto:
            texto = "Cumprimente e pergunte como pode ajudar."

        contexto = (
            f"Usuario: {message.author.display_name} ({message.author.id})\n"
            f"Canal: {getattr(message.channel, 'name', 'DM')}\n"
            f"Mensagem: {texto}\n\n"
            "Responda como Tenshi, assistente administrativo e narrativo do Imperio. "
            "Ajude com comandos, RPG, cargos, casamento, leis, eventos e duvidas gerais. "
            "Se pedirem uma acao administrativa real, explique o comando necessario e exija autoridade."
        )
        resposta = await ia_soberana(
            prompt_lei_imperial()
            + "\n\nSeja claro, util e elegante. Maximo 900 caracteres. Nao marque @everyone.",
            contexto,
            max_tokens=450,
        )
        embed = discord.Embed(
            title="Tenshi responde",
            description=f"{resposta[:1800]}\n\n{SEP}",
            color=COR_DOURADO if len(texto) > 20 else COR_NEUTRO,
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def talvez_responder(self, message, conteudo: str, prefixo: str) -> bool:
        conteudo_lower = conteudo.lower().strip()
        if not self._deve_responder(message, conteudo_lower, prefixo):
            return False

        agora = time.monotonic()
        ultimo = self.cooldowns.get(message.author.id, 0)
        if agora - ultimo < 8:
            return True
        self.cooldowns[message.author.id] = agora

        await self._responder(message, conteudo)
        return True

    async def handle_chat(self, message, args):
        texto = " ".join(args).strip()
        if not texto:
            embed = discord.Embed(
                title="Tenshi IA",
                description="Use: `Tenshi, chat [pergunta ou pedido]`",
                color=COR_NEUTRO,
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return
        await self._responder(message, texto)
