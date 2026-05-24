import discord
import random
from datetime import datetime, timedelta
from database import get_user, save_user, calcular_nivel
from utils import embed_imperial, SEP, RODAPE_IMPERIAL, CORES_PEGADA

COOLDOWN_TRABALHO = 45 * 60  # 45 minutos

# ─────────────────────────────────────────────────────────────────────────────
# TODOS OS EMPREGOS LEGAIS
# ─────────────────────────────────────────────────────────────────────────────
EMPREGOS_LEGAIS = [
    # Área de Saúde
    {"id": "medico",          "nome": "Médico Imperial",          "emoji": "⚕️", "area": "Saúde",          "narrativa": "*Horas no hospital imperial curando feridos de batalha e doenças raras do éter...*",          "moedas": (60, 120), "xp": (20, 40), "poder": (0, 5)},
    {"id": "enfermeiro",      "nome": "Enfermeiro de Campo",      "emoji": "🩺", "area": "Saúde",          "narrativa": "*Tratando feridos nas tendas de campanha nas bordas do Império...*",                         "moedas": (30, 70),  "xp": (15, 30), "poder": (0, 3)},
    {"id": "alquimista",      "nome": "Alquimista",               "emoji": "⚗️", "area": "Saúde/Magia",    "narrativa": "*Horas destilando ervas raras e combinando elementos arcanos para criar poções...*",          "moedas": (50, 100), "xp": (25, 50), "poder": (2, 8)},
    # Área Jurídica
    {"id": "advogado",        "nome": "Advogado Imperial",        "emoji": "⚖️", "area": "Direito",        "narrativa": "*Defendendo casos na Câmara Imperial com argumentos afiados como lâminas...*",               "moedas": (80, 150), "xp": (10, 25), "poder": (0, 3)},
    {"id": "juiz",            "nome": "Magistrado de Tenshi",     "emoji": "🔨", "area": "Direito",        "narrativa": "*Presidindo julgamentos imperiais. Cada decreto marca o destino de um súdito...*",            "moedas": (90, 160), "xp": (15, 30), "poder": (0, 5)},
    {"id": "diplomata",       "nome": "Diplomata Imperial",       "emoji": "🤝", "area": "Política",       "narrativa": "*Negociando tratados com clãs rivais nos salões de mármore. Palavras como armas...*",         "moedas": (70, 140), "xp": (20, 35), "poder": (0, 4)},
    # Construção e Engenharia
    {"id": "engenheiro",      "nome": "Engenheiro das Muralhas",  "emoji": "🏗️", "area": "Engenharia",     "narrativa": "*Supervisionando a construção das muralhas do sul. Cada pedra é um ato de defesa...*",         "moedas": (55, 110), "xp": (18, 35), "poder": (0, 4)},
    {"id": "arquiteto",       "nome": "Arquiteto Imperial",       "emoji": "📐", "area": "Engenharia",     "narrativa": "*Projetando novos salões e torres para o Império. Beleza e função em harmonia...*",            "moedas": (65, 130), "xp": (15, 30), "poder": (0, 3)},
    {"id": "ferreiro",        "nome": "Ferreiro Imperial",        "emoji": "⚒️", "area": "Artesanato",     "narrativa": "*O calor da forja, o som do martelo no aço. Forjando armas para os guerreiros do Império...*","moedas": (45, 90),  "xp": (20, 40), "poder": (3, 10)},
    {"id": "mineiro",         "nome": "Mineiro das Pedras Negras","emoji": "⛏️", "area": "Extração",       "narrativa": "*Nas profundezas das minas de Tenshi, extraindo minério precioso em tuneis escuros...*",      "moedas": (40, 80),  "xp": (15, 35), "poder": (1, 6)},
    {"id": "artesao",         "nome": "Artesão das Runas",        "emoji": "🎨", "area": "Artesanato",     "narrativa": "*Esculpindo e pintando artefatos com símbolos rúnicos para os nobres do Império...*",         "moedas": (40, 85),  "xp": (20, 38), "poder": (1, 5)},
    # Educação e Cultura
    {"id": "professor",       "nome": "Professor da Academia",    "emoji": "📚", "area": "Educação",       "narrativa": "*Ensinando jovens recrutas as artes de guerra, história imperial e arcanismo básico...*",      "moedas": (40, 80),  "xp": (30, 55), "poder": (0, 4)},
    {"id": "bardo",           "nome": "Bardo Imperial",           "emoji": "🎵", "area": "Arte",           "narrativa": "*Suas histórias e canções ecoam pelos salões. O moral do exército cresce com cada verso...*",  "moedas": (35, 75),  "xp": (25, 45), "poder": (0, 3)},
    {"id": "bibliotecario",   "nome": "Bibliotecário dos Grimórios","emoji":"📖", "area": "Conhecimento",  "narrativa": "*Catalogando e protegendo manuscritos antigos na Biblioteca Imemorial de Tenshi...*",          "moedas": (35, 70),  "xp": (35, 60), "poder": (2, 7)},
    {"id": "escriba",         "nome": "Escriba da Corte",         "emoji": "📜", "area": "Burocracia",     "narrativa": "*Horas copiando decretos e contratos em pergaminho. A lei impressa é poder absoluto...*",      "moedas": (30, 65),  "xp": (30, 50), "poder": (0, 3)},
    # Agricultura e Alimentação
    {"id": "agricultor",      "nome": "Agricultor Imperial",      "emoji": "🌾", "area": "Agricultura",    "narrativa": "*Os campos de Tenshi foram trabalhados com suas mãos. A colheita sustenta o Império...*",      "moedas": (25, 60),  "xp": (15, 30), "poder": (0, 3)},
    {"id": "chef",            "nome": "Chef do Palácio Imperial", "emoji": "👨‍🍳","area": "Gastronomia",    "narrativa": "*Preparando banquetes para a Corte. Cada prato é obra de arte e política...*",                "moedas": (50, 100), "xp": (20, 35), "poder": (0, 2)},
    {"id": "comerciante",     "nome": "Comerciante Imperial",     "emoji": "💼", "area": "Comércio",       "narrativa": "*Negociando rotas comerciais e contratos vantajosos nos mercados imperiais...*",               "moedas": (55, 110), "xp": (15, 30), "poder": (0, 3)},
    # Segurança
    {"id": "guarda",          "nome": "Guarda Imperial",          "emoji": "🛡️", "area": "Segurança",      "narrativa": "*Patrulhando as muralhas e canais de Tenshi. Sua presença disuade criminosos...*",             "moedas": (35, 75),  "xp": (20, 40), "poder": (3, 10)},
    {"id": "sacerdote",       "nome": "Sacerdote da Ordem",       "emoji": "📿", "area": "Religião",       "narrativa": "*Conduzindo rituais sagrados e lendo os astros em nome do Oráculo de Tenshi...*",              "moedas": (30, 65),  "xp": (30, 55), "poder": (2, 8)},
    {"id": "marinheiro",      "nome": "Marinheiro Imperial",      "emoji": "⚓", "area": "Marítimo",        "narrativa": "*Navegando pelos mares de Tenshi, mantendo as rotas comerciais abertas e seguras...*",         "moedas": (40, 85),  "xp": (18, 35), "poder": (1, 5)},
    {"id": "veterinario",     "nome": "Veterinário das Bestas",   "emoji": "🐉", "area": "Saúde Animal",   "narrativa": "*Cuidando dos dragões e bestas imperiais usadas nas fronteiras do Império...*",                "moedas": (45, 90),  "xp": (22, 42), "poder": (1, 6)},
    {"id": "gerente_hospital","nome": "Gestor do Hospital Imperial","emoji":"🏥","area": "Gestão",          "narrativa": "*Administrando o maior hospital de Tenshi — recursos, equipes, emergências e tudo mais...*",   "moedas": (80, 160), "xp": (20, 40), "poder": (0, 5)},
    {"id": "pesquisador",     "nome": "Pesquisador Arcano",       "emoji": "🔬", "area": "Pesquisa",       "narrativa": "*Estudando artefatos antigos e fenômenos mágicos nos laboratórios da Academia Imperial...*",   "moedas": (50, 100), "xp": (35, 65), "poder": (3, 12)},
]

