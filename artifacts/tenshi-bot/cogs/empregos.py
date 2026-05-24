"""
Sistema de Empregos do Império de Tenshi
Integrado ao sistema acadêmico da Tenshi Academy —
empregos de alta patente exigem diploma específico.
"""
import discord
import random
from datetime import datetime, timedelta
from database import get_user, save_user, calcular_nivel
from utils import embed_imperial, SEP, RODAPE_IMPERIAL, CORES_PEGADA
from ia_router import ia_rapida, ia_analitica

COOLDOWN_TRABALHO = 45 * 60  # 45 minutos

# ─── MATÉRIAS E SEUS DADOS DE ESTUDO ─────────────────────────────────────────
# Espelho dos dados de cogs/academia.py para evitar importação circular
MATERIAS_INFO = {
    "tatica_militar":      {"nome": "Tática Militar",          "emoji": "⚔️",  "presenças": 3, "tempo_estudo_h": 12},
    "historia_lore":       {"nome": "História e Lore de Tenshi","emoji": "📜",  "presenças": 3, "tempo_estudo_h": 12},
    "ciencias_esotéricas": {"nome": "Ciências Esotéricas",     "emoji": "🔮",  "presenças": 3, "tempo_estudo_h": 12},
    "direito_imperial":    {"nome": "Direito Imperial",         "emoji": "⚖️",  "presenças": 3, "tempo_estudo_h": 12},
    "logística_engenharia":{"nome": "Logística e Engenharia",   "emoji": "🔧",  "presenças": 3, "tempo_estudo_h": 12},
}


def _tem_diploma(user: dict, materia: str) -> bool:
    """Verifica se o usuário possui diploma na matéria especificada."""
    return any(d.get("materia") == materia for d in user.get("diplomas", []))


def _info_curso(materia: str) -> str:
    """Retorna texto de requisito acadêmico formatado."""
    m = MATERIAS_INFO.get(materia)
    if not m:
        return ""
    return (
        f"📚 **Curso:** {m['emoji']} {m['nome']}\n"
        f"⏱️ **Tempo estimado:** ~{m['tempo_estudo_h']}h (3 presenças + exame)\n"
        f"🎓 Use `Tenshi, matricular {materia}` para iniciar os estudos."
    )


