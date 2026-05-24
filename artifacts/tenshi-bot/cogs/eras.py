"""
Protocolo 23 — Sistema de Eras do Trono
Protocolo 24 — Localização PT-BR estrita
Controle da Era_Atual global e saudações diárias 07h/19h
"""
import discord
import asyncio
from datetime import datetime, timezone
from database import get_user, save_user, get_all_users
from utils import IMPERADOR_ID
from design import (embed_doc, embed_soberano_decreto, embed_admin_doc,
                    COR_GERAL, COR_DECRETO, COR_JUDICIAL, COR_CRIME,
                    COR_ADMIN, COR_HOSPITAL, rodape_padrao)

# ─── ERAS ─────────────────────────────────────────────────────────────────────
ERAS = {
    "prosperidade": {
        "nome":    "Era da Colheita e Prosperidade",
        "emoji":   "🌾",
        "cor":     0x9E7815,
        "descricao": "Paz, comércio florescente e evolução mística governam o Império.",
        "tom_ia":  (
            "O atual contexto político do Império é de paz e prosperidade. "
            "Use tom culto, pacífico e motivacional. Foque em estoicismo, crescimento pessoal, "
            "comércio, laços sociais e evolução mística. As crônicas devem inspirar e elevar."
        ),
        "temp_manha": (
            "Saudação matinal (07h) em Português Brasileiro formal. Tom pacífico, estoico e elevado. "
            "Mencione o sol nascendo sobre a Cidadela Branca, o Imperador Alloy e a prosperidade do dia."
        ),
        "temp_tarde": (
            "Saudação noturna (19h) em Português Brasileiro formal. Tom contemplativo, focado em "
            "colheita de esforços, descanso merecido e preparação para o amanhã."
        ),
    },
    "alerta_militar": {
        "nome":    "Era do Alerta e Tensão Militar",
        "emoji":   "⚔️",
        "cor":     0xC0392B,
        "descricao": "Ameaças externas ativadas. Postura defensiva em todo o Império.",
        "tom_ia":  (
            "O Império está em ESTADO DE ALERTA MILITAR. Tom severo, militarista, focado em "
            "segurança nacional, vigilância constante e preparação para o combate. "
            "Mesmo na cafeteria ou escola, a IA deve refletir tensão, disciplina e ordem marcial. "
            "As crônicas de nicho geram mais tramas de espionagem, ameaças de fronteira e traições."
        ),
        "temp_manha": (
            "Saudação matinal (07h) em Português Brasileiro formal, tom marcial e severo. "
            "Mencione o estado de alerta, a necessidade de vigilância e a força das forças de segurança do Império."
        ),
        "temp_tarde": (
            "Saudação noturna (19h) em Português Brasileiro, tom militar e sóbrio. "
            "Mencione os relatórios do dia, o perímetro seguro e a rotina das sentinelas."
        ),
    },
    "renascimento_mistico": {
        "nome":    "Era do Renascimento Místico",
        "emoji":   "🔮",
        "cor":     0x4B0082,
        "descricao": "Forças esotéricas convergem. Profecias e alinhamentos astrais dominam.",
        "tom_ia":  (
            "O Império atravessa um RENASCIMENTO MÍSTICO. Use vocabulário densamente esotérico, "
            "focado em profecias, alinhamentos astrais, portais dimensionais, runas ancestrais e destinos. "
            "Todas as crônicas devem ter elementos sobrenaturais. Comandos de Tarot e Runa ganham "
            "descrições mais longas, enigmáticas e perturbadoras."
        ),
        "temp_manha": (
            "Saudação matinal (07h) em Português Brasileiro, tom místico, profético e arcano. "
            "Mencione alinhamentos astrais, o véu entre os planos, visões do Oráculo e o destino do Império."
        ),
        "temp_tarde": (
            "Saudação noturna (19h) em Português Brasileiro, tom esotérico e visionário. "
            "Mencione as estrelas, segredos do cosmos e rituais noturnos do Clube de Ocultismo."
        ),
    },
}

_era_atual: str = "prosperidade"
_ultima_saudacao_manha: str = ""
_ultima_saudacao_tarde: str = ""
_decreto_marcial_ativo: bool = False


def get_era_atual() -> str:
    return _era_atual


def get_tom_ia() -> str:
    return ERAS[_era_atual]["tom_ia"]


def get_era_info() -> dict:
    return ERAS[_era_atual]


def set_decreto_marcial(ativo: bool):
    global _decreto_marcial_ativo
    _decreto_marcial_ativo = ativo


def get_decreto_marcial() -> bool:
    return _decreto_marcial_ativo


# ─── FILTRO PT-BR (Protocolo 24) ─────────────────────────────────────────────
_TERMOS_PROIBIDOS_EN = {
    "cooldown":    "tempo de recuperação",
    "inventory":   "inventário",
    "level":       "nível",
    "level up":    "subir de nível",
    "buff":        "bônus",
    "debuff":      "penalidade",
    "hp":          "pontos de vida",
    "mana":        "mana",
    "xp":          "pontos de experiência",
    "guild":       "servidor",
    "command":     "comando",
    "user":        "usuário",
    "status":      "estado",
    "update":      "atualização",
    "embed":       "mensagem formatada",
    "modal":       "formulário",
}

