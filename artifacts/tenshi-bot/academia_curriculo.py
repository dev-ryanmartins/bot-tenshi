"""
Curriculo oficial da Academia Imperial Tenshi.

Baseado no PDF "Academia_Imperial_Tenshi_Curriculo_RPG.pdf".
Este arquivo e a fonte unica para cursos, diplomas, competencias e
desbloqueios profissionais do sistema escolar.
"""
from __future__ import annotations

from datetime import datetime


ESTILO_CARGO = "” ͎ᵎ  ⊰ {emoji}  {nome}"


CURRICULO_ACADEMIA: dict[str, dict] = {
    "governo_imperial": {
        "nome": "Governo Imperial",
        "emoji": "👑",
        "faculdade": "Faculdade Imperial de Governo",
        "cargo_destino": "Conselheiro da Coroa",
        "tempo_estudo_h": 18,
        "competencias": [
            "lideranca imperial",
            "administracao publica",
            "governanca",
            "gestao de crises",
            "formacao de imperadores",
        ],
        "permissoes_rpg": [
            "auxiliar decretos administrativos",
            "participar de conselhos imperiais",
            "organizar planos de governo e resposta a crises",
        ],
        "empregos": ["ministro_imperial", "gestor_crises", "conselheiro_coroa"],
        "prompt": (
            "Voce e Professor da Faculdade Imperial de Governo. Ensine Historia dos Grandes Imperios, "
            "Filosofia da Lideranca, Etica Imperial, Administracao Publica, Governanca, Gestao de Crises, "
            "Formacao de Imperadores e Psicologia da Lideranca. Avalie postura, prudencia e capacidade de comando."
        ),
    },
    "direito_imperial": {
        "nome": "Direito Imperial",
        "emoji": "⚖️",
        "faculdade": "Faculdade Imperial de Governo",
        "cargo_destino": "Magistrado",
        "tempo_estudo_h": 18,
        "competencias": [
            "direito constitucional",
            "direito administrativo",
            "direito empresarial",
            "direito internacional",
            "direito diplomatico e sucessorio",
        ],
        "permissoes_rpg": [
            "emitir parecer juridico em RP",
            "atuar como advogado, magistrado ou chanceler juridico",
            "interpretar o Codigo Imperial Tenshi",
        ],
        "empregos": ["advogado", "juiz", "chanceler_juridico", "consultor_legal"],
        "prompt": (
            "Voce e Professor Catedratico de Direito Imperial. Ensine o Codigo Imperial, hermeneutica juridica, "
            "processo administrativo, sucessao, diplomacia juridica e jurisprudencia do Trono. Seja formal e tecnico."
        ),
    },
    "tenshi_enterprise": {
        "nome": "Tenshi Enterprise",
        "emoji": "💼",
        "faculdade": "Faculdade Tenshi Enterprise",
        "cargo_destino": "Estrategista Corporativo",
        "tempo_estudo_h": 16,
        "competencias": [
            "administracao",
            "economia e financas",
            "empreendedorismo",
            "compliance e ESG",
            "bolsa de valores, venture capital e fusoes",
        ],
        "permissoes_rpg": [
            "gerir empresas e patrimonio",
            "auditar contratos e investimentos",
            "desenhar estrategias corporativas",
        ],
        "empregos": ["diretor_enterprise", "analista_investimentos", "gestor_patrimonial", "diretor_compliance"],
        "prompt": (
            "Voce e Professor da Tenshi Enterprise. Ensine administracao, economia, financas, mercado financeiro, "
            "bolsa de valores, venture capital, gestao patrimonial, fusoes e marketing estrategico."
        ),
    },
    "tecnologia_ia": {
        "nome": "Tecnologia, IA e Sistemas",
        "emoji": "🤖",
        "faculdade": "Faculdade de Tecnologia",
        "cargo_destino": "Engenheiro de IA Imperial",
        "tempo_estudo_h": 20,
        "competencias": [
            "ciencia da computacao",
            "inteligencia artificial e machine learning",
            "banco de dados e cloud",
            "desenvolvimento web e mobile",
            "automacao de sistemas imperiais",
        ],
        "permissoes_rpg": [
            "criar sistemas e automacoes narrativas",
            "atuar como engenheiro de IA, dados ou cloud",
            "apoiar auditorias tecnologicas",
        ],
        "empregos": ["engenheiro_ia", "arquiteto_cloud", "analista_dados", "dev_imperial"],
        "prompt": (
            "Voce e Professor de Tecnologia Imperial. Ensine computacao, IA, machine learning, dados, cloud, "
            "desenvolvimento web/mobile e automacao. Avalie raciocinio tecnico e seguranca operacional."
        ),
    },
    "seguranca_digital": {
        "nome": "Seguranca Digital e Criptografia",
        "emoji": "🛡️",
        "faculdade": "Faculdade de Tecnologia",
        "cargo_destino": "Defensor Cibernetico",
        "tempo_estudo_h": 18,
        "competencias": [
            "seguranca digital",
            "criptografia",
            "defesa cibernetica",
            "analise de incidentes",
            "protecao de dados",
        ],
        "permissoes_rpg": [
            "auditar riscos digitais",
            "defender infraestrutura do servidor",
            "atuar em investigacoes ciberneticas de RP",
        ],
        "empregos": ["defensor_cibernetico", "criptografo", "analista_osint"],
        "prompt": (
            "Voce e Professor de Seguranca Digital da Coroa. Ensine criptografia, defesa cibernetica, "
            "gestao de incidentes e protecao de dados. Nao ensine invasao real; mantenha tudo no RPG."
        ),
    },
    "engenharia_imperial": {
        "nome": "Engenharia Imperial",
        "emoji": "🏗️",
        "faculdade": "Faculdade de Tecnologia",
        "cargo_destino": "Engenheiro Imperial",
        "tempo_estudo_h": 18,
        "competencias": [
            "engenharia civil",
            "engenharia mecanica",
            "engenharia eletrica",
            "engenharia aeroespacial",
            "engenharia biomedica",
        ],
        "permissoes_rpg": [
            "planejar infraestrutura imperial",
            "supervisionar obras, transporte e energia",
            "apoiar projetos medicos e tecnologicos",
        ],
        "empregos": ["engenheiro", "arquiteto", "engenheiro_aeroespacial", "engenheiro_biomedico"],
        "prompt": (
            "Voce e Engenheiro-Chefe da Academia. Ensine engenharia civil, mecanica, eletrica, aeroespacial, "
            "biomedica, infraestrutura, logistica e manutencao de sistemas imperiais."
        ),
    },
    "militar_imperial": {
        "nome": "Estrategia Militar Imperial",
        "emoji": "⚔️",
        "faculdade": "Faculdade Militar Imperial",
        "cargo_destino": "Oficial da Guarda Imperial",
        "tempo_estudo_h": 16,
        "competencias": [
            "estrategia militar",
            "historia militar",
            "defesa pessoal",
            "operacoes especiais",
            "sobrevivencia e protecao executiva",
        ],
        "permissoes_rpg": [
            "comandar patrulhas de RP",
            "organizar escoltas e defesa cerimonial",
            "atuar em operacoes militares narrativas",
        ],
        "empregos": ["guarda", "oficial_guarda", "protector_executivo", "instrutor_militar"],
        "prompt": (
            "Voce e Instrutor da Faculdade Militar Imperial. Ensine estrategia, historia militar, defesa pessoal, "
            "operacoes especiais, sobrevivencia, protecao executiva e cerimonial militar."
        ),
    },
    "inteligencia_imperial": {
        "nome": "Inteligencia e Contrainteligencia",
        "emoji": "🕵️",
        "faculdade": "Faculdade Militar Imperial",
        "cargo_destino": "Analista de Inteligencia",
        "tempo_estudo_h": 18,
        "competencias": [
            "inteligencia",
            "contrainteligencia",
            "analise de risco",
            "protecao de informacoes",
            "investigacao estrategica",
        ],
        "permissoes_rpg": [
            "produzir relatorios de inteligencia no RP",
            "avaliar riscos de faccoes e crises",
            "atuar como analista imperial",
        ],
        "empregos": ["analista_inteligencia", "contrainteligencia", "investigador_estrategico"],
        "prompt": (
            "Voce e Professor de Inteligencia Imperial. Ensine analise, contrainteligencia, protecao de informacoes "
            "e investigacao estrategica no contexto do RPG, sem instrucoes perigosas do mundo real."
        ),
    },
    "diplomacia": {
        "nome": "Diplomacia e Protocolo",
        "emoji": "🤝",
        "faculdade": "Faculdade Diplomatica",
        "cargo_destino": "Diplomata Imperial",
        "tempo_estudo_h": 16,
        "competencias": [
            "relacoes internacionais",
            "protocolo e cerimonial",
            "mediacao de conflitos",
            "negociacao internacional",
            "tratados e etiqueta diplomaticos",
        ],
        "permissoes_rpg": [
            "negociar tratados em RP",
            "mediar conflitos entre membros ou faccoes",
            "representar a Casa em cerimonias diplomaticas",
        ],
        "empregos": ["diplomata", "chanceler", "mediador_imperial", "negociador_internacional"],
        "prompt": (
            "Voce e Chanceler Docente da Faculdade Diplomatica. Ensine relacoes internacionais, protocolo, "
            "cerimonial, mediacao de conflitos e negociacao. Priorize elegancia, prudencia e clareza."
        ),
    },
    "linguas_imperiais": {
        "nome": "Linguas Imperiais",
        "emoji": "📚",
        "faculdade": "Faculdade de Linguas",
        "cargo_destino": "Interprete Diplomatico",
        "tempo_estudo_h": 14,
        "competencias": [
            "portugues",
            "italiano",
            "ingles",
            "latim",
            "frances, espanhol, alemao, grego, hebraico, arabe, japones, mandarim e russo",
        ],
        "permissoes_rpg": [
            "atuar como tradutor imperial",
            "apoiar documentos diplomaticos e cerimoniais",
            "dar aulas de lingua no RP",
        ],
        "empregos": ["tradutor_imperial", "interprete_diplomatico", "professor_linguas"],
        "prompt": (
            "Voce e Professor da Faculdade de Linguas. Ensine portugues, italiano, ingles, latim e linguas optativas. "
            "Avalie clareza, traducao, etiqueta linguistica e uso cerimonial."
        ),
    },
    "medicina_ciencias": {
        "nome": "Medicina e Ciencias",
        "emoji": "⚕️",
        "faculdade": "Faculdades Complementares",
        "cargo_destino": "Medico Imperial",
        "tempo_estudo_h": 18,
        "competencias": [
            "medicina",
            "ciencias naturais",
            "diagnostico e triagem",
            "pesquisa cientifica",
            "biomedicina",
        ],
        "permissoes_rpg": [
            "atuar em hospital e socorro de RP",
            "emitir laudos narrativos",
            "conduzir pesquisa cientifica imperial",
        ],
        "empregos": ["medico", "pesquisador", "biomedico", "gerente_hospital"],
        "prompt": (
            "Voce e Professor de Medicina e Ciencias. Ensine triagem, diagnostico narrativo, biomedicina, "
            "pesquisa e etica medica do RPG. Nao substitua orientacao medica real."
        ),
    },
    "artes_etiqueta": {
        "nome": "Artes e Etiqueta Imperial",
        "emoji": "🎭",
        "faculdade": "Faculdades Complementares",
        "cargo_destino": "Mestre de Etiqueta",
        "tempo_estudo_h": 12,
        "competencias": [
            "artes",
            "oratoria",
            "etiqueta imperial",
            "protocolo de salao",
            "comunicacao cerimonial",
        ],
        "permissoes_rpg": [
            "organizar eventos sociais e apresentacoes",
            "corrigir postura cerimonial",
            "atuar como curador de artes",
        ],
        "empregos": ["mestre_etiqueta", "curador_artes", "orador_cerimonial"],
        "prompt": (
            "Voce e Mestre de Artes e Etiqueta Imperial. Ensine artes, oratoria, postura, protocolo de salao "
            "e comunicacao cerimonial."
        ),
    },
    "familia_imperial": {
        "nome": "Familia Imperial e Genealogia",
        "emoji": "📜",
        "faculdade": "Faculdades Complementares",
        "cargo_destino": "Arquivista Genealogico",
        "tempo_estudo_h": 14,
        "competencias": [
            "historia da dinastia",
            "genealogia",
            "administracao da coroa",
            "formacao da familia imperial",
            "memoria historica",
        ],
        "permissoes_rpg": [
            "registrar linhagens e titulos",
            "auxiliar sucessoes e cerimonias familiares",
            "guardar memoria historica da Casa",
        ],
        "empregos": ["genealogista", "arquivista_imperial", "administrador_coroa"],
        "prompt": (
            "Voce e Arquivista-Mor da Familia Imperial. Ensine historia da dinastia, genealogia, administracao "
            "da coroa, memoria historica e sucessao."
        ),
    },
    "mestres_cerimoniais": {
        "nome": "Mestres Cerimoniais",
        "emoji": "🕯️",
        "faculdade": "Academias Especiais",
        "cargo_destino": "Ritualista de Tenshi",
        "tempo_estudo_h": 16,
        "competencias": [
            "casamento imperial",
            "coroacao",
            "protocolo solene",
            "juramentos",
            "organizacao de ritos",
        ],
        "permissoes_rpg": [
            "organizar casamentos e coroacoes de RP celebrados pela Tenshi IA",
            "preparar juramentos e ritos solenes",
            "atuar como Ritualista e mestre de cerimonias sem substituir a Tenshi IA",
        ],
        "empregos": ["mestre_cerimonial", "organizador_coroacoes", "oficial_matrimonial"],
        "prompt": (
            "Voce e Mestre Cerimonial da Academia Especial. Ensine casamento imperial, coroacao, juramentos, "
            "ritos solenes e protocolo. Use apenas o essencial historico quando for casamento."
        ),
    },
    "herdeiros_coroa": {
        "nome": "Programa dos Herdeiros da Coroa",
        "emoji": "🏛️",
        "faculdade": "Programa Obrigatorio dos Herdeiros",
        "cargo_destino": "Regente em Treinamento",
        "tempo_estudo_h": 24,
        "competencias": [
            "lideranca",
            "historia da dinastia",
            "direito constitucional",
            "administracao da coroa",
            "diplomacia, economia, tecnologia e oratoria",
        ],
        "permissoes_rpg": [
            "preparacao para sucessao e regencia",
            "participar de ritos da Coroa quando autorizado",
            "liderar projetos de Estado supervisionados",
        ],
        "empregos": ["regente_treinamento", "assessor_herdeiro", "guardiao_sucessao"],
        "prompt": (
            "Voce e Tutor dos Herdeiros da Coroa. Ensine lideranca, historia da dinastia, direito constitucional, "
            "administracao da coroa, diplomacia, economia, tecnologia, oratoria, religioes, artes e gestao de crises."
        ),
    },
    "jornalismo_comunicacao": {
        "nome": "Jornalismo e Comunicação Imperial",
        "emoji": "📰",
        "faculdade": "Faculdade de Comunicação",
        "cargo_destino": "Jornalista Imperial",
        "tempo_estudo_h": 14,
        "competencias": ["apuração", "entrevista", "redação", "checagem de fatos", "comunicação pública"],
        "permissoes_rpg": [
            "produzir reportagens e boletins de RP",
            "entrevistar autoridades e cidadãos",
            "atuar na Gazeta Imperial",
        ],
        "empregos": ["jornalista_imperial", "editor_gazeta"],
        "prompt": (
            "Você é Professor de Jornalismo Imperial. Ensine apuração, entrevista, redação, ética, "
            "checagem de fatos e comunicação pública. Diferencie notícia, opinião e propaganda."
        ),
    },
    "economia_financas": {
        "nome": "Economia e Finanças Imperiais",
        "emoji": "📈",
        "faculdade": "Faculdade Tenshi Enterprise",
        "cargo_destino": "Economista Imperial",
        "tempo_estudo_h": 18,
        "competencias": ["macroeconomia", "orçamento", "política monetária", "tributação", "gestão do tesouro"],
        "permissoes_rpg": [
            "analisar inflação e atividade econômica no RP",
            "preparar orçamento e prestação de contas",
            "atuar no Tesouro e no Banco Imperial",
        ],
        "empregos": ["economista_imperial", "tesoureiro_real"],
        "prompt": (
            "Você é Professor de Economia Imperial. Ensine orçamento, inflação, moeda, impostos, "
            "tesouro e análise econômica aplicada ao universo de Tenshi."
        ),
    },
    "gestao_publica": {
        "nome": "Gestão Pública e Urbanismo",
        "emoji": "🏙️",
        "faculdade": "Faculdade Imperial de Governo",
        "cargo_destino": "Gestor Público Imperial",
        "tempo_estudo_h": 16,
        "competencias": ["serviços públicos", "urbanismo", "planejamento", "ouvidoria", "transparência"],
        "permissoes_rpg": [
            "planejar serviços e espaços públicos",
            "organizar consultas e ouvidorias",
            "acompanhar projetos urbanos de RP",
        ],
        "empregos": ["urbanista_imperial", "ouvidor_imperial"],
        "prompt": (
            "Você é Professor de Gestão Pública. Ensine planejamento urbano, serviços públicos, indicadores, "
            "ouvidoria, transparência e avaliação de políticas do Império."
        ),
    },
    "psicologia_estrategica": {
        "nome": "Psicologia e Mediação Estratégica",
        "emoji": "🧠",
        "faculdade": "Faculdades Complementares",
        "cargo_destino": "Psicólogo Imperial",
        "tempo_estudo_h": 18,
        "competencias": ["escuta ativa", "mediação", "psicologia social", "ética", "gestão de conflitos"],
        "permissoes_rpg": [
            "mediar conflitos narrativos",
            "oferecer acolhimento estritamente dentro do RP",
            "atuar como conselheiro institucional",
        ],
        "empregos": ["psicologo_imperial", "mediador_comunitario"],
        "prompt": (
            "Você é Professor de Psicologia e Mediação no contexto de RPG. Ensine escuta, ética, limites e "
            "resolução de conflitos sem diagnosticar pessoas reais nem substituir profissionais."
        ),
    },
    "ecologia_agricultura": {
        "nome": "Ecologia e Agricultura Imperial",
        "emoji": "🌱",
        "faculdade": "Faculdade de Ciências Naturais",
        "cargo_destino": "Agrônomo Imperial",
        "tempo_estudo_h": 16,
        "competencias": ["agronomia", "ecologia", "recursos hídricos", "manejo", "segurança alimentar"],
        "permissoes_rpg": [
            "planejar colheitas e abastecimento",
            "fiscalizar impactos ambientais no RP",
            "propor recuperação de áreas naturais",
        ],
        "empregos": ["agronomo_imperial", "fiscal_ambiental"],
        "prompt": (
            "Você é Professor de Ecologia e Agricultura Imperial. Ensine solo, água, produção, biodiversidade, "
            "manejo sustentável e segurança alimentar no universo de Tenshi."
        ),
    },
    "gastronomia_hospitalidade": {
        "nome": "Gastronomia e Hospitalidade",
        "emoji": "🍽️",
        "faculdade": "Faculdade de Artes e Ofícios",
        "cargo_destino": "Mestre de Hospitalidade",
        "tempo_estudo_h": 12,
        "competencias": ["gastronomia", "segurança alimentar", "eventos", "hospedagem", "protocolo de recepção"],
        "permissoes_rpg": [
            "organizar banquetes e recepções",
            "administrar hospedagem de visitantes",
            "atuar em cozinhas e eventos imperiais",
        ],
        "empregos": ["chef_real", "gestor_hospedagem"],
        "prompt": (
            "Você é Professor de Gastronomia e Hospitalidade. Ensine planejamento de cardápios, segurança "
            "alimentar, recepção, hospedagem, eventos e protocolo de serviço."
        ),
    },
    "arquitetura_imperial": {
        "nome": "Arquitetura e Design Imperial",
        "emoji": "🏛️",
        "faculdade": "Faculdade de Tecnologia",
        "cargo_destino": "Arquiteto Imperial",
        "tempo_estudo_h": 18,
        "competencias": ["arquitetura", "design de interiores", "urbanismo", "restauração", "planejamento espacial"],
        "permissoes_rpg": [
            "projetar edifícios imperiais",
            "supervisionar restaurações",
            "planejar espaços públicos e privados",
        ],
        "empregos": ["arquiteto_imperial", "designer_interiores", "urbanista"],
        "prompt": (
            "Você é Professor de Arquitetura Imperial. Ensine arquitetura, design, urbanismo, restauração "
            "e planejamento espacial no contexto do Império de Tenshi."
        ),
    },
    "logistica_transportes": {
        "nome": "Logística e Transportes Imperiais",
        "emoji": "🚚",
        "faculdade": "Faculdade Tenshi Enterprise",
        "cargo_destino": "Gestor Logístico Imperial",
        "tempo_estudo_h": 16,
        "competencias": ["logística", "transportes", "cadeia de suprimentos", "gestão de frotas", "armazenagem"],
        "permissoes_rpg": [
            "gerir transportes imperiais",
            "organizar rotas logísticas",
            "administrar armazéns e frotas",
        ],
        "empregos": ["gestor_logistico", "coordenador_transportes", "gerente_armazem"],
        "prompt": (
            "Você é Professor de Logística Imperial. Ensine logística, transportes, cadeia de suprimentos, "
            "gestão de frotas e armazenagem eficiente."
        ),
    },
    "marketing_imperial": {
        "nome": "Marketing e Comunicação Estratégica",
        "emoji": "📢",
        "faculdade": "Faculdade de Comunicação",
        "cargo_destino": "Diretor de Marketing Imperial",
        "tempo_estudo_h": 14,
        "competencias": ["marketing", "branding", "publicidade", "relações públicas", "análise de mercado"],
        "permissoes_rpg": [
            "criar campanhas imperiais",
            "gerir imagem pública",
            "desenvolver estratégias de comunicação",
        ],
        "empregos": ["diretor_marketing", "analista_mercado", "relacoes_publicas"],
        "prompt": (
            "Você é Professor de Marketing Imperial. Ensine marketing, branding, publicidade, relações públicas "
            "e análise de mercado para o Império de Tenshi."
        ),
    },
    "recursos_humanos": {
        "nome": "Gestão de Recursos Humanos",
        "emoji": "👥",
        "faculdade": "Faculdade Tenshi Enterprise",
        "cargo_destino": "Diretor de RH Imperial",
        "tempo_estudo_h": 14,
        "competencias": ["recrutamento", "treinamento", "avaliação de desempenho", "gestão de talentos", "cultura organizacional"],
        "permissoes_rpg": [
            "recrutar para cargos imperiais",
            "gerir treinamentos",
            "avaliar desempenho de funcionários",
        ],
        "empregos": ["diretor_rh", "recrutador", "treinador"],
        "prompt": (
            "Você é Professor de Recursos Humanos. Ensine recrutamento, treinamento, avaliação, "
            "gestão de talentos e cultura organizacional."
        ),
    },
    "financas_corporativas": {
        "nome": "Finanças Corporativas e Investimentos",
        "emoji": "💹",
        "faculdade": "Faculdade Tenshi Enterprise",
        "cargo_destino": "CFO Imperial",
        "tempo_estudo_h": 18,
        "competencias": ["finanças corporativas", "investimentos", "análise financeira", "gestão de riscos", "mergidos e aquisições"],
        "permissoes_rpg": [
            "gerir finanças corporativas",
            "analisar investimentos",
            "supervisionar operações financeiras",
        ],
        "empregos": ["cfo_imperial", "analista_financeiro", "gestor_investimentos"],
        "prompt": (
            "Você é Professor de Finanças Corporativas. Ensine finanças, investimentos, análise financeira, "
            "gestão de riscos e operações de M&A."
        ),
    },
    "ciencias_politicas": {
        "nome": "Ciências Políticas e Relações Governamentais",
        "emoji": "🏛️",
        "faculdade": "Faculdade Imperial de Governo",
        "cargo_destino": "Analista Político Imperial",
        "tempo_estudo_h": 16,
        "competencias": ["ciência política", "relações governamentais", "política pública", "análise legislativa", "lobby ético"],
        "permissoes_rpg": [
            "analisar cenários políticos",
            "assessorar em políticas públicas",
            "representar interesses governamentais",
        ],
        "empregos": ["analista_politico", "assessor_governamental", "consultor_politico"],
        "prompt": (
            "Você é Professor de Ciências Políticas. Ensine ciência política, relações governamentais, "
            "política pública, análise legislativa e lobby ético."
        ),
    },
    "historia_imperial": {
        "nome": "História Imperial e Patrimônio",
        "emoji": "📜",
        "faculdade": "Faculdades Complementares",
        "cargo_destino": "Historiador Imperial",
        "tempo_estudo_h": 14,
        "competencias": ["história imperial", "patrimônio cultural", "arqueologia", "preservação", "memória histórica"],
        "permissoes_rpg": [
            "documentar história imperial",
            "preservar patrimônio cultural",
            "conduzir pesquisas históricas",
        ],
        "empregos": ["historiador_imperial", "arquivista", "curador_patrimonio"],
        "prompt": (
            "Você é Professor de História Imperial. Ensine história do Império, patrimônio cultural, "
            "arqueologia, preservação e memória histórica."
        ),
    },
    "educacao_pedagogia": {
        "nome": "Educação e Pedagogia Imperial",
        "emoji": "🎓",
        "faculdade": "Faculdades Complementares",
        "cargo_destino": "Pedagogo Imperial",
        "tempo_estudo_h": 16,
        "competencias": ["pedagogia", "metodologia de ensino", "psicologia educacional", "currículo", "avaliação educacional"],
        "permissoes_rpg": [
            "desenvolver currículos",
            "treinar professores",
            "criar métodos educacionais",
        ],
        "empregos": ["pedagogo_imperial", "coordenador_curricular", "treinador_professores"],
        "prompt": (
            "Você é Professor de Educação e Pedagogia. Ensine pedagogia, metodologia, psicologia educacional, "
            "currículo e avaliação educacional."
        ),
    },
    "esportes_educacao_fisica": {
        "nome": "Esportes e Educação Física Imperial",
        "emoji": "⚽",
        "faculdade": "Faculdade de Ciências Naturais",
        "cargo_destino": "Treinador Imperial",
        "tempo_estudo_h": 12,
        "competencias": ["educação física", "treinamento esportivo", "fisiologia", "nutrição esportiva", "gestão de equipes"],
        "permissoes_rpg": [
            "treinar atletas imperiais",
            "organizar eventos esportivos",
            "desenvolver programas de fitness",
        ],
        "empregos": ["treinador_imperial", "instrutor_fisico", "organizador_esportes"],
        "prompt": (
            "Você é Professor de Educação Física. Ensine esportes, treinamento, fisiologia, nutrição esportiva "
            "e gestão de equipes atléticas."
        ),
    },
    "botanica_jardinagem": {
        "nome": "Botânica e Jardinagem Imperial",
        "emoji": "🌿",
        "faculdade": "Faculdade de Ciências Naturais",
        "cargo_destino": "Botânico Imperial",
        "tempo_estudo_h": 14,
        "competencias": ["botânica", "jardinagem", "paisagismo", "cultivo de plantas", "conservação de espécies"],
        "permissoes_rpg": [
            "gerir jardins imperiais",
            "cultivar plantas raras",
            "projetar paisagens",
        ],
        "empregos": ["botanico_imperial", "jardineiro_chefe", "paisagista"],
        "prompt": (
            "Você é Professor de Botânica. Ensine botânica, jardinagem, paisagismo, cultivo de plantas "
            "e conservação de espécies no Império."
        ),
    },
    "astronomia_cosmologia": {
        "nome": "Astronomia e Cosmologia Imperial",
        "emoji": "🔭",
        "faculdade": "Faculdade de Ciências Naturais",
        "cargo_destino": "Astrônomo Imperial",
        "tempo_estudo_h": 18,
        "competencias": ["astronomia", "cosmologia", "astrofísica", "navegação celestial", "observatório"],
        "permissoes_rpg": [
            "operar observatórios imperiais",
            "conduzir pesquisas astronômicas",
            "navegar por estrelas",
        ],
        "empregos": ["astronomo_imperial", "astrofisico", "navegador_celestial"],
        "prompt": (
            "Você é Professor de Astronomia. Ensine astronomia, cosmologia, astrofísica, navegação celestial "
            "e operação de observatórios."
        ),
    },
    "quimica_alquimia": {
        "nome": "Química e Alquimia Imperial",
        "emoji": "⚗️",
        "faculdade": "Faculdade de Ciências Naturais",
        "cargo_destino": "Químico Imperial",
        "tempo_estudo_h": 16,
        "competencias": ["química", "alquimia", "laboratório", "análise química", "síntese"],
        "permissoes_rpg": [
            "conduzir experimentos químicos",
            "analisar substâncias",
            "desenvolver novos compostos",
        ],
        "empregos": ["quimico_imperial", "alquimista", "analista_laboratorial"],
        "prompt": (
            "Você é Professor de Química e Alquimia. Ensine química, alquimia, laboratório, análise química "
            "e síntese de compostos no contexto do RPG."
        ),
    },
    "fisica_engenharia": {
        "nome": "Física e Engenharia Aplicada",
        "emoji": "⚡",
        "faculdade": "Faculdade de Tecnologia",
        "cargo_destino": "Físico Imperial",
        "tempo_estudo_h": 18,
        "competencias": ["física", "engenharia aplicada", "mecânica", "termodinâmica", "eletricidade"],
        "permissoes_rpg": [
            "desenvolver tecnologias físicas",
            "analisar sistemas mecânicos",
            "projetar soluções de engenharia",
        ],
        "empregos": ["fisico_imperial", "engenheiro_aplicado", "pesquisador_fisico"],
        "prompt": (
            "Você é Professor de Física e Engenharia. Ensine física, engenharia aplicada, mecânica, "
            "termodinâmica e eletricidade no contexto imperial."
        ),
    },
}