# ─────────────────────────────────────────────────────────────────────────────
# TODOS OS EMPREGOS ILEGAIS
# ─────────────────────────────────────────────────────────────────────────────
EMPREGOS_ILEGAIS = [
    {"id": "contrabandista",  "nome": "Contrabandista",           "emoji": "📦", "area": "Comércio Ilegal", "narrativa": "*Transportando cargas proibidas pelas rotas secretas abaixo das muralhas de Tenshi...*",     "moedas": (80, 180), "xp": (15, 30), "poder": (2, 7),  "risco": 0.25},
    {"id": "assassino",       "nome": "Assassino de Aluguel",     "emoji": "🗡️", "area": "Violência",      "narrativa": "*Um contrato foi cumprido nas sombras. Ninguém viu. Ninguém saberá. O pagamento chegou...*",  "moedas": (120, 250),"xp": (20, 40), "poder": (5, 15), "risco": 0.35},
    {"id": "espiao",          "nome": "Espião de Elite",          "emoji": "🕵️", "area": "Inteligência",   "narrativa": "*Infiltrado na Corte rival, colhendo informações valiosas. Cada detalhe tem preço...*",       "moedas": (90, 200), "xp": (25, 45), "poder": (3, 10), "risco": 0.30},
    {"id": "falsificador",    "nome": "Falsificador de Decretos", "emoji": "📋", "area": "Fraude",         "narrativa": "*Imitando selos imperiais com perfeição assustadora. Os documentos passam em qualquer inspeção.*","moedas":(70, 150),"xp": (20, 38), "poder": (1, 5),  "risco": 0.20},
    {"id": "traficante",      "nome": "Traficante de Artefatos",  "emoji": "💎", "area": "Mercado Negro",  "narrativa": "*Vendendo relíquias proibidas para colecionadores que pagam uma fortuna pela raridade...*",    "moedas": (100, 220),"xp": (15, 30), "poder": (2, 8),  "risco": 0.28},
    {"id": "ladrao",          "nome": "Ladrão de Alta Classe",    "emoji": "🔓", "area": "Crime",          "narrativa": "*Entrando e saindo das mansões nobres de Tenshi sem deixar rastro algum. Arte pura...*",       "moedas": (70, 160), "xp": (18, 35), "poder": (2, 7),  "risco": 0.30},
    {"id": "chantagista",     "nome": "Chantagista",              "emoji": "📩", "area": "Crime",          "narrativa": "*Com informações comprometedoras em mãos, o pagamento mensal chega pontualmente...*",          "moedas": (90, 190), "xp": (15, 28), "poder": (1, 5),  "risco": 0.22},
    {"id": "pistoleiro",      "nome": "Pistoleiro da Máfia",      "emoji": "🔫", "area": "Máfia",          "narrativa": "*Executando ordens do Don sem questionar. Eficiência e lealdade são sua moeda...*",            "moedas": (85, 175), "xp": (20, 40), "poder": (4, 12), "risco": 0.32},
    {"id": "hacker_arcano",   "nome": "Hacker Arcano",            "emoji": "💻", "area": "Tecnologia/Magia","narrativa":"*Penetrando nos sistemas de runas da Tenshi Enterprise e extraindo dados valiosos...*",          "moedas": (110, 230),"xp": (25, 48), "poder": (3, 10), "risco": 0.25},
    {"id": "saqueador",       "nome": "Saqueador de Tumbas",      "emoji": "🏺", "area": "Exploração",     "narrativa": "*Adentrando catacumbas proibidas e extraindo relíquias dos mortos. Lucrativo e perigoso...*",  "moedas": (80, 170), "xp": (22, 42), "poder": (3, 9),  "risco": 0.38},
    {"id": "mercenario",      "nome": "Mercenário das Sombras",   "emoji": "⚔️", "area": "Conflito",       "narrativa": "*Serviços de combate para quem pagar mais. Sem lealdade, apenas contratos...*",               "moedas": (100, 210),"xp": (25, 50), "poder": (5, 15), "risco": 0.30},
    {"id": "cambista",        "nome": "Cambista do Submundo",     "emoji": "💱", "area": "Finanças Ilegais","narrativa":"*Convertendo moedas imperiais em divisas do submundo com spreads abusivos mas anônimos...*",    "moedas": (75, 155), "xp": (12, 25), "poder": (1, 4),  "risco": 0.18},
    {"id": "sequestrador",    "nome": "Operador de Resgates",     "emoji": "🎭", "area": "Crime Organizado","narrativa":"*Garantindo que o pagamento pelo 'retorno seguro' de nobres chegue antes deles...*",           "moedas": (150, 300),"xp": (20, 35), "poder": (3, 8),  "risco": 0.45},
]

