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
from academia_curriculo import materias_academicas, tem_diploma as tem_diploma_curriculo

COOLDOWN_TRABALHO = 45 * 60  # 45 minutos
PREFIXO_CARGO_PROFISSAO = "Profissão • "

REGRAS_TRABALHO = (
    "Cada turno possui 45 minutos de recuperação.",
    "Empregos de alta patente exigem o diploma e o nível indicados.",
    "Concluir um turno legal define a profissão ativa no perfil e sincroniza o cargo no servidor.",
    "Ao trocar de profissão, o cargo profissional anterior é removido.",
    "Serviços ilegais podem causar interceptação, multa e não geram cargo público.",
    "Diplomas e cargos não substituem permissões administrativas do servidor.",
)


async def _sincronizar_profissao(guild, member, emprego: dict, user: dict) -> str:
    """Atualiza perfil e cargo Discord da profissão legal exercida."""
    nome_cargo = f"{PREFIXO_CARGO_PROFISSAO}{emprego['nome']}"[:100]
    user["emprego_id"] = emprego["id"]
    user["emprego_nome"] = emprego["nome"]
    user["cargo_trabalho"] = nome_cargo
    user.setdefault("ficha", {})["profissao"] = emprego["nome"]

    if guild is None or member is None:
        return "Profissão salva no perfil; cargo do servidor indisponível."
    try:
        role = discord.utils.get(guild.roles, name=nome_cargo)
        if role is None:
            role = await guild.create_role(name=nome_cargo, color=discord.Color.dark_teal(), reason="Profissão do sistema Tenshi")
        if role not in member.roles:
            await member.add_roles(role, reason="Profissão assumida no sistema Tenshi")
        antigos = [role_antigo for role_antigo in member.roles if role_antigo.name.startswith(PREFIXO_CARGO_PROFISSAO) and role_antigo.name != nome_cargo]
        if antigos:
            await member.remove_roles(*antigos, reason="Troca de profissão no sistema Tenshi")
        return f"Cargo `{nome_cargo}` sincronizado e exibido no perfil."
    except discord.Forbidden:
        return f"Profissão salva no perfil; não consegui atribuir `{nome_cargo}` por falta de permissão/hierarquia."
    except discord.HTTPException as exc:
        return f"Profissão salva no perfil; falha ao sincronizar cargo: {str(exc)[:80]}"

# ─── MATÉRIAS E SEUS DADOS DE ESTUDO ─────────────────────────────────────────
MATERIAS_INFO = {
    key: {
        "nome": value.get("nome", key),
        "emoji": value.get("emoji", "🎓"),
        "presenças": 3,
        "tempo_estudo_h": value.get("tempo_estudo_h", 12),
    }
    for key, value in materias_academicas().items()
}