# Diplomas antigos continuam valendo para nao quebrar progresso dos jogadores.
EQUIVALENCIAS_DIPLOMA = {
    "tatica_militar": "militar_imperial",
    "tática_militar": "militar_imperial",
    "historia_lore": "familia_imperial",
    "história_lore": "familia_imperial",
    "ciencias_esotéricas": "medicina_ciencias",
    "ciências_esotéricas": "medicina_ciencias",
    "ciencias_esotericas": "medicina_ciencias",
    "logística_engenharia": "engenharia_imperial",
    "logistica_engenharia": "engenharia_imperial",
}


CURSOS_VISIVEIS = tuple(CURRICULO_ACADEMIA.keys())


def normalizar_materia(materia: str | None) -> str:
    key = str(materia or "").strip().lower()
    return EQUIVALENCIAS_DIPLOMA.get(key, key)


def curso_por_id(materia: str | None) -> dict | None:
    return CURRICULO_ACADEMIA.get(normalizar_materia(materia))


def materias_academicas() -> dict[str, dict]:
    data = {k: dict(v) for k, v in CURRICULO_ACADEMIA.items()}
    for alias, canonico in EQUIVALENCIAS_DIPLOMA.items():
        curso = CURRICULO_ACADEMIA.get(canonico)
        if curso:
            data[alias] = dict(curso, alias_de=canonico)
    return data


