"""Censura multilíngue com detecção local rápida e revisão opcional por IA."""

import asyncio
import json
import os
import re
import unicodedata

import discord

from ia_router import chamar_ia
from utils import RODAPE_IMPERIAL


PALAVRAS_POR_IDIOMA = {
    "pt": ("caralho", "porra", "merda", "puta", "puto", "fdp", "cuzão", "cuzao", "arrombado", "desgraçado", "desgracado", "filho da puta", "vai se foder"),
    "en": ("fuck", "fucking", "motherfucker", "shit", "bullshit", "asshole", "bitch", "bastard", "dickhead", "son of a bitch"),
    "es": ("mierda", "joder", "puta", "puto", "pendejo", "cabron", "cabrón", "gilipollas", "hijo de puta", "chingada"),
    "fr": ("merde", "putain", "connard", "connasse", "salope", "enculé", "encule", "fils de pute"),
    "de": ("scheisse", "scheiße", "arschloch", "hurensohn", "fick dich", "wichser", "fotze"),
    "it": ("cazzo", "merda", "stronzo", "puttana", "vaffanculo", "figlio di puttana"),
    "ru": ("блять", "сука", "хуй", "пиздец", "ебать", "мудак"),
    "ar": ("كس", "شرموط", "قحبة", "ابن الكلب", "يلعن"),
    "zh": ("操你", "傻逼", "妈的", "他妈的", "混蛋"),
    "ja": ("くそ", "クソ", "死ね", "ばかやろう", "馬鹿野郎"),
    "ko": ("씨발", "시발", "병신", "개새끼", "좆"),
    "hi": ("मादरचोद", "बहनचोद", "madarchod", "bhenchod", "chutiya"),
}

LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})
TOKEN_RE = re.compile(r"[\wÀ-ÿ@#$*!]+", re.UNICODE)


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.casefold().translate(LEET))
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    return re.sub(r"[^\w]+", "", texto, flags=re.UNICODE)


TERMOS_NORMALIZADOS = {
    _normalizar(termo): idioma
    for idioma, termos in PALAVRAS_POR_IDIOMA.items()
    for termo in termos
}
TERMOS_SIMPLES = {termo for termo in TERMOS_NORMALIZADOS if " " not in termo}


def detectar_e_camuflar(texto: str, termos_extras: list[str] | None = None) -> tuple[str, list[str], set[str]]:
    """Retorna texto camuflado, termos detectados e idiomas prováveis."""
    extras = {_normalizar(termo) for termo in (termos_extras or []) if termo.strip()}
    conhecidos = set(TERMOS_NORMALIZADOS) | extras
    encontrados: list[str] = []
    idiomas: set[str] = set()

    def substituir(match: re.Match) -> str:
        token = match.group(0)
        normalizado = _normalizar(token)
        if normalizado in conhecidos:
            encontrados.append(token)
            if normalizado in TERMOS_NORMALIZADOS:
                idiomas.add(TERMOS_NORMALIZADOS[normalizado])
            return "▰" * min(max(len(token), 3), 12)
        return token

    camuflado = TOKEN_RE.sub(substituir, texto)

    # Idiomas sem separação por espaços e expressões compostas.
    for idioma, termos in PALAVRAS_POR_IDIOMA.items():
        for termo in termos:
            if " " in termo or idioma in {"zh", "ja", "ko", "ar"}:
                padrao = re.compile(re.escape(termo), re.IGNORECASE)
                if padrao.search(camuflado):
                    encontrados.append(termo)
                    idiomas.add(idioma)
                    camuflado = padrao.sub(lambda m: "▰" * min(max(len(m.group(0)), 3), 12), camuflado)

    # Expressões extras indicadas pela IA.
    for termo in termos_extras or []:
        if not termo.strip():
            continue
        padrao = re.compile(re.escape(termo.strip()), re.IGNORECASE)
        if padrao.search(camuflado):
            encontrados.append(termo.strip())
            camuflado = padrao.sub(lambda m: "▰" * min(max(len(m.group(0)), 3), 12), camuflado)

    return camuflado, list(dict.fromkeys(encontrados)), idiomas


class RevelarConteudoView(discord.ui.View):
    def __init__(self, original: str):
        super().__init__(timeout=600)
        self.original = original

    @discord.ui.button(label="Ver conteúdo original", emoji="👁️", style=discord.ButtonStyle.secondary)
    async def revelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"⚠️ **Conteúdo original:**\n{self.original[:1800]}",
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )


class CensuraMultilingue:
    def __init__(self, bot):
        self.bot = bot
        self.ia_ativa = os.environ.get("TENSHI_CENSOR_AI", "1").strip().casefold() not in {"0", "false", "off", "nao", "não"}
        self._em_analise: set[int] = set()

    async def _publicar_camuflada(self, message: discord.Message, camuflado: str, origem: str) -> bool:
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            return False
        embed = discord.Embed(
            description=camuflado[:3900],
            color=0x3D3D3D,
        )
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.set_footer(text=f"🛡️ Conteúdo sensível camuflado ({origem}) • {RODAPE_IMPERIAL}")
        await message.channel.send(
            embed=embed,
            view=RevelarConteudoView(message.content),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return True

    async def processar_local(self, message: discord.Message) -> bool:
        camuflado, encontrados, idiomas = detectar_e_camuflar(message.content)
        if not encontrados:
            return False
        origem = "idiomas: " + ", ".join(sorted(idiomas)) if idiomas else "filtro multilíngue"
        return await self._publicar_camuflada(message, camuflado, origem)

    def agendar_analise_ia(self, message: discord.Message) -> None:
        if not self.ia_ativa or not message.guild or not 4 <= len(message.content) <= 500:
            return
        if message.id in self._em_analise:
            return
        self._em_analise.add(message.id)
        self.bot.loop.create_task(self._analisar_ia(message))

    async def _analisar_ia(self, message: discord.Message) -> None:
        try:
            sistema = (
                "Você é um classificador multilíngue estrito. Detecte somente palavrões ou xingamentos dirigidos, "
                "em qualquer idioma. Não marque crítica educada, termos técnicos ou narrativa fictícia sem ofensa. "
                "Responda apenas JSON: {\"abusivo\":bool,\"confianca\":0.0,\"idioma\":\"código\",\"termos\":[\"...\"]}."
            )
            resposta = await asyncio.wait_for(
                chamar_ia(sistema, message.content, modelo="rapida", max_tokens=80, temperature=0.0),
                timeout=8,
            )
            inicio, fim = resposta.find("{"), resposta.rfind("}")
            if inicio < 0 or fim <= inicio:
                return
            dados = json.loads(resposta[inicio:fim + 1])
            if not dados.get("abusivo") or float(dados.get("confianca", 0)) < 0.85:
                return
            termos = [str(item) for item in dados.get("termos", []) if str(item).strip()][:8]
            camuflado, encontrados, _ = detectar_e_camuflar(message.content, termos)
            if not encontrados:
                return
            await self._publicar_camuflada(message, camuflado, f"IA • {dados.get('idioma', 'multilíngue')}")
        except (asyncio.TimeoutError, json.JSONDecodeError, discord.HTTPException):
            return
        finally:
            self._em_analise.discard(message.id)