def _tem_diploma(user: dict, materia: str) -> bool:
    """Verifica se o usuário possui diploma na matéria especificada."""
    return tem_diploma_curriculo(user, materia)


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
EMPREGOS_LEGAIS.extend([
    {
        "id": "ministro_imperial",
        "nome": "Ministro Imperial", "emoji": "👑", "area": "Governo",
        "narrativa": "*Coordenando decretos, crises e agendas de Estado com disciplina de gabinete...*",
        "moedas": (150, 260), "xp": (35, 70), "poder": (2, 8),
        "requer_diploma": "governo_imperial",
        "nivel_minimo": 12,
        "descricao_cargo": "Cargo alto de governo. Exige Governo Imperial e nivel 12+.",
    },
    {
        "id": "gestor_crises",
        "nome": "Gestor de Crises", "emoji": "🏛️", "area": "Governo",
        "narrativa": "*Organizando respostas rapidas para conflitos, falhas de infraestrutura e tensoes politicas...*",
        "moedas": (120, 220), "xp": (32, 62), "poder": (1, 6),
        "requer_diploma": "governo_imperial",
        "nivel_minimo": 8,
        "descricao_cargo": "Planejamento e resposta administrativa a crises imperiais.",
    },
    {
        "id": "chanceler_juridico",
        "nome": "Chanceler Juridico", "emoji": "⚖️", "area": "Direito",
        "narrativa": "*Emitindo pareceres sobre tratados, sucessao e conflitos administrativos do Trono...*",
        "moedas": (140, 240), "xp": (30, 60), "poder": (1, 6),
        "requer_diploma": "direito_imperial",
        "nivel_minimo": 12,
        "descricao_cargo": "Direito de alta patente para pareceres e tratados.",
    },
    {
        "id": "diretor_enterprise",
        "nome": "Diretor Tenshi Enterprise", "emoji": "💼", "area": "Corporativo",
        "narrativa": "*Supervisionando contratos, investimentos e estrategia economica da Enterprise...*",
        "moedas": (150, 280), "xp": (28, 58), "poder": (0, 5),
        "requer_diploma": "tenshi_enterprise",
        "nivel_minimo": 10,
        "descricao_cargo": "Gestao corporativa de alto escalao.",
    },
    {
        "id": "analista_investimentos",
        "nome": "Analista de Investimentos", "emoji": "📈", "area": "Financas",
        "narrativa": "*Avaliando risco, patrimonio e oportunidades de mercado para a Coroa...*",
        "moedas": (110, 210), "xp": (25, 50), "poder": (0, 4),
        "requer_diploma": "tenshi_enterprise",
        "nivel_minimo": 6,
        "descricao_cargo": "Financas, bolsa, venture capital e gestao patrimonial.",
    },
    {
        "id": "diretor_compliance",
        "nome": "Diretor de Compliance", "emoji": "📋", "area": "Corporativo",
        "narrativa": "*Revisando contratos, condutas e riscos para manter a Enterprise dentro da lei imperial...*",
        "moedas": (120, 230), "xp": (25, 55), "poder": (0, 4),
        "requer_diploma": "tenshi_enterprise",
        "nivel_minimo": 8,
        "descricao_cargo": "Compliance, ESG e auditoria corporativa.",
    },
    {
        "id": "engenheiro_ia",
        "nome": "Engenheiro de IA Imperial", "emoji": "🤖", "area": "Tecnologia",
        "narrativa": "*Treinando automacoes e sistemas inteligentes para apoiar a administracao imperial...*",
        "moedas": (140, 260), "xp": (35, 75), "poder": (0, 5),
        "requer_diploma": "tecnologia_ia",
        "nivel_minimo": 8,
        "descricao_cargo": "IA, dados, automacao e sistemas.",
    },
    {
        "id": "arquiteto_cloud",
        "nome": "Arquiteto Cloud", "emoji": "☁️", "area": "Tecnologia",
        "narrativa": "*Mantendo servidores, backups e aplicacoes imperiais resilientes em nuvem...*",
        "moedas": (120, 230), "xp": (28, 62), "poder": (0, 4),
        "requer_diploma": "tecnologia_ia",
        "nivel_minimo": 7,
        "descricao_cargo": "Cloud, banco de dados e disponibilidade de sistemas.",
    },
    {
        "id": "defensor_cibernetico",
        "nome": "Defensor Cibernetico", "emoji": "🛡️", "area": "Seguranca Digital",
        "narrativa": "*Auditorias defensivas protegem dados, canais e registros da Casa Tenshi...*",
        "moedas": (130, 250), "xp": (34, 72), "poder": (0, 6),
        "requer_diploma": "seguranca_digital",
        "nivel_minimo": 8,
        "descricao_cargo": "Defesa digital, criptografia e resposta a incidentes de RP.",
    },
    {
        "id": "criptografo",
        "nome": "Criptografo Imperial", "emoji": "🔐", "area": "Seguranca Digital",
        "narrativa": "*Selando registros, rotas de comunicacao e arquivos sigilosos com protocolos de cifra...*",
        "moedas": (115, 220), "xp": (28, 60), "poder": (0, 4),
        "requer_diploma": "seguranca_digital",
        "nivel_minimo": 6,
        "descricao_cargo": "Criptografia narrativa e protecao de dados.",
    },
    {
        "id": "engenheiro_aeroespacial",
        "nome": "Engenheiro Aeroespacial", "emoji": "🚀", "area": "Engenharia",
        "narrativa": "*Projetando mecanismos de voo, propulsao e transporte estrategico do Imperio...*",
        "moedas": (130, 245), "xp": (32, 66), "poder": (0, 5),
        "requer_diploma": "engenharia_imperial",
        "nivel_minimo": 9,
        "descricao_cargo": "Especializacao avancada da Engenharia Imperial.",
    },
    {
        "id": "engenheiro_biomedico",
        "nome": "Engenheiro Biomedico", "emoji": "⚕️", "area": "Engenharia/Saude",
        "narrativa": "*Criando equipamentos e protocolos tecnicos para o Hospital Imperial...*",
        "moedas": (115, 225), "xp": (30, 64), "poder": (0, 4),
        "requer_diploma": "engenharia_imperial",
        "nivel_minimo": 7,
        "descricao_cargo": "Integra medicina, ciencia e engenharia.",
    },
    {
        "id": "oficial_guarda",
        "nome": "Oficial da Guarda Imperial", "emoji": "⚔️", "area": "Seguranca",
        "narrativa": "*Comandando rondas, escoltas e protocolos de protecao da Coroa...*",
        "moedas": (105, 210), "xp": (34, 70), "poder": (6, 16),
        "requer_diploma": "militar_imperial",
        "nivel_minimo": 7,
        "descricao_cargo": "Comando militar e protecao executiva.",
    },
    {
        "id": "analista_inteligencia",
        "nome": "Analista de Inteligencia", "emoji": "🕵️", "area": "Inteligencia",
        "narrativa": "*Cruzando relatos, mapas de risco e sinais politicos para orientar a Coroa...*",
        "moedas": (115, 230), "xp": (34, 72), "poder": (1, 7),
        "requer_diploma": "inteligencia_imperial",
        "nivel_minimo": 8,
        "descricao_cargo": "Analise de risco e relatorios estrategicos.",
    },
    {
        "id": "chanceler",
        "nome": "Chanceler Diplomatico", "emoji": "🤝", "area": "Diplomacia",
        "narrativa": "*Conduzindo tratados, mediacoes e recepcoes formais em nome da Casa...*",
        "moedas": (130, 240), "xp": (30, 64), "poder": (0, 5),
        "requer_diploma": "diplomacia",
        "nivel_minimo": 8,
        "descricao_cargo": "Diplomacia, protocolo e mediacao de conflitos.",
    },
    {
        "id": "interprete_diplomatico",
        "nome": "Interprete Diplomatico", "emoji": "📚", "area": "Linguas",
        "narrativa": "*Traduzindo acordos, discursos e documentos cerimoniais com precisao...*",
        "moedas": (90, 175), "xp": (25, 55), "poder": (0, 3),
        "requer_diploma": "linguas_imperiais",
        "nivel_minimo": 4,
        "descricao_cargo": "Traducao e protocolo linguistico.",
    },
    {
        "id": "biomedico",
        "nome": "Biomedico Imperial", "emoji": "🧬", "area": "Saude/Ciencia",
        "narrativa": "*Analisando amostras, laudos e pesquisas para apoiar o Hospital Imperial...*",
        "moedas": (105, 205), "xp": (30, 65), "poder": (0, 3),
        "requer_diploma": "medicina_ciencias",
        "nivel_minimo": 6,
        "descricao_cargo": "Medicina, ciencias e diagnostico narrativo.",
    },
    {
        "id": "mestre_etiqueta",
        "nome": "Mestre de Etiqueta Imperial", "emoji": "🎭", "area": "Cultura",
        "narrativa": "*Preparando recepcoes, postura de salao e oratoria para eventos nobres...*",
        "moedas": (85, 170), "xp": (25, 52), "poder": (0, 3),
        "requer_diploma": "artes_etiqueta",
        "nivel_minimo": 4,
        "descricao_cargo": "Etiqueta, artes, oratoria e protocolo social.",
    },
    {
        "id": "genealogista",
        "nome": "Genealogista da Coroa", "emoji": "📜", "area": "Arquivo",
        "narrativa": "*Registrando linhagens, titulos, sucessoes e memoria historica da Familia Imperial...*",
        "moedas": (95, 190), "xp": (28, 58), "poder": (0, 4),
        "requer_diploma": "familia_imperial",
        "nivel_minimo": 5,
        "descricao_cargo": "Genealogia, arquivo imperial e administracao da Coroa.",
    },
    {
        "id": "mestre_cerimonial",
        "nome": "Ritualista de Tenshi", "emoji": "🔮", "area": "Cerimonial",
        "narrativa": "*Ensaiando votos, juramentos, coroacoes e ritos solenes com precisao impecavel...*",
        "moedas": (110, 220), "xp": (32, 70), "poder": (0, 5),
        "requer_diploma": "mestres_cerimoniais",
        "nivel_minimo": 7,
        "descricao_cargo": "Organiza casamentos, coroacoes e o Ritual de Tenshi; a celebracao pertence a Tenshi IA.",
    },
    {
        "id": "regente_treinamento",
        "nome": "Regente em Treinamento", "emoji": "🏛️", "area": "Coroa",
        "narrativa": "*Assumindo simulacoes de governo, sucessao e gestao de Estado sob supervisao...*",
        "moedas": (160, 300), "xp": (40, 85), "poder": (2, 10),
        "requer_diploma": "herdeiros_coroa",
        "nivel_minimo": 15,
        "descricao_cargo": "Programa obrigatorio dos herdeiros e lideranca de Estado.",
    },
])