# Dropdown de seleção de emprego
class SelectEmpregoView(discord.ui.View):
    def __init__(self, user_id: int, tipo: str):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.tipo    = tipo
        lista = EMPREGOS_LEGAIS if tipo == "legal" else EMPREGOS_ILEGAIS
        # Dividir em grupos de até 25 (limite Discord)
        self.add_item(EmpregoSelect(user_id, lista[:25], tipo))


class EmpregoSelect(discord.ui.Select):
    def __init__(self, user_id: int, empregos: list, tipo: str):
        self.user_id_ref = user_id
        self.tipo        = tipo
        opcoes = [
            discord.SelectOption(
                label=f"{e['emoji']} {e['nome']}",
                value=e["id"],
                description=f"{e['area']} | Ganho: {e['moedas'][0]}-{e['moedas'][1]} moedas",
                emoji=e["emoji"],
            )
            for e in empregos
        ]
        placeholder = "💼 Escolha um emprego legal..." if tipo == "legal" else "🖤 Escolha um serviço ilegal..."
        super().__init__(placeholder=placeholder, options=opcoes)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id_ref:
            await interaction.response.send_message("*Este menu não é seu.*", ephemeral=True)
            return

        emprego_id = self.values[0]
        lista = EMPREGOS_LEGAIS if self.tipo == "legal" else EMPREGOS_ILEGAIS
        emprego = next((e for e in lista if e["id"] == emprego_id), None)
        if not emprego:
            return

        user = get_user(interaction.user.id)
        agora = datetime.utcnow()

        # Cooldown
        if user.get("ultimo_trabalho"):
            ultimo = datetime.fromisoformat(user["ultimo_trabalho"])
            diferenca = agora - ultimo
            if diferenca < timedelta(seconds=COOLDOWN_TRABALHO):
                restante = timedelta(seconds=COOLDOWN_TRABALHO) - diferenca
                mins = int(restante.total_seconds() // 60)
                segs = int(restante.total_seconds() % 60)
                await interaction.response.send_message(
                    embed=embed_imperial("⏳ Em Recuperação", f"Próximo trabalho em: **{mins}m {segs}s**", 0x2B0A3D),
                    ephemeral=True
                )
                return

        moedas = random.randint(*emprego["moedas"])
        xp     = random.randint(*emprego["xp"])
        poder  = random.randint(*emprego["poder"])

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
                        f"**Você foi pego!** Uma multa de **{multa}** moedas foi aplicada pelos guardas imperiais.\n\n"
                        f"*Seja mais cuidadoso na próxima.*\n\n{SEP}"
                    ),
                    color=0x8B0000
                ).set_footer(text=RODAPE_IMPERIAL), ephemeral=False)
                return

        user["moedas"] = user.get("moedas", 0) + moedas
        user["xp"]     = user.get("xp", 0) + xp
        user["poder"]  = user.get("poder", 100) + poder
        user["ultimo_trabalho"] = agora.isoformat()
        nivel, _ = calcular_nivel(user["xp"])
        user["nivel"] = nivel
        save_user(interaction.user.id, user)

        pegada = user.get("pegada", "imperial")
        cor = 0x006400 if self.tipo == "legal" else 0x1C1C1C
        embed = discord.Embed(
            title=f"{emprego['emoji']} {emprego['nome'].upper()}",
            description=f"{emprego['narrativa']}\n\n{SEP}",
            color=cor
        )
        embed.add_field(name="💰 Ganho",  value=f"**+{moedas}** moedas",  inline=True)
        embed.add_field(name="✨ XP",     value=f"**+{xp}**",             inline=True)
        if poder > 0:
            embed.add_field(name="💥 Poder", value=f"**+{poder}**",       inline=True)
        embed.add_field(name="🏢 Área",   value=emprego["area"],           inline=True)
        if self.tipo == "ilegal":
            embed.add_field(name="⚠️ Aviso", value="*Trabalho ilegal — risco de ser interceptado*", inline=False)
        embed.set_footer(text=f"⏳ Próximo trabalho em 45 minutos  •  {RODAPE_IMPERIAL}")
        await interaction.response.send_message(embed=embed)


