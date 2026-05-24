"""
Módulo Jurídico — Módulo 12
Sistema de Warns Automáticos, Código de Conduta e Gestão Penal
"""
import discord
import asyncio
import re
from datetime import datetime, timedelta
from database import get_user, save_user, registrar_infracao, get_infrações, remover_infracao
from utils import SEP, RODAPE_IMPERIAL, IMPERADOR_ID
from ia_router import ia_analitica, ia_rapida

COR_IMPERIAL = 0x2C3E50
COR_PRETO    = 0x111111
COR_PERIGO   = 0x7B1F1F
COR_NEUTRO   = 0x3D3D3D
COR_SUCESSO  = 0x1A5C2E

def embed_soberano(titulo: str, descricao: str, cor: int = COR_IMPERIAL) -> discord.Embed:
    e = discord.Embed(title=titulo, description=descricao, color=cor)
    e.set_footer(text=RODAPE_IMPERIAL)
    return e

# ─── CÓDIGO DE CONDUTA (para o prompt de triagem) ─────────────────────────────
CODIGO_CONDUTA = {
    "art4_i":   {"texto": "Uso de linguagem ofensiva, preconceituosa ou discriminatória",      "nivel": "grave"},
    "art4_ii":  {"texto": "Divulgação de conteúdo impróprio (pornografia, violência extrema)",  "nivel": "grave"},
    "art4_iii": {"texto": "Bullying, assédio moral, ameaças ou humilhação",                    "nivel": "grave"},
    "art4_iv":  {"texto": "Metagaming deliberado e prejudicial",                               "nivel": "moderado"},
    "art4_v":   {"texto": "Divulgação de informações privadas sem consentimento",              "nivel": "moderado"},
    "art4_vi":  {"texto": "Spam ou autopromoção sem permissão",                                "nivel": "leve"},
    "art4_vii": {"texto": "Criação de fakes ou contas para burlar regras",                    "nivel": "grave"},
    "art6":     {"texto": "Crime previsto no Código Penal (racismo, ameaças, apologia)",      "nivel": "critico"},
}

# Palavras que ativam triagem automática
GATILHOS_CRITICOS = [
    r"\bracismo\b", r"\bnazi\b", r"\bfascismo\b", r"\baptem\b",
    r"vou te matar", r"vou te bater", r"sua morte", r"te destruir",
    r"\bputa\b", r"\bviado\b", r"\bcracker\b",
]

GATILHOS_MODERADOS = [
    r"\bspam\b", r"\baupromo\b", r"link suspeito",
]

def _analisar_mensagem(texto: str) -> tuple[str | None, str | None]:
    t = texto.lower()
    for pattern in GATILHOS_CRITICOS:
        if re.search(pattern, t):
            return "art6", "critico"
    for pattern in GATILHOS_MODERADOS:
        if re.search(pattern, t):
            return "art4_vi", "leve"
    return None, None