EMPREGOS_LEGAIS.extend([
    {
        "id": "jornalista_imperial", "nome": "Jornalista Imperial", "emoji": "📰", "area": "Comunicação",
        "narrativa": "*Apurando fatos, ouvindo cidadãos e publicando o boletim oficial sem sacrificar a verdade...*",
        "moedas": (55, 115), "xp": (25, 48), "poder": (0, 3), "requer_diploma": "jornalismo_comunicacao", "nivel_minimo": 3,
        "descricao_cargo": "Reportagem, entrevistas e cobertura dos acontecimentos do Império.",
    },
    {
        "id": "editor_gazeta", "nome": "Editor da Gazeta", "emoji": "✒️", "area": "Comunicação",
        "narrativa": "*Revisando manchetes, verificando fontes e fechando a próxima edição da Gazeta de Tenshi...*",
        "moedas": (75, 145), "xp": (28, 52), "poder": (0, 3), "requer_diploma": "jornalismo_comunicacao", "nivel_minimo": 6,
        "descricao_cargo": "Coordenação editorial e verificação de informações públicas.",
    },
    {
        "id": "economista_imperial", "nome": "Economista Imperial", "emoji": "📈", "area": "Economia",
        "narrativa": "*Analisando inflação, arrecadação e atividade comercial para orientar as decisões da Coroa...*",
        "moedas": (90, 175), "xp": (24, 46), "poder": (0, 4), "requer_diploma": "economia_financas", "nivel_minimo": 5,
        "descricao_cargo": "Análise econômica, orçamento e políticas monetárias de RP.",
    },
    {
        "id": "tesoureiro_real", "nome": "Tesoureiro Real", "emoji": "🪙", "area": "Finanças",
        "narrativa": "*Conferindo cofres, pagamentos e reservas com precisão digna da confiança do Trono...*",
        "moedas": (105, 195), "xp": (22, 44), "poder": (0, 4), "requer_diploma": "economia_financas", "nivel_minimo": 8,
        "descricao_cargo": "Gestão do tesouro, orçamento e prestação de contas.",
    },
    {
        "id": "urbanista_imperial", "nome": "Urbanista Imperial", "emoji": "🏙️", "area": "Gestão Pública",
        "narrativa": "*Planejando bairros, serviços e rotas para que a capital cresça sem perder sua ordem...*",
        "moedas": (80, 160), "xp": (28, 55), "poder": (0, 4), "requer_diploma": "gestao_publica", "nivel_minimo": 5,
        "descricao_cargo": "Planejamento urbano e coordenação de serviços públicos.",
    },
    {
        "id": "ouvidor_imperial", "nome": "Ouvidor Imperial", "emoji": "📬", "area": "Gestão Pública",
        "narrativa": "*Recebendo demandas dos cidadãos e transformando reclamações dispersas em providências verificáveis...*",
        "moedas": (60, 125), "xp": (30, 58), "poder": (0, 3), "requer_diploma": "gestao_publica", "nivel_minimo": 3,
        "descricao_cargo": "Ouvidoria, transparência e acompanhamento de serviços.",
    },
    {
        "id": "psicologo_imperial", "nome": "Psicólogo Imperial", "emoji": "🧠", "area": "Saúde Mental",
        "narrativa": "*Escutando conflitos e oferecendo orientação narrativa com ética, sigilo e atenção...*",
        "moedas": (75, 150), "xp": (32, 62), "poder": (0, 3), "requer_diploma": "psicologia_estrategica", "nivel_minimo": 5,
        "descricao_cargo": "Acolhimento e psicologia aplicada ao RP; não substitui cuidado real.",
    },
    {
        "id": "mediador_comunitario", "nome": "Mediador Comunitário", "emoji": "🫱🏻‍🫲🏽", "area": "Mediação",
        "narrativa": "*Conduzindo uma conversa difícil até que as partes encontrem limites e compromissos possíveis...*",
        "moedas": (55, 115), "xp": (34, 64), "poder": (0, 3), "requer_diploma": "psicologia_estrategica", "nivel_minimo": 3,
        "descricao_cargo": "Mediação de conflitos comunitários e institucionais.",
    },
    {
        "id": "agronomo_imperial", "nome": "Agrônomo Imperial", "emoji": "🌱", "area": "Agricultura",
        "narrativa": "*Avaliando solo, irrigação e colheitas para proteger o abastecimento das províncias...*",
        "moedas": (65, 135), "xp": (28, 54), "poder": (0, 4), "requer_diploma": "ecologia_agricultura", "nivel_minimo": 4,
        "descricao_cargo": "Produção agrícola, manejo sustentável e segurança alimentar.",
    },
    {
        "id": "fiscal_ambiental", "nome": "Fiscal Ambiental", "emoji": "🌳", "area": "Meio Ambiente",
        "narrativa": "*Inspecionando rios, bosques e operações comerciais para impedir danos ao território imperial...*",
        "moedas": (70, 145), "xp": (30, 58), "poder": (1, 5), "requer_diploma": "ecologia_agricultura", "nivel_minimo": 5,
        "descricao_cargo": "Proteção ambiental, fiscalização e recuperação de áreas.",
    },
    {
        "id": "chef_real", "nome": "Chef Real", "emoji": "👨‍🍳", "area": "Gastronomia",
        "narrativa": "*Coordenando a cozinha do palácio para um banquete que precisa impressionar aliados e rivais...*",
        "moedas": (70, 145), "xp": (24, 48), "poder": (0, 3), "requer_diploma": "gastronomia_hospitalidade", "nivel_minimo": 4,
        "descricao_cargo": "Gastronomia profissional, segurança alimentar e banquetes.",
    },
    {
        "id": "gestor_hospedagem", "nome": "Gestor de Hospedagem", "emoji": "🏨", "area": "Hospitalidade",
        "narrativa": "*Organizando aposentos, recepção e protocolo para visitantes de todo o Império...*",
        "moedas": (65, 135), "xp": (26, 50), "poder": (0, 3), "requer_diploma": "gastronomia_hospitalidade", "nivel_minimo": 4,
        "descricao_cargo": "Gestão de hospedagem, eventos e experiência de visitantes.",
    },
])