class Empregos:
    def __init__(self, bot):
        self.bot = bot

    async def handle_trabalhos(self, message):
        user   = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")
        embed = discord.Embed(
            title="💼 SISTEMA DE EMPREGOS IMPERIAL",
            description=(
                f"*Escolha como ganhar sua vida no Império de Tenshi...*\n{SEP}\n\n"
                f"**{len(EMPREGOS_LEGAIS)}** empregos legais disponíveis\n"
                f"**{len(EMPREGOS_ILEGAIS)}** serviços ilegais disponíveis\n\n"
                f"*Cooldown: 45 minutos entre turnos de trabalho*\n\n{SEP}"
            ),
            color=CORES_PEGADA.get(pegada, 0x2B0A3D)
        )
        embed.add_field(
            name="💼 Empregos Legais",
            value="`Tenshi, emprego legal` — Trabalho honrado e seguro\n*Menor risco, ganhos moderados*",
            inline=False
        )
        embed.add_field(
            name="🖤 Serviços Ilegais",
            value="`Tenshi, emprego ilegal` — Trabalho nas sombras\n*Alto risco, alto retorno — chance de ser pego*",
            inline=False
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
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

        pegada = user.get("pegada", "imperial")
        cor = 0x2B0A3D if tipo == "legal" else 0x1C1C1C

        if tipo == "ilegal":
            # Checar se tem pegada/acesso
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
                f"*{'Oportunidades de trabalho honrado no Império...' if tipo == 'legal' else 'O submundo oferece serviços para os corajosos...'}*\n{SEP}\n\n"
                f"Escolha um emprego no menu abaixo:"
            ),
            color=cor
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = SelectEmpregoView(message.author.id, tipo)
        await message.channel.send(embed=embed, view=view)