# ─────────────────────────────────────────────────────────────────────────────
# EMPREGOS LEGAIS — com requisitos acadêmicos
# ─────────────────────────────────────────────────────────────────────────────
EMPREGOS_LEGAIS = [
    # ── ÁREA DE SAÚDE ──────────────────────────────────────────────────────
    {
        "id": "medico",
        "nome": "Médico Imperial", "emoji": "⚕️", "area": "Saúde",
        "narrativa": "*Horas no hospital imperial curando feridos de batalha e doenças raras do éter...*",
        "moedas": (80, 160), "xp": (25, 50), "poder": (0, 5),
        "requer_diploma": "ciencias_esotéricas",
        "nivel_minimo": 5,
        "descricao_cargo": "Diagnóstico e tratamento de condições místico-biológicas. Alta remuneração.",
    },
    {
        "id": "enfermeiro",
        "nome": "Enfermeiro de Campo", "emoji": "🩺", "area": "Saúde",
        "narrativa": "*Tratando feridos nas tendas de campanha nas bordas do Império...*",
        "moedas": (35, 80), "xp": (15, 35), "poder": (0, 3),
        "requer_diploma": None,
        "nivel_minimo": 1,
        "descricao_cargo": "Atendimento básico hospitalar. Sem pré-requisitos acadêmicos.",
    },
    {
        "id": "alquimista",
        "nome": "Alquimista da Corte", "emoji": "⚗️", "area": "Saúde/Magia",
        "narrativa": "*Horas destilando ervas raras e combinando elementos arcanos para criar poções...*",
        "moedas": (60, 130), "xp": (30, 60), "poder": (3, 10),
        "requer_diploma": "ciencias_esotéricas",
        "nivel_minimo": 3,
        "descricao_cargo": "Síntese de poções e reagentes arcanos. Exige formação em Ciências Esotéricas.",
    },
    {
        "id": "veterinario",
        "nome": "Veterinário das Bestas", "emoji": "🐉", "area": "Saúde Animal",
        "narrativa": "*Cuidando dos dragões e bestas imperiais usadas nas fronteiras do Império...*",
        "moedas": (50, 100), "xp": (22, 45), "poder": (1, 6),
        "requer_diploma": "ciencias_esotéricas",
        "nivel_minimo": 3,
        "descricao_cargo": "Tratamento de criaturas místicas imperiais. Requer domínio de biologia arcana.",
    },
    {
        "id": "gerente_hospital",
        "nome": "Gestor do Hospital Imperial", "emoji": "🏥", "area": "Gestão",
        "narrativa": "*Administrando o maior hospital de Tenshi — recursos, equipes, emergências e tudo mais...*",
        "moedas": (90, 180), "xp": (20, 45), "poder": (0, 5),
        "requer_diploma": "ciencias_esotéricas",
        "nivel_minimo": 8,
        "descricao_cargo": "Gestão hospitalar de alto escalão. Exige Ciências Esotéricas e nível 8+.",
    },
    # ── ÁREA JURÍDICA ───────────────────────────────────────────────────────
    {
        "id": "advogado",
        "nome": "Advogado Imperial", "emoji": "⚖️", "area": "Direito",
        "narrativa": "*Defendendo casos na Câmara Imperial com argumentos afiados como lâminas...*",
        "moedas": (90, 170), "xp": (12, 28), "poder": (0, 3),
        "requer_diploma": "direito_imperial",
        "nivel_minimo": 4,
        "descricao_cargo": "Defesa e acusação nos tribunais imperiais. Requer formação em Direito Imperial.",
    },
    {
        "id": "juiz",
        "nome": "Magistrado de Tenshi", "emoji": "🔨", "area": "Direito",
        "narrativa": "*Presidindo julgamentos imperiais. Cada decreto marca o destino de um súdito...*",
        "moedas": (100, 190), "xp": (18, 35), "poder": (0, 5),
        "requer_diploma": "direito_imperial",
        "nivel_minimo": 10,
        "descricao_cargo": "Presidência de julgamentos imperiais. Exige Direito Imperial e nível 10+.",
    },
    {
        "id": "diplomata",
        "nome": "Diplomata Imperial", "emoji": "🤝", "area": "Política",
        "narrativa": "*Negociando tratados com clãs rivais nos salões de mármore. Palavras como armas...*",
        "moedas": (80, 160), "xp": (20, 40), "poder": (0, 4),
        "requer_diploma": "historia_lore",
        "nivel_minimo": 5,
        "descricao_cargo": "Negociação de tratados inter-facções. Requer História e Lore de Tenshi.",
    },
    # ── ENGENHARIA ──────────────────────────────────────────────────────────
    {
        "id": "engenheiro",
        "nome": "Engenheiro das Muralhas", "emoji": "🏗️", "area": "Engenharia",
        "narrativa": "*Supervisionando a construção das muralhas do sul. Cada pedra é um ato de defesa...*",
        "moedas": (65, 130), "xp": (20, 40), "poder": (0, 4),
        "requer_diploma": "logística_engenharia",
        "nivel_minimo": 4,
        "descricao_cargo": "Supervisão de obras imperiais. Requer Logística e Engenharia.",
    },
    {
        "id": "arquiteto",
        "nome": "Arquiteto Imperial", "emoji": "📐", "area": "Engenharia",
        "narrativa": "*Projetando novos salões e torres para o Império. Beleza e função em harmonia...*",
        "moedas": (75, 150), "xp": (18, 35), "poder": (0, 3),
        "requer_diploma": "logística_engenharia",
        "nivel_minimo": 5,
        "descricao_cargo": "Projeto arquitetônico de edifícios imperiais. Requer Logística e Engenharia.",
    },
    {
        "id": "marinheiro",
        "nome": "Marinheiro Imperial", "emoji": "⚓", "area": "Marítimo",
        "narrativa": "*Navegando pelos mares de Tenshi, mantendo as rotas comerciais abertas e seguras...*",
        "moedas": (45, 95), "xp": (18, 38), "poder": (1, 5),
        "requer_diploma": "logística_engenharia",
        "nivel_minimo": 2,
        "descricao_cargo": "Operação de frotas e logística fluvial. Requer Logística e Engenharia.",
    },
    # ── SEGURANÇA E ORDEM ───────────────────────────────────────────────────
    {
        "id": "guarda",
        "nome": "Guarda Imperial", "emoji": "🛡️", "area": "Segurança",
        "narrativa": "*Patrulhando as muralhas e canais de Tenshi. Sua presença disuade criminosos...*",
        "moedas": (40, 85), "xp": (22, 45), "poder": (5, 12),
        "requer_diploma": "tatica_militar",
        "nivel_minimo": 2,
        "descricao_cargo": "Guarda das muralhas e patrulha urbana. Requer formação em Tática Militar.",
    },
    # ── EDUCAÇÃO E CULTURA ──────────────────────────────────────────────────
    {
        "id": "professor",
        "nome": "Professor da Academia", "emoji": "📚", "area": "Educação",
        "narrativa": "*Ensinando jovens recrutas as artes de guerra, história imperial e arcanismo básico...*",
        "moedas": (45, 90), "xp": (35, 65), "poder": (0, 4),
        "requer_diploma": "historia_lore",
        "nivel_minimo": 5,
        "descricao_cargo": "Docência na Tenshi Academy. Requer História e Lore de Tenshi.",
    },
    {
        "id": "bibliotecario",
        "nome": "Bibliotecário dos Grimórios", "emoji": "📖", "area": "Conhecimento",
        "narrativa": "*Catalogando e protegendo manuscritos antigos na Biblioteca Imemorial de Tenshi...*",
        "moedas": (40, 80), "xp": (40, 70), "poder": (2, 7),
        "requer_diploma": "historia_lore",
        "nivel_minimo": 3,
        "descricao_cargo": "Custódia e catalogação do acervo histórico. Requer História e Lore.",
    },
    {
        "id": "escriba",
        "nome": "Escriba da Corte", "emoji": "📜", "area": "Burocracia",
        "narrativa": "*Horas copiando decretos e contratos em pergaminho. A lei impressa é poder absoluto...*",
        "moedas": (35, 75), "xp": (30, 55), "poder": (0, 3),
        "requer_diploma": "historia_lore",
        "nivel_minimo": 2,
        "descricao_cargo": "Redação e cópia de decretos imperiais. Requer História e Lore.",
    },
    {
        "id": "bardo",
        "nome": "Bardo Imperial", "emoji": "🎵", "area": "Arte",
        "narrativa": "*Suas histórias e canções ecoam pelos salões. O moral do exército cresce com cada verso...*",
        "moedas": (35, 78), "xp": (28, 50), "poder": (0, 3),
        "requer_diploma": None,
        "nivel_minimo": 1,
        "descricao_cargo": "Arte e entretenimento imperial. Sem pré-requisito acadêmico.",
    },
    # ── PESQUISA ────────────────────────────────────────────────────────────
    {
        "id": "pesquisador",
        "nome": "Pesquisador Arcano", "emoji": "🔬", "area": "Pesquisa",
        "narrativa": "*Estudando artefatos antigos e fenômenos mágicos nos laboratórios da Academia Imperial...*",
        "moedas": (60, 120), "xp": (40, 75), "poder": (4, 14),
        "requer_diploma": "ciencias_esotéricas",
        "nivel_minimo": 6,
        "descricao_cargo": "Pesquisa de artefatos arcanos e fenômenos místicos. Requer Ciências Esotéricas.",
    },
    {
        "id": "sacerdote",
        "nome": "Sacerdote da Ordem", "emoji": "📿", "area": "Religião",
        "narrativa": "*Conduzindo rituais sagrados e lendo os astros em nome do Oráculo de Tenshi...*",
        "moedas": (35, 75), "xp": (35, 60), "poder": (3, 9),
        "requer_diploma": "ciencias_esotéricas",
        "nivel_minimo": 3,
        "descricao_cargo": "Condução de rituais e leitura dos astros. Requer Ciências Esotéricas.",
    },
    # ── EMPREGOS DE ENTRADA (SEM DIPLOMA) ───────────────────────────────────
    {
        "id": "ferreiro",
        "nome": "Ferreiro Imperial", "emoji": "⚒️", "area": "Artesanato",
        "narrativa": "*O calor da forja, o som do martelo no aço. Forjando armas para os guerreiros do Império...*",
        "moedas": (45, 90), "xp": (22, 45), "poder": (4, 12),
        "requer_diploma": None,
        "nivel_minimo": 1,
        "descricao_cargo": "Forja de armas e armaduras. Acesso imediato.",
    },
    {
        "id": "mineiro",
        "nome": "Mineiro das Pedras Negras", "emoji": "⛏️", "area": "Extração",
        "narrativa": "*Nas profundezas das minas de Tenshi, extraindo minério precioso em tuneis escuros...*",
        "moedas": (35, 78), "xp": (15, 35), "poder": (2, 7),
        "requer_diploma": None,
        "nivel_minimo": 1,
        "descricao_cargo": "Extração de minérios nas minas imperiais. Acesso imediato.",
    },
    {
        "id": "artesao",
        "nome": "Artesão das Runas", "emoji": "🎨", "area": "Artesanato",
        "narrativa": "*Esculpindo e pintando artefatos com símbolos rúnicos para os nobres do Império...*",
        "moedas": (40, 85), "xp": (22, 42), "poder": (1, 5),
        "requer_diploma": None,
        "nivel_minimo": 1,
        "descricao_cargo": "Criação de artefatos decorativos e rúnicos. Acesso imediato.",
    },
    {
        "id": "agricultor",
        "nome": "Agricultor Imperial", "emoji": "🌾", "area": "Agricultura",
        "narrativa": "*Os campos de Tenshi foram trabalhados com suas mãos. A colheita sustenta o Império...*",
        "moedas": (25, 60), "xp": (15, 30), "poder": (0, 3),
        "requer_diploma": None,
        "nivel_minimo": 1,
        "descricao_cargo": "Cultivo dos campos imperiais. Acesso imediato.",
    },
    {
        "id": "chef",
        "nome": "Chef do Palácio Imperial", "emoji": "👨‍🍳", "area": "Gastronomia",
        "narrativa": "*Preparando banquetes para a Corte. Cada prato é obra de arte e política...*",
        "moedas": (50, 100), "xp": (20, 38), "poder": (0, 2),
        "requer_diploma": None,
        "nivel_minimo": 1,
        "descricao_cargo": "Culinária de alto padrão para a Corte Imperial. Acesso imediato.",
    },
    {
        "id": "comerciante",
        "nome": "Comerciante Imperial", "emoji": "💼", "area": "Comércio",
        "narrativa": "*Negociando rotas comerciais e contratos vantajosos nos mercados imperiais...*",
        "moedas": (55, 110), "xp": (15, 32), "poder": (0, 3),
        "requer_diploma": None,
        "nivel_minimo": 1,
        "descricao_cargo": "Negociação comercial nos mercados. Acesso imediato.",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# EMPREGOS ILEGAIS
# ─────────────────────────────────────────────────────────────────────────────
EMPREGOS_ILEGAIS = [
    {"id": "contrabandista",  "nome": "Contrabandista",            "emoji": "📦", "area": "Comércio Ilegal",  "narrativa": "*Transportando cargas proibidas pelas rotas secretas abaixo das muralhas de Tenshi...*",      "moedas": (80,  180), "xp": (15, 30), "poder": (2, 7),  "risco": 0.25, "requer_diploma": None, "nivel_minimo": 1},
    {"id": "assassino",       "nome": "Assassino de Aluguel",      "emoji": "🗡️", "area": "Violência",        "narrativa": "*Um contrato foi cumprido nas sombras. Ninguém viu. Ninguém saberá. O pagamento chegou...*",   "moedas": (120, 250), "xp": (20, 40), "poder": (5, 15), "risco": 0.35, "requer_diploma": None, "nivel_minimo": 5},
    {"id": "espiao",          "nome": "Espião de Elite",           "emoji": "🕵️", "area": "Inteligência",     "narrativa": "*Infiltrado na Corte rival, colhendo informações valiosas. Cada detalhe tem preço...*",        "moedas": (90,  200), "xp": (25, 45), "poder": (3, 10), "risco": 0.30, "requer_diploma": "tatica_militar", "nivel_minimo": 4},
    {"id": "falsificador",    "nome": "Falsificador de Decretos",  "emoji": "📋", "area": "Fraude",           "narrativa": "*Imitando selos imperiais com perfeição assustadora. Os documentos passam em qualquer inspeção.*","moedas": (70,  150), "xp": (20, 38), "poder": (1, 5),  "risco": 0.20, "requer_diploma": "historia_lore", "nivel_minimo": 3},
    {"id": "traficante",      "nome": "Traficante de Artefatos",   "emoji": "💎", "area": "Mercado Negro",    "narrativa": "*Vendendo relíquias proibidas para colecionadores que pagam uma fortuna pela raridade...*",     "moedas": (100, 220), "xp": (15, 30), "poder": (2, 8),  "risco": 0.28, "requer_diploma": None, "nivel_minimo": 3},
    {"id": "ladrao",          "nome": "Ladrão de Alta Classe",     "emoji": "🔓", "area": "Crime",            "narrativa": "*Entrando e saindo das mansões nobres de Tenshi sem deixar rastro algum. Arte pura...*",        "moedas": (70,  160), "xp": (18, 35), "poder": (2, 7),  "risco": 0.30, "requer_diploma": None, "nivel_minimo": 2},
    {"id": "chantagista",     "nome": "Chantagista",               "emoji": "📩", "area": "Crime",            "narrativa": "*Com informações comprometedoras em mãos, o pagamento mensal chega pontualmente...*",           "moedas": (90,  190), "xp": (15, 28), "poder": (1, 5),  "risco": 0.22, "requer_diploma": None, "nivel_minimo": 2},
    {"id": "pistoleiro",      "nome": "Pistoleiro da Máfia",       "emoji": "🔫", "area": "Máfia",            "narrativa": "*Executando ordens do Don sem questionar. Eficiência e lealdade são sua moeda...*",             "moedas": (85,  175), "xp": (20, 40), "poder": (4, 12), "risco": 0.32, "requer_diploma": "tatica_militar", "nivel_minimo": 3},
    {"id": "hacker_arcano",   "nome": "Hacker Arcano",             "emoji": "💻", "area": "Tecnologia/Magia", "narrativa": "*Penetrando nos sistemas de runas da Tenshi Enterprise e extraindo dados valiosos...*",          "moedas": (110, 230), "xp": (25, 48), "poder": (3, 10), "risco": 0.25, "requer_diploma": "logística_engenharia", "nivel_minimo": 5},
    {"id": "saqueador",       "nome": "Saqueador de Tumbas",       "emoji": "🏺", "area": "Exploração",       "narrativa": "*Adentrando catacumbas proibidas e extraindo relíquias dos mortos. Lucrativo e perigoso...*",   "moedas": (80,  170), "xp": (22, 42), "poder": (3, 9),  "risco": 0.38, "requer_diploma": None, "nivel_minimo": 2},
    {"id": "mercenario",      "nome": "Mercenário das Sombras",    "emoji": "⚔️", "area": "Conflito",         "narrativa": "*Serviços de combate para quem pagar mais. Sem lealdade, apenas contratos...*",                "moedas": (100, 210), "xp": (25, 50), "poder": (5, 15), "risco": 0.30, "requer_diploma": "tatica_militar", "nivel_minimo": 4},
    {"id": "cambista",        "nome": "Cambista do Submundo",      "emoji": "💱", "area": "Finanças Ilegais", "narrativa": "*Convertendo moedas imperiais em divisas do submundo com spreads abusivos mas anônimos...*",     "moedas": (75,  155), "xp": (12, 25), "poder": (1, 4),  "risco": 0.18, "requer_diploma": None, "nivel_minimo": 1},
    {"id": "sequestrador",    "nome": "Operador de Resgates",      "emoji": "🎭", "area": "Crime Organizado", "narrativa": "*Garantindo que o pagamento pelo 'retorno seguro' de nobres chegue antes deles...*",            "moedas": (150, 300), "xp": (20, 35), "poder": (3, 8),  "risco": 0.45, "requer_diploma": None, "nivel_minimo": 6},
]


# ─────────────────────────────────────────────────────────────────────────────
# VIEWS DE SELEÇÃO
# ─────────────────────────────────────────────────────────────────────────────
class SelectEmpregoView(discord.ui.View):
    def __init__(self, user_id: int, tipo: str, user_data: dict):
        super().__init__(timeout=120)
        self.user_id   = user_id
        self.tipo      = tipo
        self.user_data = user_data
        lista = EMPREGOS_LEGAIS if tipo == "legal" else EMPREGOS_ILEGAIS
        self.add_item(EmpregoSelect(user_id, lista[:25], tipo, user_data))


class EmpregoSelect(discord.ui.Select):
    def __init__(self, user_id: int, empregos: list, tipo: str, user_data: dict):
        self.user_id_ref = user_id
        self.tipo        = tipo
        self.user_data   = user_data
        opcoes = []
        for e in empregos:
            requer = e.get("requer_diploma")
            tem    = _tem_diploma(user_data, requer) if requer else True
            nivel_ok = user_data.get("nivel", 1) >= e.get("nivel_minimo", 1)
            trava = ""
            if requer and not tem:
                m = MATERIAS_INFO.get(requer, {})
                trava = f"🔒 Requer: {m.get('nome','?')}"
            elif not nivel_ok:
                trava = f"🔒 Nível {e['nivel_minimo']}+ necessário"
            opcoes.append(discord.SelectOption(
                label=f"{e['emoji']} {e['nome']}",
                value=e["id"],
                description=trava if trava else f"{e['area']} | {e['moedas'][0]}-{e['moedas'][1]} moedas",
                emoji=e["emoji"],
            ))
        placeholder = "💼 Escolha um emprego legal..." if tipo == "legal" else "🖤 Escolha um serviço ilegal..."
        super().__init__(placeholder=placeholder, options=opcoes)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id_ref:
            await interaction.response.send_message("*Este menu não é seu.*", ephemeral=True)
            return

        emprego_id = self.values[0]
        lista      = EMPREGOS_LEGAIS if self.tipo == "legal" else EMPREGOS_ILEGAIS
        emprego    = next((e for e in lista if e["id"] == emprego_id), None)
        if not emprego:
            return

        user  = get_user(interaction.user.id)
        agora = datetime.utcnow()

        # ── Verificar diploma ────────────────────────────────────────────────
        requer = emprego.get("requer_diploma")
        if requer and not _tem_diploma(user, requer):
            req_info = _info_curso(requer)
            await interaction.response.send_message(embed=discord.Embed(
                title="🎓 Formação Acadêmica Necessária",
                description=(
                    f"**{emprego['emoji']} {emprego['nome']}** exige qualificação profissional específica.\n\n"
                    f"{req_info}"
                ),
                color=0x2C3E50
            ).set_footer(text=RODAPE_IMPERIAL), ephemeral=True)
            return

        # ── Verificar nível mínimo ───────────────────────────────────────────
        nivel_min = emprego.get("nivel_minimo", 1)
        if user.get("nivel", 1) < nivel_min:
            await interaction.response.send_message(embed=discord.Embed(
                title="📊 Nível Insuficiente",
                description=f"**{emprego['nome']}** exige nível **{nivel_min}+**. Seu nível atual: **{user.get('nivel',1)}**.",
                color=0x6B0000
            ).set_footer(text=RODAPE_IMPERIAL), ephemeral=True)
            return

        # ── Cooldown ─────────────────────────────────────────────────────────
        if user.get("ultimo_trabalho"):
            ultimo = datetime.fromisoformat(user["ultimo_trabalho"])
            diferenca = agora - ultimo
            if diferenca < timedelta(seconds=COOLDOWN_TRABALHO):
                restante = timedelta(seconds=COOLDOWN_TRABALHO) - diferenca
                mins = int(restante.total_seconds() // 60)
                segs = int(restante.total_seconds() % 60)
                await interaction.response.send_message(
                    embed=embed_imperial("⏳ Em Recuperação",
                                        f"Próximo trabalho em: **{mins}m {segs}s**", 0x2B0A3D),
                    ephemeral=True)
                return

        moedas = random.randint(*emprego["moedas"])
        xp     = random.randint(*emprego["xp"])
        poder  = random.randint(*emprego["poder"])

        # ── Risco emprego ilegal ─────────────────────────────────────────────
        if self.tipo == "ilegal":
            risco = emprego.get("risco", 0.25)
            if random.random() < risco:
                multa = int(moedas * 0.5)
                user["moedas"] = max(0, user.get("moedas", 0) - multa)
                user["ultimo_trabalho"] = agora.isoformat()
                save_user(interaction.user.id, user)
                await interaction.response.send_message(embed=discord.Embed(
                    title="🚨 INTERCEPTADO!",
                    description=(
                        f"*{emprego['narrativa']}*\n\n{SEP}\n\n"
                        f"**Você foi capturado!** Multa de **{multa}** moedas imperiais aplicada.\n\n{SEP}"
                    ),
                    color=0x8B0000
                ).set_footer(text=RODAPE_IMPERIAL))
                return

        user["moedas"] = user.get("moedas", 0) + moedas
        user["xp"]     = user.get("xp", 0) + xp
        user["poder"]  = user.get("poder", 100) + poder
        user["ultimo_trabalho"] = agora.isoformat()
        nivel, _ = calcular_nivel(user["xp"])
        user["nivel"] = nivel
        save_user(interaction.user.id, user)

        cor = 0x006400 if self.tipo == "legal" else 0x1C1C1C
        embed = discord.Embed(
            title=f"{emprego['emoji']} {emprego['nome'].upper()}",
            description=f"{emprego['narrativa']}\n\n{SEP}",
            color=cor
        )
        embed.add_field(name="💰 Ganho",  value=f"**+{moedas}** moedas", inline=True)
        embed.add_field(name="✨ XP",     value=f"**+{xp}**",            inline=True)
        if poder > 0:
            embed.add_field(name="💥 Poder", value=f"**+{poder}**",      inline=True)
        embed.add_field(name="🏢 Área",   value=emprego["area"],          inline=True)
        if requer:
            m = MATERIAS_INFO.get(requer, {})
            embed.add_field(name="🎓 Cargo", value=m.get("nome","?"),     inline=True)
        if self.tipo == "ilegal":
            embed.add_field(name="⚠️ Aviso",
                            value="*Trabalho ilegal — sujeito a interceptação*", inline=False)
        embed.set_footer(text=f"⏳ Próximo trabalho em 45 minutos  •  {RODAPE_IMPERIAL}")
        await interaction.response.send_message(embed=embed)


# ─────────────────────────────────────────────────────────────────────────────
# COG PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
class Empregos:
    def __init__(self, bot):
        self.bot = bot

    async def handle_trabalhos(self, message):
        user = get_user(message.author.id)

        # Contar quantos empregos estão disponíveis para o usuário
        disponiveis_legais  = sum(1 for e in EMPREGOS_LEGAIS
                                  if (not e["requer_diploma"] or _tem_diploma(user, e["requer_diploma"]))
                                  and user.get("nivel",1) >= e.get("nivel_minimo",1))
        disponiveis_ilegais = sum(1 for e in EMPREGOS_ILEGAIS
                                  if (not e["requer_diploma"] or _tem_diploma(user, e["requer_diploma"]))
                                  and user.get("nivel",1) >= e.get("nivel_minimo",1))

        embed = discord.Embed(
            title="💼 SISTEMA DE EMPREGOS IMPERIAL",
            description=(
                f"*Escolha como ganhar sua vida no Império de Tenshi...*\n{SEP}\n\n"
                f"**{len(EMPREGOS_LEGAIS)}** empregos legais cadastrados "
                f"| **{disponiveis_legais}** disponíveis para você\n"
                f"**{len(EMPREGOS_ILEGAIS)}** serviços ilegais cadastrados "
                f"| **{disponiveis_ilegais}** disponíveis para você\n\n"
                f"🎓 **Empregos de patente exigem diploma da Tenshi Academy.**\n"
                f"Use `Tenshi, carreiras` para ver os requisitos de cada cargo.\n\n"
                f"*Tempo de recuperação: 45 minutos entre turnos*\n\n{SEP}"
            ),
            color=CORES_PEGADA.get(user.get("pegada","imperial"), 0x2B0A3D)
        )
        embed.add_field(
            name="💼 Empregos Legais",
            value="`Tenshi, emprego legal` — Trabalho honrado e seguro",
            inline=False
        )
        embed.add_field(
            name="🖤 Serviços Ilegais",
            value="`Tenshi, emprego ilegal` — Trabalho nas sombras (nível 3+ / Máfia)",
            inline=False
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_carreiras(self, message):
        """Lista todos os cargos com seus requisitos acadêmicos."""
        user = get_user(message.author.id)
        embed = discord.Embed(
            title="🎓 GUIA DE CARREIRAS — REQUISITOS ACADÊMICOS",
            description=(
                f"*Empregos de alta patente exigem formação na Tenshi Academy.*\n"
                f"🔒 = Diploma necessário  •  ✅ = Disponível para você\n{SEP}"
            ),
            color=0x2C3E50
        )
        # Agrupar por área
        por_materia: dict[str, list] = {}
        sem_req = []
        for e in EMPREGOS_LEGAIS:
            req = e.get("requer_diploma")
            if req:
                por_materia.setdefault(req, []).append(e)
            else:
                sem_req.append(e)

        for mat_key, lista in por_materia.items():
            m = MATERIAS_INFO.get(mat_key, {})
            tem_dipl = _tem_diploma(user, mat_key)
            nomes = []
            for e in lista:
                nivel_ok = user.get("nivel",1) >= e.get("nivel_minimo",1)
                ok = tem_dipl and nivel_ok
                icon = "✅" if ok else "🔒"
                nomes.append(f"{icon} {e['emoji']} {e['nome']} (Nv.{e['nivel_minimo']}+)")
            dipl_str = "✅ Você possui este diploma" if tem_dipl else f"🔒 `Tenshi, matricular {mat_key}`"
            embed.add_field(
                name=f"{m.get('emoji','📚')} {m.get('nome', mat_key)} — ~{m.get('tempo_estudo_h',12)}h de estudo",
                value=dipl_str + "\n" + "\n".join(nomes),
                inline=False
            )
        if sem_req:
            nomes_livres = " • ".join(f"{e['emoji']} {e['nome']}" for e in sem_req)
            embed.add_field(
                name="✅ Acesso Imediato (sem diploma necessário)",
                value=nomes_livres,
                inline=False
            )
        embed.set_footer(text=f"Tenshi Academy • Use 'Tenshi, matricular [materia]' para iniciar  •  {RODAPE_IMPERIAL}")
        await message.channel.send(embed=embed)

    async def handle_emprego(self, message, args):
        user  = get_user(message.author.id)
        agora = datetime.utcnow()

        if user.get("ultimo_trabalho"):
            ultimo = datetime.fromisoformat(user["ultimo_trabalho"])
            if agora - ultimo < timedelta(seconds=COOLDOWN_TRABALHO):
                restante = timedelta(seconds=COOLDOWN_TRABALHO) - (agora - ultimo)
                mins = int(restante.total_seconds() // 60)
                segs = int(restante.total_seconds() % 60)
                await message.channel.send(embed=embed_imperial(
                    "⏳ Em Descanso",
                    f"*Você ainda precisa descansar após o último turno...*\n\nPróximo trabalho em: **{mins}m {segs}s**",
                    0x2B0A3D
                ))
                return

        tipo = "legal"
        if args and args[0].lower() in ("ilegal", "ilegais", "crime", "mafia", "negro"):
            tipo = "ilegal"

        pegada   = user.get("pegada", "imperial")
        cor = 0x2B0A3D if tipo == "legal" else 0x1C1C1C

        if tipo == "ilegal":
            tem_acesso = pegada in ("mafia",) or user.get("nivel", 1) >= 3
            if not tem_acesso:
                await message.channel.send(embed=embed_imperial(
                    "🚫 Acesso Restrito",
                    "*Os contatos do submundo não confiam em você ainda...*\n\nNível 3+ ou pegada Máfia necessária.",
                    0x6B0000
                ))
                return

        embed = discord.Embed(
            title=f"{'💼 EMPREGOS LEGAIS' if tipo == 'legal' else '🖤 SERVIÇOS DO SUBMUNDO'}",
            description=(
                f"*{'Oportunidades de trabalho honrado no Império...' if tipo == 'legal' else 'O submundo oferece serviços para os corajosos...'}*\n"
                f"{SEP}\n\nEscolha um emprego no menu abaixo:"
            ),
            color=cor
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = SelectEmpregoView(message.author.id, tipo, user)
        await message.channel.send(embed=embed, view=view)