EMPREGOS_LEGAIS.extend([
    {"id": "conselheiro_coroa", "nome": "Conselheiro da Coroa", "emoji": "🏛️", "area": "Governo", "narrativa": "*Analisando uma decisão de Estado e apresentando alternativas prudentes ao Conselho...*", "moedas": (120, 220), "xp": (32, 62), "poder": (1, 6), "requer_diploma": "governo_imperial", "nivel_minimo": 9, "descricao_cargo": "Assessoria estratégica à Coroa."},
    {"id": "consultor_legal", "nome": "Consultor Legal", "emoji": "📚", "area": "Direito", "narrativa": "*Revisando contratos e pareceres para evitar conflitos com o Código Imperial...*", "moedas": (85, 165), "xp": (25, 48), "poder": (0, 3), "requer_diploma": "direito_imperial", "nivel_minimo": 5, "descricao_cargo": "Consultoria jurídica e contratos."},
    {"id": "gestor_patrimonial", "nome": "Gestor Patrimonial", "emoji": "🏦", "area": "Finanças", "narrativa": "*Reorganizando ativos e reservas para proteger o patrimônio de uma Casa Imperial...*", "moedas": (100, 190), "xp": (24, 46), "poder": (0, 4), "requer_diploma": "tenshi_enterprise", "nivel_minimo": 7, "descricao_cargo": "Gestão de patrimônio e risco."},
    {"id": "analista_dados", "nome": "Analista de Dados", "emoji": "📊", "area": "Tecnologia", "narrativa": "*Transformando registros dispersos em indicadores claros para a administração imperial...*", "moedas": (85, 170), "xp": (30, 60), "poder": (0, 4), "requer_diploma": "tecnologia_ia", "nivel_minimo": 5, "descricao_cargo": "Dados, métricas e inteligência analítica."},
    {"id": "dev_imperial", "nome": "Desenvolvedor Imperial", "emoji": "💻", "area": "Tecnologia", "narrativa": "*Construindo uma automação para reduzir a burocracia dos registros da Casa...*", "moedas": (90, 180), "xp": (32, 64), "poder": (0, 4), "requer_diploma": "tecnologia_ia", "nivel_minimo": 5, "descricao_cargo": "Desenvolvimento de sistemas narrativos."},
    {"id": "analista_osint", "nome": "Analista OSINT", "emoji": "🔎", "area": "Segurança Digital", "narrativa": "*Cruzando fontes públicas do Império para verificar uma informação sensível...*", "moedas": (85, 165), "xp": (30, 58), "poder": (0, 4), "requer_diploma": "seguranca_digital", "nivel_minimo": 6, "descricao_cargo": "Pesquisa em fontes abertas dentro do RP."},
    {"id": "protector_executivo", "nome": "Protetor Executivo", "emoji": "🛡️", "area": "Segurança", "narrativa": "*Planejando a escolta de uma autoridade por uma rota de risco controlado...*", "moedas": (95, 180), "xp": (28, 54), "poder": (4, 10), "requer_diploma": "militar_imperial", "nivel_minimo": 7, "descricao_cargo": "Escolta e proteção de autoridades no RP."},
    {"id": "instrutor_militar", "nome": "Instrutor Militar", "emoji": "🎖️", "area": "Defesa", "narrativa": "*Conduzindo treinamento de disciplina, estratégia e sobrevivência para novos recrutas...*", "moedas": (85, 160), "xp": (35, 68), "poder": (3, 8), "requer_diploma": "militar_imperial", "nivel_minimo": 7, "descricao_cargo": "Formação e treinamento da Guarda."},
    {"id": "contrainteligencia", "nome": "Agente de Contrainteligência", "emoji": "🕶️", "area": "Inteligência", "narrativa": "*Identificando inconsistências em relatórios antes que uma falsa pista alcance o Conselho...*", "moedas": (100, 190), "xp": (32, 62), "poder": (1, 5), "requer_diploma": "inteligencia_imperial", "nivel_minimo": 7, "descricao_cargo": "Proteção de informações e análise de ameaças no RP."},
    {"id": "investigador_estrategico", "nome": "Investigador Estratégico", "emoji": "🧭", "area": "Inteligência", "narrativa": "*Organizando depoimentos, registros e cronologias para esclarecer uma crise imperial...*", "moedas": (90, 175), "xp": (34, 65), "poder": (0, 5), "requer_diploma": "inteligencia_imperial", "nivel_minimo": 6, "descricao_cargo": "Investigação narrativa e análise estratégica."},
    {"id": "mediador_imperial", "nome": "Mediador Imperial", "emoji": "🕊️", "area": "Diplomacia", "narrativa": "*Reconstruindo o diálogo entre duas facções antes que a tensão vire conflito...*", "moedas": (85, 165), "xp": (36, 68), "poder": (0, 4), "requer_diploma": "diplomacia", "nivel_minimo": 5, "descricao_cargo": "Mediação diplomática e de facções."},
    {"id": "negociador_internacional", "nome": "Negociador Internacional", "emoji": "🌐", "area": "Diplomacia", "narrativa": "*Ajustando cláusulas de um tratado para preservar os interesses da Casa Tenshi...*", "moedas": (105, 195), "xp": (30, 58), "poder": (0, 5), "requer_diploma": "diplomacia", "nivel_minimo": 8, "descricao_cargo": "Tratados e negociação internacional de RP."},
    {"id": "tradutor_imperial", "nome": "Tradutor Imperial", "emoji": "🗣️", "area": "Línguas", "narrativa": "*Traduzindo uma correspondência diplomática sem perder tom, intenção ou protocolo...*", "moedas": (70, 140), "xp": (32, 60), "poder": (0, 3), "requer_diploma": "linguas_imperiais", "nivel_minimo": 4, "descricao_cargo": "Tradução narrativa e documental."},
    {"id": "professor_linguas", "nome": "Professor de Línguas", "emoji": "🔤", "area": "Educação", "narrativa": "*Preparando uma aula de idioma e etiqueta linguística para diplomatas iniciantes...*", "moedas": (70, 135), "xp": (38, 72), "poder": (0, 3), "requer_diploma": "linguas_imperiais", "nivel_minimo": 6, "descricao_cargo": "Ensino de línguas no RP."},
    {"id": "curador_artes", "nome": "Curador de Artes", "emoji": "🖼️", "area": "Cultura", "narrativa": "*Selecionando obras e construindo a narrativa de uma exposição da Galeria Imperial...*", "moedas": (70, 145), "xp": (32, 62), "poder": (0, 3), "requer_diploma": "artes_etiqueta", "nivel_minimo": 5, "descricao_cargo": "Curadoria de exposições e eventos culturais."},
    {"id": "orador_cerimonial", "nome": "Orador Cerimonial", "emoji": "🎙️", "area": "Cerimonial", "narrativa": "*Apresentando uma solenidade com clareza, ritmo e respeito ao protocolo...*", "moedas": (65, 130), "xp": (34, 66), "poder": (0, 3), "requer_diploma": "artes_etiqueta", "nivel_minimo": 4, "descricao_cargo": "Oratória e apresentação de eventos."},
    {"id": "arquivista_imperial", "nome": "Arquivista Imperial", "emoji": "🗄️", "area": "Arquivo", "narrativa": "*Catalogando documentos de uma linhagem para preservar sua memória e autenticidade...*", "moedas": (75, 145), "xp": (36, 68), "poder": (0, 3), "requer_diploma": "familia_imperial", "nivel_minimo": 5, "descricao_cargo": "Arquivo, memória e genealogia da Casa."},
    {"id": "administrador_coroa", "nome": "Administrador da Coroa", "emoji": "👑", "area": "Casa Imperial", "narrativa": "*Coordenando agenda, patrimônio e registros internos da Família Imperial...*", "moedas": (105, 200), "xp": (28, 55), "poder": (1, 5), "requer_diploma": "familia_imperial", "nivel_minimo": 8, "descricao_cargo": "Administração institucional da Coroa."},
    {"id": "organizador_coroacoes", "nome": "Organizador de Coroações", "emoji": "💠", "area": "Cerimonial", "narrativa": "*Conferindo símbolos, precedência e juramentos para uma coroação impecável...*", "moedas": (90, 175), "xp": (34, 65), "poder": (0, 4), "requer_diploma": "mestres_cerimoniais", "nivel_minimo": 6, "descricao_cargo": "Planejamento de coroações e solenidades."},
    {"id": "oficial_matrimonial", "nome": "Ritualista Matrimonial", "emoji": "🔮", "area": "Cerimonial", "narrativa": "*Verificando registros, testemunhas e agenda antes de abrir o Ritual de Tenshi para a celebração da IA...*", "moedas": (75, 150), "xp": (35, 68), "poder": (0, 3), "requer_diploma": "mestres_cerimoniais", "nivel_minimo": 5, "descricao_cargo": "Conduz o Ritual de Tenshi enquanto a própria IA celebra o casamento."},
    {"id": "assessor_herdeiro", "nome": "Assessor de Herdeiro", "emoji": "📜", "area": "Sucessão", "narrativa": "*Preparando estudos, agenda e relatórios para a formação de um herdeiro da Coroa...*", "moedas": (110, 205), "xp": (35, 66), "poder": (1, 5), "requer_diploma": "herdeiros_coroa", "nivel_minimo": 10, "descricao_cargo": "Assessoria à formação e agenda dos herdeiros."},
    {"id": "guardiao_sucessao", "nome": "Guardião da Sucessão", "emoji": "🔱", "area": "Sucessão", "narrativa": "*Protegendo documentos e protocolos que garantem a continuidade legítima da Coroa...*", "moedas": (125, 230), "xp": (32, 62), "poder": (3, 9), "requer_diploma": "herdeiros_coroa", "nivel_minimo": 12, "descricao_cargo": "Proteção dos protocolos sucessórios do RP."},
    # Novos empregos baseados nos cursos expandidos
    {"id": "arquiteto_imperial_novo", "nome": "Arquiteto Imperial", "emoji": "🏛️", "area": "Arquitetura", "narrativa": "*Projetando edifícios majestosos que definem a skyline do Império...*", "moedas": (95, 185), "xp": (28, 56), "poder": (0, 4), "requer_diploma": "arquitetura_imperial", "nivel_minimo": 6, "descricao_cargo": "Projetos arquitetônicos e design de interiores."},
    {"id": "designer_interiores", "nome": "Designer de Interiores", "emoji": "🎨", "area": "Design", "narrativa": "*Transformando salões vazios em espaços elegantes e funcionais para a nobreza...*", "moedas": (75, 145), "xp": (24, 48), "poder": (0, 3), "requer_diploma": "arquitetura_imperial", "nivel_minimo": 4, "descricao_cargo": "Design de interiores e decoração imperial."},
    {"id": "gestor_logistico", "nome": "Gestor Logístico Imperial", "emoji": "🚚", "area": "Logística", "narrativa": "*Coordenando frotas e rotas para manter o abastecimento de todo o Império...*", "moedas": (85, 170), "xp": (26, 52), "poder": (0, 4), "requer_diploma": "logistica_transportes", "nivel_minimo": 5, "descricao_cargo": "Gestão de transporte e cadeia de suprimentos."},
    {"id": "coordenador_transportes", "nome": "Coordenador de Transportes", "emoji": "🚛", "area": "Logística", "narrativa": "*Organizando rotas e horários para otimizar o fluxo de mercadorias...*", "moedas": (70, 140), "xp": (22, 44), "poder": (0, 3), "requer_diploma": "logistica_transportes", "nivel_minimo": 3, "descricao_cargo": "Coordenação de rotas e transportes."},
    {"id": "gerente_armazem", "nome": "Gerente de Armazém", "emoji": "📦", "area": "Logística", "narrativa": "*Supervisionando o armazenamento e distribuição de suprimentos imperiais...*", "moedas": (65, 130), "xp": (20, 40), "poder": (0, 3), "requer_diploma": "logistica_transportes", "nivel_minimo": 3, "descricao_cargo": "Gestão de armazéns e estoque."},
    {"id": "diretor_marketing", "nome": "Diretor de Marketing Imperial", "emoji": "📢", "area": "Marketing", "narrativa": "*Criando campanhas que elevam a imagem e influência do Império...*", "moedas": (100, 195), "xp": (28, 56), "poder": (0, 4), "requer_diploma": "marketing_imperial", "nivel_minimo": 6, "descricao_cargo": "Estratégias de marketing e comunicação."},
    {"id": "analista_mercado", "nome": "Analista de Mercado", "emoji": "📊", "area": "Marketing", "narrativa": "*Estudando tendências e comportamentos para orientar decisões comerciais...*", "moedas": (75, 150), "xp": (24, 48), "poder": (0, 3), "requer_diploma": "marketing_imperial", "nivel_minimo": 4, "descricao_cargo": "Análise de mercado e tendências."},
    {"id": "relacoes_publicas", "nome": "Relações Públicas Imperial", "emoji": "🎤", "area": "Comunicação", "narrativa": "*Gerenciando a imagem pública e respondendo a questões da imprensa...*", "moedas": (80, 160), "xp": (26, 52), "poder": (0, 3), "requer_diploma": "marketing_imperial", "nivel_minimo": 4, "descricao_cargo": "Relações públicas e comunicação institucional."},
    {"id": "diretor_rh", "nome": "Diretor de RH Imperial", "emoji": "👥", "area": "Recursos Humanos", "narrativa": "*Recrutando os melhores talentos para servir o Império...*", "moedas": (90, 180), "xp": (26, 52), "poder": (0, 4), "requer_diploma": "recursos_humanos", "nivel_minimo": 6, "descricao_cargo": "Gestão de recursos humanos e talentos."},
    {"id": "recrutador", "nome": "Recrutador Imperial", "emoji": "🔍", "area": "Recursos Humanos", "narrativa": "*Buscando e avaliando candidatos para preencher vagas imperiais...*", "moedas": (65, 130), "xp": (22, 44), "poder": (0, 3), "requer_diploma": "recursos_humanos", "nivel_minimo": 3, "descricao_cargo": "Recrutamento e seleção de pessoal."},
    {"id": "treinador_rh", "nome": "Treinador Corporativo", "emoji": "📚", "area": "Recursos Humanos", "narrativa": "*Capacitando funcionários para melhor desempenho em suas funções...*", "moedas": (60, 120), "xp": (20, 40), "poder": (0, 3), "requer_diploma": "recursos_humanos", "nivel_minimo": 3, "descricao_cargo": "Treinamento e desenvolvimento de equipes."},
    {"id": "cfo_imperial", "nome": "CFO Imperial", "emoji": "💹", "area": "Finanças Corporativas", "narrativa": "*Supervisionando as finanças corporativas e estratégias de investimento...*", "moedas": (130, 250), "xp": (32, 64), "poder": (0, 5), "requer_diploma": "financas_corporativas", "nivel_minimo": 10, "descricao_cargo": "Direção financeira corporativa de alto nível."},
    {"id": "analista_financeiro", "nome": "Analista Financeiro", "emoji": "📈", "area": "Finanças", "narrativa": "*Analisando relatórios financeiros e identificando oportunidades de melhoria...*", "moedas": (80, 160), "xp": (26, 52), "poder": (0, 4), "requer_diploma": "financas_corporativas", "nivel_minimo": 5, "descricao_cargo": "Análise financeira e relatórios."},
    {"id": "gestor_investimentos", "nome": "Gestor de Investimentos", "emoji": "💰", "area": "Investimentos", "narrativa": "*Gerenciando portfólios de investimento para maximizar retornos...*", "moedas": (95, 185), "xp": (28, 56), "poder": (0, 4), "requer_diploma": "financas_corporativas", "nivel_minimo": 6, "descricao_cargo": "Gestão de investimentos e portfólios."},
    {"id": "analista_politico", "nome": "Analista Político Imperial", "emoji": "🏛️", "area": "Política", "narrativa": "*Analisando cenários políticos e tendências para orientar decisões...*", "moedas": (85, 170), "xp": (28, 56), "poder": (0, 4), "requer_diploma": "ciencias_politicas", "nivel_minimo": 5, "descricao_cargo": "Análise política e relações governamentais."},
    {"id": "assessor_governamental", "nome": "Assessor Governamental", "emoji": "📋", "area": "Política", "narrativa": "*Assessorando em políticas públicas e decisões administrativas...*", "moedas": (75, 150), "xp": (24, 48), "poder": (0, 3), "requer_diploma": "ciencias_politicas", "nivel_minimo": 4, "descricao_cargo": "Assessoria em políticas públicas."},
    {"id": "consultor_politico", "nome": "Consultor Político", "emoji": "🎯", "area": "Política", "narrativa": "*Fornecendo consultoria estratégica para decisões políticas complexas...*", "moedas": (90, 180), "xp": (26, 52), "poder": (0, 4), "requer_diploma": "ciencias_politicas", "nivel_minimo": 6, "descricao_cargo": "Consultoria política estratégica."},
    {"id": "historiador_imperial", "nome": "Historiador Imperial", "emoji": "📜", "area": "História", "narrativa": "*Documentando e preservando a rica história do Império de Tenshi...*", "moedas": (70, 140), "xp": (26, 52), "poder": (0, 3), "requer_diploma": "historia_imperial", "nivel_minimo": 4, "descricao_cargo": "Pesquisa e documentação histórica."},
    {"id": "curador_patrimonio", "nome": "Curador de Patrimônio", "emoji": "🏺", "area": "Patrimônio", "narrativa": "*Cuidando e exibindo artefatos históricos e culturais do Império...*", "moedas": (75, 150), "xp": (24, 48), "poder": (0, 3), "requer_diploma": "historia_imperial", "nivel_minimo": 4, "descricao_cargo": "Curadoria de patrimônio cultural."},
    {"id": "pedagogo_imperial", "nome": "Pedagogo Imperial", "emoji": "🎓", "area": "Educação", "narrativa": "*Desenvolvendo métodos educacionais e currículos para a Academia...*", "moedas": (80, 160), "xp": (30, 60), "poder": (0, 4), "requer_diploma": "educacao_pedagogia", "nivel_minimo": 5, "descricao_cargo": "Pedagogia e desenvolvimento educacional."},
    {"id": "coordenador_curricular", "nome": "Coordenador Curricular", "emoji": "📚", "area": "Educação", "narrativa": "*Organizando e atualizando os currículos das disciplinas acadêmicas...*", "moedas": (70, 140), "xp": (26, 52), "poder": (0, 3), "requer_diploma": "educacao_pedagogia", "nivel_minimo": 4, "descricao_cargo": "Coordenação curricular e educacional."},
    {"id": "treinador_professores", "nome": "Treinador de Professores", "emoji": "👨‍🏫", "area": "Educação", "narrativa": "*Capacitando novos professores nas metodologias da Academia...*", "moedas": (75, 150), "xp": (28, 56), "poder": (0, 3), "requer_diploma": "educacao_pedagogia", "nivel_minimo": 4, "descricao_cargo": "Treinamento docente e metodologia."},
    {"id": "treinador_imperial", "nome": "Treinador Imperial", "emoji": "⚽", "area": "Esportes", "narrativa": "*Treinando atletas e equipes para competições imperiais...*", "moedas": (70, 140), "xp": (28, 56), "poder": (2, 6), "requer_diploma": "esportes_educacao_fisica", "nivel_minimo": 4, "descricao_cargo": "Treinamento esportivo e condicionamento físico."},
    {"id": "instrutor_fisico", "nome": "Instrutor Físico", "emoji": "💪", "area": "Fitness", "narrativa": "*Guiando cidadãos em programas de fitness e saúde...*", "moedas": (55, 110), "xp": (22, 44), "poder": (1, 4), "requer_diploma": "esportes_educacao_fisica", "nivel_minimo": 2, "descricao_cargo": "Instrução física e programas de fitness."},
    {"id": "organizador_esportes", "nome": "Organizador de Eventos Esportivos", "emoji": "🏆", "area": "Esportes", "narrativa": "*Organizando torneios e competições esportivas imperiais...*", "moedas": (65, 130), "xp": (24, 48), "poder": (0, 3), "requer_diploma": "esportes_educacao_fisica", "nivel_minimo": 3, "descricao_cargo": "Organização de eventos esportivos."},
    {"id": "botanico_imperial", "nome": "Botânico Imperial", "emoji": "🌿", "area": "Botânica", "narrativa": "*Cultivando e estudando plantas raras nos jardins imperiais...*", "moedas": (65, 130), "xp": (26, 52), "poder": (0, 3), "requer_diploma": "botanica_jardinagem", "nivel_minimo": 4, "descricao_cargo": "Botânica e cultivo de plantas."},
    {"id": "jardineiro_chefe", "nome": "Jardineiro-Chefe", "emoji": "🌻", "area": "Jardinagem", "narrativa": "*Supervisionando a manutenção dos jardins e paisagens imperiais...*", "moedas": (55, 110), "xp": (22, 44), "poder": (0, 3), "requer_diploma": "botanica_jardinagem", "nivel_minimo": 3, "descricao_cargo": "Jardinagem e paisagismo."},
    {"id": "paisagista", "nome": "Paisagista Imperial", "emoji": "🏞️", "area": "Paisagismo", "narrativa": "*Projetando paisagens e jardins para embelezar o Império...*", "moedas": (70, 140), "xp": (24, 48), "poder": (0, 3), "requer_diploma": "botanica_jardinagem", "nivel_minimo": 4, "descricao_cargo": "Projetos paisagísticos e design de jardins."},
    {"id": "astronomo_imperial", "nome": "Astrônomo Imperial", "emoji": "🔭", "area": "Astronomia", "narrativa": "*Observando os céus e conduzindo pesquisas astronômicas...*", "moedas": (90, 180), "xp": (30, 60), "poder": (0, 4), "requer_diploma": "astronomia_cosmologia", "nivel_minimo": 6, "descricao_cargo": "Astronomia e operação de observatórios."},
    {"id": "astrofisico", "nome": "Astrofísico Imperial", "emoji": "✨", "area": "Astrofísica", "narrativa": "*Estudando os fenômenos cósmicos e leis do universo...*", "moedas": (100, 195), "xp": (32, 64), "poder": (0, 5), "requer_diploma": "astronomia_cosmologia", "nivel_minimo": 8, "descricao_cargo": "Astrofísica e pesquisa cósmica."},
    {"id": "navegador_celestial", "nome": "Navegador Celestial", "emoji": "⭐", "area": "Navegação", "narrativa": "*Navegando pelas estrelas para guiar frotas imperiais...*", "moedas": (80, 160), "xp": (28, 56), "poder": (0, 4), "requer_diploma": "astronomia_cosmologia", "nivel_minimo": 5, "descricao_cargo": "Navegação celestial e orientação estelar."},
    {"id": "quimico_imperial", "nome": "Químico Imperial", "emoji": "⚗️", "area": "Química", "narrativa": "*Conduzindo experimentos químicos e desenvolvendo novos compostos...*", "moedas": (85, 170), "xp": (28, 56), "poder": (0, 4), "requer_diploma": "quimica_alquimia", "nivel_minimo": 5, "descricao_cargo": "Química e análise laboratorial."},
    {"id": "analista_laboratorial", "nome": "Analista Laboratorial", "emoji": "🔬", "area": "Laboratório", "narrativa": "*Analisando amostras e substâncias em laboratório imperial...*", "moedas": (70, 140), "xp": (24, 48), "poder": (0, 3), "requer_diploma": "quimica_alquimia", "nivel_minimo": 4, "descricao_cargo": "Análise laboratorial e química."},
    {"id": "fisico_imperial", "nome": "Físico Imperial", "emoji": "⚡", "area": "Física", "narrativa": "*Estudando as leis fundamentais da física e aplicando-as ao imperio...*", "moedas": (95, 185), "xp": (32, 64), "poder": (0, 5), "requer_diploma": "fisica_engenharia", "nivel_minimo": 7, "descricao_cargo": "Física teórica e aplicada."},
    {"id": "engenheiro_aplicado", "nome": "Engenheiro Aplicado", "emoji": "⚙️", "area": "Engenharia", "narrativa": "*Aplicando princípios físicos para resolver problemas de engenharia...*", "moedas": (85, 170), "xp": (28, 56), "poder": (0, 4), "requer_diploma": "fisica_engenharia", "nivel_minimo": 5, "descricao_cargo": "Engenharia aplicada e soluções técnicas."},
    {"id": "pesquisador_fisico", "nome": "Pesquisador Físico", "emoji": "🔬", "area": "Pesquisa", "narrativa": "*Conduzindo pesquisas de ponta em física e engenharia...*", "moedas": (105, 205), "xp": (34, 68), "poder": (0, 5), "requer_diploma": "fisica_engenharia", "nivel_minimo": 8, "descricao_cargo": "Pesquisa em física e engenharia avançada."},
])


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
        lista = sorted(
            lista,
            key=lambda e: (
                (not e.get("requer_diploma") or _tem_diploma(user_data, e.get("requer_diploma"))),
                user_data.get("nivel", 1) >= e.get("nivel_minimo", 1),
                e.get("nivel_minimo", 1),
            ),
            reverse=True,
        )
        self.lista = lista
        self.pagina = 0
        self.por_pagina = 25
        self._montar_pagina()

    @property
    def total_paginas(self) -> int:
        return max(1, (len(self.lista) + self.por_pagina - 1) // self.por_pagina)

    def _montar_pagina(self):
        self.clear_items()
        inicio = self.pagina * self.por_pagina
        self.add_item(EmpregoSelect(self.user_id, self.lista[inicio:inicio + self.por_pagina], self.tipo, self.user_data))
        if self.total_paginas > 1:
            anterior = discord.ui.Button(label="Anterior", emoji="◀️", style=discord.ButtonStyle.secondary, disabled=self.pagina == 0)
            proxima = discord.ui.Button(label="Próxima", emoji="▶️", style=discord.ButtonStyle.primary, disabled=self.pagina >= self.total_paginas - 1)
            indicador = discord.ui.Button(label=f"Página {self.pagina + 1}/{self.total_paginas}", style=discord.ButtonStyle.secondary, disabled=True)
            anterior.callback = self._anterior
            proxima.callback = self._proxima
            self.add_item(anterior)
            self.add_item(indicador)
            self.add_item(proxima)

    async def _mudar(self, interaction: discord.Interaction, deslocamento: int):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este menu não é seu.", ephemeral=True)
            return
        self.pagina = max(0, min(self.total_paginas - 1, self.pagina + deslocamento))
        self._montar_pagina()
        await interaction.response.edit_message(view=self)

    async def _anterior(self, interaction: discord.Interaction):
        await self._mudar(interaction, -1)

    async def _proxima(self, interaction: discord.Interaction):
        await self._mudar(interaction, 1)


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
        cargo_msg = None
        if self.tipo == "legal":
            cargo_msg = await _sincronizar_profissao(interaction.guild, interaction.user, emprego, user)
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
        if cargo_msg:
            embed.add_field(name="💼 Profissão ativa", value=cargo_msg, inline=False)
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

    async def handle_regras(self, message):
        linhas = "\n".join(f"**{indice}.** {regra}" for indice, regra in enumerate(REGRAS_TRABALHO, 1))
        embed = discord.Embed(
            title="📜 Regras de Trabalho do Império",
            description=(
                f"{linhas}\n\n{SEP}\n"
                "**Comandos úteis**\n"
                "`Tenshi, carreiras` — catálogo e requisitos\n"
                "`Tenshi, emprego legal [id]` — exercer profissão\n"
                "`Tenshi, perfil` — conferir a profissão ativa"
            ),
            color=0x2C3E50,
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
                nomes.append(f"{icon} `{e['id']}` - {e['emoji']} {e['nome']} (Nv.{e['nivel_minimo']}+)")
            dipl_str = "✅ Você possui este diploma" if tem_dipl else f"🔒 `Tenshi, matricular {mat_key}`"
            linhas = nomes[:9]
            if len(nomes) > 9:
                linhas.append(f"... +{len(nomes) - 9} cargos neste diploma")
            valor = dipl_str + "\n" + "\n".join(linhas)
            embed.add_field(
                name=f"{m.get('emoji','📚')} {m.get('nome', mat_key)} — ~{m.get('tempo_estudo_h',12)}h de estudo",
                value=valor[:1000],
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

    async def _executar_emprego_direto(self, message, tipo: str, emprego_id: str):
        lista = EMPREGOS_LEGAIS if tipo == "legal" else EMPREGOS_ILEGAIS
        emprego_id = emprego_id.lower().replace("-", "_")
        emprego = next((e for e in lista if e["id"] == emprego_id), None)
        if not emprego:
            await message.channel.send(embed=embed_imperial(
                "Cargo nao encontrado",
                f"`{emprego_id}` nao existe nesta categoria. Use `Tenshi, carreiras` para ver os IDs.",
                0x6B0000,
            ))
            return

        user = get_user(message.author.id)
        requer = emprego.get("requer_diploma")
        if requer and not _tem_diploma(user, requer):
            await message.channel.send(embed=embed_imperial(
                "Formacao necessaria",
                f"**{emprego['emoji']} {emprego['nome']}** exige diploma.\n\n{_info_curso(requer)}",
                0x2C3E50,
            ))
            return

        nivel_min = emprego.get("nivel_minimo", 1)
        if user.get("nivel", 1) < nivel_min:
            await message.channel.send(embed=embed_imperial(
                "Nivel insuficiente",
                f"**{emprego['nome']}** exige nivel **{nivel_min}+**. Seu nivel atual: **{user.get('nivel', 1)}**.",
                0x6B0000,
            ))
            return

        agora = datetime.utcnow()
        if user.get("ultimo_trabalho"):
            ultimo = datetime.fromisoformat(user["ultimo_trabalho"])
            if agora - ultimo < timedelta(seconds=COOLDOWN_TRABALHO):
                restante = timedelta(seconds=COOLDOWN_TRABALHO) - (agora - ultimo)
                mins = int(restante.total_seconds() // 60)
                segs = int(restante.total_seconds() % 60)
                await message.channel.send(embed=embed_imperial(
                    "Em descanso",
                    f"Proximo trabalho em: **{mins}m {segs}s**",
                    0x2B0A3D,
                ))
                return

        moedas = random.randint(*emprego["moedas"])
        xp = random.randint(*emprego["xp"])
        poder = random.randint(*emprego["poder"])

        if tipo == "ilegal":
            risco = emprego.get("risco", 0.25)
            if random.random() < risco:
                multa = int(moedas * 0.5)
                user["moedas"] = max(0, user.get("moedas", 0) - multa)
                user["ultimo_trabalho"] = agora.isoformat()
                save_user(message.author.id, user)
                await message.channel.send(embed=discord.Embed(
                    title="INTERCEPTADO!",
                    description=f"{emprego['narrativa']}\n\nMulta aplicada: **{multa}** moedas.",
                    color=0x8B0000,
                ).set_footer(text=RODAPE_IMPERIAL))
                return

        user["moedas"] = user.get("moedas", 0) + moedas
        user["xp"] = user.get("xp", 0) + xp
        user["poder"] = user.get("poder", 100) + poder
        user["ultimo_trabalho"] = agora.isoformat()
        nivel, _ = calcular_nivel(user["xp"])
        user["nivel"] = nivel
        cargo_msg = None
        if tipo == "legal":
            cargo_msg = await _sincronizar_profissao(message.guild, message.author, emprego, user)
        save_user(message.author.id, user)

        embed = discord.Embed(
            title=f"{emprego['emoji']} {emprego['nome'].upper()}",
            description=f"{emprego['narrativa']}\n\n{SEP}",
            color=0x006400 if tipo == "legal" else 0x1C1C1C,
        )
        embed.add_field(name="Ganho", value=f"**+{moedas}** moedas", inline=True)
        embed.add_field(name="XP", value=f"**+{xp}**", inline=True)
        if poder > 0:
            embed.add_field(name="Poder", value=f"**+{poder}**", inline=True)
        embed.add_field(name="Area", value=emprego["area"], inline=True)
        if requer:
            m = MATERIAS_INFO.get(requer, {})
            embed.add_field(name="Diploma usado", value=m.get("nome", requer), inline=True)
        if cargo_msg:
            embed.add_field(name="Profissão ativa", value=cargo_msg, inline=False)
        embed.set_footer(text=f"Proximo trabalho em 45 minutos  •  {RODAPE_IMPERIAL}")
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

        job_id = None
        if args:
            primeiro = args[0].lower()
            categorias = ("legal", "legais", "trabalho", "honesto", "ilegal", "ilegais", "crime", "mafia", "negro")
            if primeiro in categorias:
                if len(args) > 1:
                    job_id = args[1]
            else:
                job_id = args[0]
        if job_id:
            await self._executar_emprego_direto(message, tipo, job_id)
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