def filtrar_ptbr(texto: str) -> str:
    """Substitui termos em inglês pelos equivalentes em PT-BR."""
    for en, pt in _TERMOS_PROIBIDOS_EN.items():
        texto = texto.replace(en, pt).replace(en.title(), pt.title())
    return texto


_PROMPT_PTBR = (
    "OBRIGATÓRIO: Responda EXCLUSIVAMENTE em Português Brasileiro (PT-BR), norma-padrão formal. "
    "Use a conjugação correta da terceira pessoa (Você/Ele/Ela) ou tratamento cerimonial "
    "(Soberano, Vossa Excelência) para Alloy e seu cônjuge. "
    "PROIBIDO usar expressões em inglês, gírias ou coloquialismos de outros dialetos."
)


class Eras:
    def __init__(self, bot):
        self.bot = bot
        self._loops_iniciados = False

    def cog_load(self):
        if not self._loops_iniciados:
            self._loops_iniciados = True
            self.bot.loop.create_task(self._loop_saudacoes())

    # ─── COMANDOS ─────────────────────────────────────────────────────────────

    async def handle_set_era(self, message, args):
        global _era_atual
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok:
            await message.channel.send("> ⚠️ **Acesso negado.** Exclusivo do Soberano."); return
        if not args:
            eras_lista = " | ".join(ERAS.keys())
            await message.channel.send(f"> ⚠️ Uso: `Tenshi, set-era [era]`\nEras disponíveis: `{eras_lista}`"); return
        nova = args[0].lower()
        if nova not in ERAS:
            await message.channel.send(f"> ⚠️ Era inválida. Disponíveis: `{' | '.join(ERAS.keys())}`"); return
        _era_atual = nova
        info = ERAS[nova]
        e = embed_soberano_decreto(
            f"Transição de Era Decretada — {info['emoji']} {info['nome']}",
            f"• **Era anterior:** {_era_atual}\n"
            f"• **Nova Era:** {info['nome']}\n"
            f"• **Descrição:** {info['descricao']}\n"
            f"• A IA adaptou seu vocabulário, tom e foco narrativo para a nova era."
        )
        e.color = info["cor"]
        await message.channel.send(embed=e)

    async def handle_era_atual(self, message):
        info = get_era_info()
        e = embed_doc(
            f"{info['emoji']} Era Atual — {info['nome']}",
            f"• **Status:** Ativa\n• **Descrição:** {info['descricao']}\n"
            f"• **Impacto narrativo:** {info['tom_ia'][:200]}...",
            info["cor"]
        )
        await message.channel.send(embed=e)

    async def handle_decreto_marcial(self, message, args):
        global _decreto_marcial_ativo, _era_atual
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok:
            await message.channel.send("> ⚠️ Exclusivo do Soberano."); return
        _decreto_marcial_ativo = not _decreto_marcial_ativo
        if _decreto_marcial_ativo:
            _era_atual = "alerta_militar"
        e = embed_soberano_decreto(
            "Decreto Marcial " + ("ATIVADO" if _decreto_marcial_ativo else "REVOGADO"),
            f"• Sistema de IA reconvertido para postura {'militarista e policialesca' if _decreto_marcial_ativo else 'normal'}.\n"
            f"• Era ajustada para: **{'alerta_militar' if _decreto_marcial_ativo else _era_atual}**"
        )
        await message.channel.send(embed=e)

    # ─── LOOP DE SAUDAÇÕES ────────────────────────────────────────────────────

    async def _loop_saudacoes(self):
        global _ultima_saudacao_manha, _ultima_saudacao_tarde
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = datetime.now(timezone.utc)
            chave = agora.strftime("%Y-%m-%d")

            if agora.hour == 7 and chave != _ultima_saudacao_manha:
                _ultima_saudacao_manha = chave
                await self._enviar_saudacao("manha")

            if agora.hour == 19 and chave != _ultima_saudacao_tarde:
                _ultima_saudacao_tarde = chave
                await self._enviar_saudacao("tarde")

            await asyncio.sleep(1800)

    async def _enviar_saudacao(self, periodo: str):
        try:
            from cogs.loremaster import _gerar, SYS_LORE, DIRETRIZ_ORIGINALIDADE
            info = get_era_info()
            key  = "temp_manha" if periodo == "manha" else "temp_tarde"
            sys_prompt = (
                f"{SYS_LORE}\n\n"
                f"CONTEXTO DA ERA ATUAL: {info['tom_ia']}\n\n"
                f"{_PROMPT_PTBR}\n\n"
                f"{DIRETRIZ_ORIGINALIDADE}"
            )
            narrativa = await _gerar(info[key], sys_prompt, temperatura=0.88)
            narrativa = filtrar_ptbr(narrativa)
            e = embed_doc(
                f"{info['emoji']} {'Saudação Matinal' if periodo == 'manha' else 'Crepúsculo Imperial'} — {info['nome']}",
                narrativa,
                info["cor"]
            )
            for guild in self.bot.guilds:
                canal = self._canal(guild, "geral")
                if canal:
                    try: await canal.send(embed=e)
                    except Exception: pass
        except Exception as ex:
            print(f"[Eras] Erro saudação: {ex}")

    def _canal(self, guild, nome: str):
        if not guild: return None
        for ch in guild.text_channels:
            if nome.lower() in ch.name.lower(): return ch
        return None
