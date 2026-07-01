import time

import discord
from ia_router import ia_soberana
from database_infractions import register_infraction
from lei_imperial import prompt_lei_imperial
from utils import RODAPE_IMPERIAL, SEP
from violation_checker import check_violation, should_auto_warn

COR_DOURADO = 0x9E7815
COR_NEUTRO = 0x3D3D3D
COR_AVISO = 0xFF6600


class AssistenteIA:
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns: dict[int, float] = {}

    async def _verificar_violacao(self, message: discord.Message, conteudo: str) -> bool:
        """
        Verifica se a mensagem viola as regras.
        Se violar, registra aviso automático e notifica o usuário.
        
        Retorna True se há violação, False caso contrário.
        """
        eh_violacao, tipo_violacao, motivo = check_violation(conteudo)
        
        if not eh_violacao:
            return False
        
        # Se deve registrar aviso automático
        if should_auto_warn(tipo_violacao):
            try:
                await register_infraction(
                    user_id=message.author.id,
                    infraction_type="aviso",
                    reason=f"[IA] Violação automática: {motivo}",
                    moderator_id=self.bot.user.id if self.bot.user else None,
                )
            except Exception as e:
                print(f"Erro ao registrar aviso automático: {e}")
        
        # Notificar usuário sobre a violação
        embed = discord.Embed(
            title="⚠️ Conteúdo Violando Regras",
            description=(
                f"Sua mensagem foi marcada como **{tipo_violacao}**.\n\n"
                f"**Motivo:** {motivo}\n\n"
                f"*Por favor, mantenha as regras imperiais. Violações reincidentes resultarão em punições.*\n\n"
                f"{SEP}"
            ),
            color=COR_AVISO,
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        
        try:
            await message.author.send(embed=embed)
        except discord.Forbidden:
            # Se não conseguir enviar DM, tenta responder no canal
            try:
                await message.channel.send(f"{message.author.mention}", embed=embed, delete_after=10)
            except Exception:
                pass
        
        return True

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

        # Verificar violações ANTES de responder
        if await self._verificar_violacao(message, conteudo):
            return True

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