class Juridico:
    def __init__(self, bot):
        self.bot = bot

    def _is_autorizado(self, user: discord.Member, user_data: dict) -> bool:
        try:
            adm = user.guild_permissions.administrator
        except Exception:
            adm = False
        return adm or user.id == IMPERADOR_ID or user_data.get("co_soberano")

    # ── TRIAGEM AUTOMÁTICA (chamado pelo on_message) ───────────────────────────
    async def triar_mensagem(self, message: discord.Message) -> bool:
        """Retorna True se a mensagem foi bloqueada/removida."""
        artigo, nivel = _analisar_mensagem(message.content)
        if not artigo:
            return False

        canal_punicoes = None
        if message.guild:
            for ch in message.guild.text_channels:
                if "punições" in ch.name.lower() or "punicoes" in ch.name.lower():
                    canal_punicoes = ch
                    break

        if nivel == "critico":
            try:
                await message.delete()
            except Exception:
                pass
            registrar_infracao(message.author.id, artigo, message.content[:200], "Sistema_IA")
            infrações = get_infrações(message.author.id)
            if canal_punicoes:
                await canal_punicoes.send(embed=discord.Embed(
                    title="COMUNICADO DE EXÍLIO SUMÁRIO | Art. 6º",
                    description=(
                        f"O usuário {message.author.mention} (ID: {message.author.id}) "
                        f"foi banido permanentemente por conduta incompatível com a legislação vigente e os "
                        f"princípios deste Império. O caso foi arquivado para auditoria da administração.\n\n"
                        f"**Enquadramento:** {CODIGO_CONDUTA[artigo]['texto']}"
                    ),
                    color=COR_PRETO
                ).set_footer(text=RODAPE_IMPERIAL))
            try:
                await message.author.ban(reason=f"Art. 6º — {CODIGO_CONDUTA[artigo]['texto']}")
            except Exception:
                pass
            return True

        # Níveis moderado / leve
        registrar_infracao(message.author.id, artigo, message.content[:200], "Sistema_IA")
        infrações = get_infrações(message.author.id)
        total = len(infrações)
        descricao = CODIGO_CONDUTA[artigo]["texto"]

        if total == 1:
            await message.channel.send(embed=embed_soberano(
                "Advertência Formal Registrada",
                f"**Usuário:** {message.author.mention}\n"
                f"**Infração detectada:** {descricao}\n"
                f"**Enquadramento:** Art. 4º, Inciso correspondente\n"
                f"**Registro:** Efetuado no banco de dados.",
                COR_PERIGO
            ))
        elif total == 2:
            try:
                await message.author.timeout(discord.utils.utcnow() + timedelta(hours=24))
            except Exception:
                pass
            if canal_punicoes:
                await canal_punicoes.send(embed=embed_soberano(
                    "Decreto de Suspensão — 2ª Reincidência",
                    f"**Usuário:** {message.author.mention}\n"
                    f"**Infração:** {descricao}\n"
                    f"**Punição:** Suspensão automática de 24 horas.\n"
                    f"**Reincidência:** 2ª ocorrência registrada.",
                    COR_PERIGO
                ))
        elif total >= 3:
            try:
                for ch in message.guild.channels:
                    await ch.set_permissions(message.author, view_channel=False)
            except Exception:
                pass
            imperador = message.guild.get_member(IMPERADOR_ID)
            if imperador:
                await imperador.send(embed=embed_soberano(
                    "⚠ ALERTA — 3ª Reincidência",
                    f"{message.author.mention} (ID: {message.author.id}) acumulou 3+ infrações.\n\n"
                    f"**Última infração:** {descricao}\n\n"
                    f"Use `Tenshi, ban @{message.author.display_name}` ou `Tenshi, exilar` para aplicar o Exílio Definitivo.",
                    COR_PERIGO
                ))
            if canal_punicoes:
                await canal_punicoes.send(embed=embed_soberano(
                    "Encaminhamento ao Julgamento Imperial",
                    f"{message.author.mention} foi removido de todos os canais e aguarda julgamento.\n"
                    f"Notificação enviada ao Imperador.",
                    COR_PRETO
                ))
        return False

    # ── FICHA CRIMINAL ────────────────────────────────────────────────────────
    async def handle_ficha_criminal(self, message, args):
        user_data = get_user(message.author.id)
        if not self._is_autorizado(message.author, user_data):
            await message.channel.send(embed=embed_soberano("Acesso Restrito", "Comando reservado à staff e autoridades.", COR_PERIGO))
            return
        alvo = message.mentions[0] if message.mentions else message.author
        infrações = get_infrações(alvo.id)
        embed = discord.Embed(
            title=f"Ficha Criminal — {alvo.display_name}",
            color=COR_PRETO if infrações else COR_NEUTRO
        )
        embed.add_field(name="ID",              value=str(alvo.id),         inline=True)
        embed.add_field(name="Total Infrações", value=str(len(infrações)),  inline=True)
        if infrações:
            for i, inf in enumerate(infrações[-10:], 1):
                artigo = inf.get("artigo", "—")
                data   = inf.get("data_hora", "—")[:10]
                tipo   = inf.get("tipo", "—")
                embed.add_field(
                    name=f"Ocorrência #{i}",
                    value=f"Artigo: {artigo}  |  Tipo: {tipo}  |  Data: {data}",
                    inline=False
                )
        else:
            embed.description = "*Sem registros de infrações para este membro.*"
        embed.set_footer(text=f"Consultado por {message.author.display_name}  •  Confidencial")
        await message.channel.send(embed=embed)

    # ── PERDOAR AVISO ─────────────────────────────────────────────────────────
    async def handle_perdoar_aviso(self, message, args):
        user_data = get_user(message.author.id)
        if not self._is_autorizado(message.author, user_data):
            await message.channel.send(embed=embed_soberano("Acesso Restrito", "Apenas autoridades podem perdoar infrações.", COR_PERIGO))
            return
        if not message.mentions or len(args) < 2:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Uso: `Tenshi, perdoar-aviso @usuario [ID_Infracao]`", COR_NEUTRO))
            return
        alvo = message.mentions[0]
        inf_id = args[-1]
        ok = remover_infracao(alvo.id, inf_id)
        if ok:
            await message.channel.send(embed=embed_soberano(
                "Aviso Removido",
                f"Infração `{inf_id}` removida do histórico de {alvo.mention} por ordem de {message.author.mention}.",
                COR_SUCESSO
            ))
        else:
            await message.channel.send(embed=embed_soberano("Não Encontrado", f"Infração `{inf_id}` não localizada.", COR_NEUTRO))

    # ── WARN MANUAL ──────────────────────────────────────────────────────────
    async def handle_warn(self, message, args):
        user_data = get_user(message.author.id)
        if not self._is_autorizado(message.author, user_data):
            await message.channel.send(embed=embed_soberano("Acesso Restrito", "Apenas moderadores podem emitir advertências.", COR_PERIGO))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Uso: `Tenshi, warn @usuario [motivo]`", COR_NEUTRO))
            return
        alvo   = message.mentions[0]
        motivo = " ".join(args[1:]) if len(args) > 1 else "Infração não especificada"
        registrar_infracao(alvo.id, "warn_manual", motivo, str(message.author.id))
        infrações = get_infrações(alvo.id)
        await message.channel.send(embed=embed_soberano(
            "Advertência Formal Emitida",
            f"**Usuário:** {alvo.mention}\n"
            f"**Motivo:** {motivo}\n"
            f"**Moderador:** {message.author.mention}\n"
            f"**Total de advertências:** {len(infrações)}",
            COR_PERIGO
        ))