def tem_diploma(user: dict, materia: str | None) -> bool:
    alvo = normalizar_materia(materia)
    if not alvo:
        return False
    for diploma in user.get("diplomas", []):
        if normalizar_materia(diploma.get("materia")) == alvo:
            return True
    return False


def competencias_do_curso(materia: str | None) -> list[str]:
    curso = curso_por_id(materia) or {}
    return list(curso.get("competencias", []))


def permissoes_do_curso(materia: str | None) -> list[str]:
    curso = curso_por_id(materia) or {}
    return list(curso.get("permissoes_rpg", []))


def formatar_cargo_diploma(materia: str | None) -> str:
    curso = curso_por_id(materia) or {"nome": str(materia or "Academia"), "emoji": "🎓"}
    return ESTILO_CARGO.format(emoji="🎓", nome=f"Diploma {curso['nome']}")


def diploma_payload(user_id: int, materia: str, nota: float, origem: str = "exame") -> dict:
    canonico = normalizar_materia(materia)
    curso = curso_por_id(canonico) or {}
    return {
        "materia": canonico,
        "nome": curso.get("nome", canonico),
        "faculdade": curso.get("faculdade", "Academia Imperial Tenshi"),
        "nota": round(float(nota), 2),
        "data": datetime.utcnow().isoformat(),
        "hash": f"DIP-{user_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "cargo_diploma": formatar_cargo_diploma(canonico),
        "competencias": competencias_do_curso(canonico),
        "permissoes_rpg": permissoes_do_curso(canonico),
        "origem": origem,
    }


def resumo_curso(materia: str | None) -> str:
    curso = curso_por_id(materia)
    if not curso:
        return "Curso nao encontrado."
    comps = ", ".join(curso.get("competencias", [])[:5])
    perms = "; ".join(curso.get("permissoes_rpg", [])[:3])
    return (
        f"{curso['emoji']} {curso['nome']} ({curso['faculdade']})\n"
        f"Cargo de destino: {curso['cargo_destino']}\n"
        f"Competencias: {comps}\n"
        f"Certificado permite: {perms}"
    )


def curriculo_resumo_prompt() -> str:
    linhas = []
    for key in CURSOS_VISIVEIS:
        curso = CURRICULO_ACADEMIA[key]
        linhas.append(
            f"- {key}: {curso['nome']} / {curso['faculdade']} / "
            f"competencias: {', '.join(curso.get('competencias', [])[:5])}"
        )
    return "Curriculo oficial da Academia Imperial Tenshi:\n" + "\n".join(linhas)
