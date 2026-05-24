"""
Protocolo 25 — Meteorologia Localizada e Espontânea por IA
Clima inédito por local_atual do usuário, modificadores mecânicos.
"""
import discord
import asyncio
import random
from datetime import datetime, timezone
from database import get_user, save_user
from design import (embed_doc, embed_hospital, embed_admin_doc,
                    COR_GERAL, COR_ADMIN, COR_HOSPITAL, rodape_padrao)

# ─── MAPA DE LOCAIS → CLASSES CLIMÁTICAS ─────────────────────────────────────
CLIMA_POR_LOCAL: dict[str, list[dict]] = {
    # Cidadela Branca / Geral
    "cidadela": [
        {"cond": "Névoa Etérea Branca", "desc": "Uma névoa suave de origem arcana envolve as torres da Cidadela. A visibilidade é reduzida a cinquenta metros.", "mod": "+5% resistência mística ao meditar.", "efeito": "resistencia_mistura", "valor": 5},
        {"cond": "Vento Soberano do Norte", "desc": "Rajadas frias e precisas varrem os corredores imperiais. O frio aguça a mente e fortalece a disciplina.", "mod": "+8% de precisão em duelos realizados ao ar livre.", "efeito": "precisao_duelo", "valor": 8},
        {"cond": "Calmaria Imperial", "desc": "Um silêncio absoluto paira sobre a Cidadela. O ar está estático, quase cerimonial.", "mod": "Sem modificadores ativos. Condições nominais.", "efeito": None, "valor": 0},
        {"cond": "Chuva de Prata Fina", "desc": "Gotículas prateadas de éter precipitam sobre a capital. A umidade ativa propriedades latentes em runas e cristais.", "mod": "+12% de eficácia em rituals esotéricos.", "efeito": "eficacia_ritual", "valor": 12},
        {"cond": "Bruma Nobre Dourada", "desc": "Uma névoa de tonalidade áurea, tipicamente associada a manifestações de poder soberano, cobre o pátio da corte.", "mod": "+10% de ganho de experiência em missões realizadas hoje.", "efeito": "xp_bonus", "valor": 10},
        {"cond": "Céu de Opala Imperial", "desc": "O firmamento exibe tons violáceos e cobreados, indicando convergência de correntes místicas superiores.", "mod": "+6% de mana regenerada passivamente por hora.", "efeito": "mana_regen", "valor": 6},
        {"cond": "Tempestade Estática de Éter", "desc": "Descargas de energia etérea percorrem a atmosfera. Equipamentos eletrônicos e mágicos apresentam interferência.", "mod": "-15% de eficácia de habilidades tecnológicas ou digitais.", "efeito": "tech_malus", "valor": -15},
        {"cond": "Granizo de Cristais Arcanos", "desc": "Fragmentos de cristais etéreos caem do céu. A precipitação é visualmente magnífica, porém prejudicial ao deslocamento.", "mod": "-10% de velocidade de viagem por terra. +5% de defesa para usuários em locais fechados.", "efeito": "viagem_malus", "valor": -10},
    ],
    # Hospital
    "hospital": [
        {"cond": "Ar Estéril Regulado", "desc": "Sistemas de purificação etérea mantêm o ar do perímetro hospitalar em estado de assepsia absoluta.", "mod": "+20% de eficácia de todos os procedimentos médicos realizados hoje.", "efeito": "cura_bonus", "valor": 20},
        {"cond": "Névoa de Desinfecção Arcana", "desc": "Névoa azulada de composição alquímica paira nos corredores clínicos, neutralizando agentes patológicos.", "mod": "Tempo de internação reduzido em 10% para novos ingressos.", "efeito": "internacao_reducao", "valor": 10},
        {"cond": "Umidade Clínica Elevada", "desc": "A saturação hídrica do ar está acima do índice padrão. Pacientes com condições respiratórias devem permanecer em leitos.", "mod": "+15% de fadiga ao realizar atividades físicas próximas ao hospital.", "efeito": "fadiga_bonus", "valor": 15},
        {"cond": "Vento Antiséptico de Leste", "desc": "Correntes de ar com propriedades purificantes circulam pelos andares. Risco de contaminação reduzido.", "mod": "-5% de chance de contrair condições negativas por contato.", "efeito": "contaminacao_reducao", "valor": -5},
        {"cond": "Pressão Barométrica Mística Alta", "desc": "A pressão atmosférica elevada aumenta a concentração de éter nos remédios de manipulação.", "mod": "+18% de potência em antídotos e poções curativas elaboradas hoje.", "efeito": "potencia_pocao", "valor": 18},
    ],
    # Escola / Academia
    "escola": [
        {"cond": "Brisa Autumnal de Estudos", "desc": "Uma brisa suave carregada de poeira de pergaminhos antigos circula pelos corredores da Academia.", "mod": "+10% de assimilação acadêmica. Questões de prova ganham dica adicional.", "efeito": "academico_bonus", "valor": 10},
        {"cond": "Vento Cortante de Outono Imperial", "desc": "Rajadas frias varrem o pátio, afastando a preguiça dos estudantes.", "mod": "+7% de velocidade de aprendizado na aula atual.", "efeito": "aprendizado_bonus", "valor": 7},
        {"cond": "Calmaria Estudantil Absoluta", "desc": "O ar está completamente parado sobre a Academia. A concentração dos alunos atinge pico máximo.", "mod": "+15% de precisão nas respostas dos exames aplicados neste momento.", "efeito": "precisao_exame", "valor": 15},
        {"cond": "Névoa Bibliotecária", "desc": "Uma névoa densa de éter escrito sai das estantes da biblioteca, impregnando o ar de conhecimento arcano.", "mod": "+12% de ganho de pontos acadêmicos nas atividades do dia.", "efeito": "pts_academicos", "valor": 12},
        {"cond": "Garoa de Tinta Etérea", "desc": "Uma garoa microscópica carregada de compostos alquímicos — usada na impressão de apostilas — cobre o pátio.", "mod": "Material didático do dia tem qualidade aprimorada. +5% na nota final da redação.", "efeito": "qualidade_apostila", "valor": 5},
        {"cond": "Vento de Sabedoria Meridional", "desc": "Corrente quente e seca proveniente do sul. Associada historicamente às épocas de grandes descobertas científicas.", "mod": "+9% de chance de obter dica extra nas provas orais.", "efeito": "dica_extra", "valor": 9},
    ],
    # Beco / Submundo
    "beco": [
        {"cond": "Chuva de Fuligem Escura", "desc": "Partículas de carbono e resíduos industriais precipitam sobre as vielas do submundo. Visibilidade comprometida.", "mod": "-20% de chance de ser detectado durante operações de crime. +5% de fadiga.", "efeito": "furtividade_bonus", "valor": 20},
        {"cond": "Umidade Abafada das Galerias", "desc": "Vapor quente e pestilento sobe das galerias subterrâneas. O ambiente é opressivo e claustrofóbico.", "mod": "+10% de fadiga ao permanecer no beco por mais de 30 minutos.", "efeito": "fadiga_beco", "valor": 10},
        {"cond": "Névoa Corrosiva Industrial", "desc": "Gases de laboratórios clandestinos vazam para o ar das vielas. Contato prolongado degrada equipamentos.", "mod": "-8% de durabilidade de armas e armaduras usadas neste perímetro.", "efeito": "durabilidade_malus", "valor": -8},
        {"cond": "Vapor das Galerias de Esgoto", "desc": "Emanações tóxicas das galerias de resíduos sobem pelas rachaduras do calçamento. Odor acre e persistente.", "mod": "+15% de chance de contrair envenenamento leve ao permanecer aqui.", "efeito": "veneno_chance", "valor": 15},
        {"cond": "Escuridão Total sem Luar", "desc": "A ausência de luz natural e das lâmpadas públicas sabotadas cria escuridão absoluta no beco.", "mod": "+25% de furtividade para membros da Máfia. -30% de visibilidade para a polícia.", "efeito": "escuridao_total", "valor": 25},
        {"cond": "Chuva Ácida de Subprodutos Alquímicos", "desc": "Precipitação com pH irregular resultante de experimentos clandestinos. Corrói metais e tecidos.", "mod": "-12% de durabilidade de equipamentos de metal. Itens orgânicos preservados.", "efeito": "chuva_acida", "valor": -12},
        {"cond": "Neblina de Mercúrio Mistico", "desc": "Uma névoa prateada e tóxica de origem alquímica cobre o chão do beco. Efeito paralisante leve.", "mod": "+5% de chance de paralisia temporária em alvos de ataque surpresa.", "efeito": "paralisia_chance", "valor": 5},
    ],
    # Parque / Jardim
    "parque": [
        {"cond": "Névoa de Éter Prateada", "desc": "Uma névoa de partículas etéreas dança entre as árvores. A visibilidade é reduzida, mas a concentração mística aumenta.", "mod": "+10% de mana regenerada ao meditar no jardim.", "efeito": "mana_regen", "valor": 10},
        {"cond": "Brisa Floral de Primavera Eterna", "desc": "Pétalas de flores místicas são carregadas pelo vento. A fragrância tem propriedades calmantes.", "mod": "-15% de fadiga para todos os usuários no parque. Cooldown de descanso reduzido.", "efeito": "fadiga_reducao", "valor": -15},
        {"cond": "Chuva Suave sobre os Jardins", "desc": "Uma chuva morna e ritmada rega os jardins imperiais. O solo absorve a água com gratidão arcana.", "mod": "+8% de eficácia de itens curativos consumidos ao ar livre.", "efeito": "curativo_bonus", "valor": 8},
        {"cond": "Sol Nascente de Pedras de Âmbar", "desc": "A luz da manhã atravessa formações de âmbar místico espalhadas pelos canteiros, criando prismas dourados.", "mod": "+12% de ganho de moedas em atividades realizadas no parque.", "efeito": "moedas_bonus", "valor": 12},
        {"cond": "Vento de Folhas Rúnicas", "desc": "Folhas gravadas com runas ancestrais desprendem-se das árvores e circulam no ar. Leitura espontânea de presságios.", "mod": "+15% de chance de evento especial no Tarot sorteado hoje.", "efeito": "tarot_bonus", "valor": 15},
        {"cond": "Orvalho de Cristal Etéreo", "desc": "Gotículas solidificadas de éter cobrem a vegetação ao amanhecer. Brilham com luz própria.", "mod": "+6% de mana ao colher itens vegetais do parque.", "efeito": "coleta_mana", "valor": 6},
    ],
    # Cassino
    "cassino": [
        {"cond": "Ar Viciado de Fortuna", "desc": "A atmosfera do cassino está saturada de éter monetário. O cheiro de moedas antigas impregna o ambiente.", "mod": "+8% de chance de vitória nas apostas realizadas hoje.", "efeito": "aposta_bonus", "valor": 8},
        {"cond": "Tensão Elétrica de Alto Risco", "desc": "Descargas estáticas de energia etérea percorrem o salão. A atmosfera está carregada de adrenalina.", "mod": "+15% de ganho em apostas de alto risco. -20% em apostas conservadoras.", "efeito": "risco_alto", "valor": 15},
        {"cond": "Névoa de Luxo e Perfume Régio", "desc": "Incenso imperial e névoa aromática circulam no salão. O ambiente convida ao prazer e ao risco.", "mod": "+5% de carisma social. Transações no cassino ganham desconto de 5%.", "efeito": "carisma_bonus", "valor": 5},
        {"cond": "Corrente Magnética Monetária", "desc": "Forças magnéticas inexplicáveis concentram energia financeira no centro do salão.", "mod": "+10% nos dividendos de apostas de longo prazo.", "efeito": "dividendo_bonus", "valor": 10},
    ],
    # Laboratório
    "laboratorio": [
        {"cond": "Emanações Alquímicas Voláteis", "desc": "Vapores de reagentes instáveis em síntese ativa pairam sobre as bancadas. Ambiente requer proteção.", "mod": "+18% de chance de obter produto raro na síntese. +12% de chance de explosão.", "efeito": "sintese_risco", "valor": 18},
        {"cond": "Vapor Químico de Alta Densidade", "desc": "Neblina densa de compostos em reação cobre o chão do laboratório. Visibilidade abaixo dos joelhos.", "mod": "+10% de potência de poções sintetizadas. -5% de durabilidade de equipamentos.", "efeito": "pocao_potencia", "valor": 10},
        {"cond": "Névoa de Éter Concentrado", "desc": "Concentração máxima de éter no ar do laboratório. Ideal para rituals de fusão de relíquias.", "mod": "+20% de eficácia na fusão de relíquias rúnicas realizadas hoje.", "efeito": "fusao_bonus", "valor": 20},
        {"cond": "Pressão Negativa de Câmara Selada", "desc": "Sistemas de exaustão mantêm pressão negativa no laboratório. Contaminação externa é impossível.", "mod": "Reagentes instáveis não se degradam hoje. Prazo de síntese suspenso por 24h.", "efeito": "reagente_estavel", "valor": 0},
    ],
    # Garagem
    "garagem": [
        {"cond": "Vapor de Combustível Místico", "desc": "Emanações de combustível de alta octanagem etérea saturam o ar da garagem. Inflamável.", "mod": "+15% de velocidade de viagem em veículos abastecidos hoje.", "efeito": "velocidade_bonus", "valor": 15},
        {"cond": "Chuva Ácida Leve sobre o Pátio", "desc": "Garoa com pH ácido corroe superfícies metálicas expostas. Veículos não cobertos sofrem dano.", "mod": "-10% de durabilidade de veículos estacionados ao ar livre.", "efeito": "durabilidade_veiculo", "valor": -10},
        {"cond": "Neblina de Óleo de Silicone", "desc": "Névoa fina de silicone utilizado na lubrificação de peças paira no ambiente.", "mod": "+12% de eficácia no reparo de veículos realizado hoje.", "efeito": "reparo_bonus", "valor": 12},
        {"cond": "Seca Extrema de Alta Condutividade", "desc": "Ar extremamente seco aumenta a condutividade elétrica. Risco de curto em sistemas eletrônicos.", "mod": "-15% de eficácia de veículos com sistemas eletrônicos. Veículos mecânicos: sem impacto.", "efeito": "eletro_malus", "valor": -15},
    ],
    # Estação de Trem
    "trem": [
        {"cond": "Vapor Ferroviário de Partida", "desc": "Nuvens de vapor branco das locomotivas etéreas cobrem as plataformas. O cheiro de trilhos quentes é inconfundível.", "mod": "+10% de velocidade de viagem de trem. Tempo de percurso reduzido.", "efeito": "trem_velocidade", "valor": 10},
        {"cond": "Neblina de Chegada da Linha Norte", "desc": "Densa neblina de origem mística acompanha a chegada da composição da linha norte.", "mod": "-5% de velocidade. +8% de chance de encontro aleatório durante a viagem.", "efeito": "encontro_viagem", "valor": 8},
        {"cond": "Geada Rúnica nos Trilhos", "desc": "Cristais de gelo etéreo formam-se sobre os trilhos rúnicos durante a madrugada. Risco de atraso.", "mod": "Viagens têm 20% de chance de atraso de 5 minutos adicionais.", "efeito": "atraso_trem", "valor": 20},
        {"cond": "Temporal Ferroviário de Éter", "desc": "Tempestade de alta intensidade sobre a malha ferroviária. Serviço de risco máximo.", "mod": "Trem paralisado por 30 minutos. Deslocamento apenas por garagem (+40% fadiga).", "efeito": "trem_paralisado", "valor": 0},
        {"cond": "Ventania de Calor nas Plataformas", "desc": "Correntes de ar quente sobem das galerias ferroviárias subterrâneas.", "mod": "+5% de fadiga por viagem de trem. Compensado por bebidas quentes da cantina.", "efeito": "fadiga_trem", "valor": 5},
    ],
    # Praça / Praca
    "praca": [
        {"cond": "Brisa Popular de Mercado", "desc": "Vento suave que carrega o aroma das barracas do mercado popular da praça imperial.", "mod": "+5% de desconto em compras realizadas na cafeteria e sorveteria hoje.", "efeito": "desconto_comercio", "valor": 5},
        {"cond": "Calmaria Pública de Hora de Almoço", "desc": "O ar está parado e quente. O movimento de cidadãos na praça atinge o pico diário.", "mod": "+10% de ganho de pontos de carisma social. Ideal para negociações.", "efeito": "carisma_praca", "valor": 10},
        {"cond": "Chuva Fina sobre o Calçamento", "desc": "Uma garoa persistente dispersa os transeuntes. As bancadas são recolhidas para cobertura.", "mod": "-10% de fluxo de cidadãos. Preços sobem 5% por baixa demanda.", "efeito": "fluxo_reducao", "valor": -10},
        {"cond": "Sol Forte de Verão Imperial", "desc": "Calor intenso sobre a praça. Os cidadãos buscam sombra nas arcadas.", "mod": "+15% de fadiga em atividades ao ar livre. -10% de eficácia de treinos externos.", "efeito": "calor_fadiga", "valor": 15},
        {"cond": "Vento Festivo de Celebração", "desc": "Rajadas suaves carregam fragmentos de papel colorido de uma festividade próxima.", "mod": "+12% de ganho de moedas em atividades comerciais. Atmosfera favorável.", "efeito": "festivo_bonus", "valor": 12},
    ],
    # Banco
    "banco": [
        {"cond": "Clima Austero de Alta Precisão", "desc": "O ar dentro do banco está temperado e preciso, como convém a um ambiente de transações de alto valor.", "mod": "Taxa de juros reduzida em 2% para empréstimos solicitados hoje.", "efeito": "juros_reducao", "valor": 2},
        {"cond": "Ar Condicionado Etéreo Máximo", "desc": "Sistemas de controle ambiental arcanos mantêm temperatura perfeita para custódia de valores.", "mod": "+5% de rendimento na conta poupança para depósitos efetuados neste momento.", "efeito": "poupanca_bonus", "valor": 5},
    ],
    # Portaria / Condomínio
    "condominio": [
        {"cond": "Vento Condominial de Limpeza", "desc": "Brisa regular de manutenção circula pelos corredores do condomínio, típica das manhãs organizadas.", "mod": "+5% de satisfação residencial. Taxa de condomínio reduzida em 5% esta semana.", "efeito": "condominio_bonus", "valor": 5},
        {"cond": "Brisa Residencial Noturna", "desc": "Correntes de ar fresco à noite ventilam os apartamentos. A qualidade do sono é superior.", "mod": "-10% de fadiga ao dormir na residência. Bônus de descanso ativado.", "efeito": "descanso_bonus", "valor": 10},
        {"cond": "Umidade Alta nos Corredores", "desc": "Saturação hídrica eleva o risco de infiltrações nas paredes do condomínio.", "mod": "+15% de custo em manutenção de residências nesta semana.", "efeito": "manutencao_custo", "valor": 15},
    ],
    # Máfia / Clube subterrâneo
    "mafia": [
        {"cond": "Escuridão Operacional Total", "desc": "Sem lâmpadas, sem luz etérea. As transmissões clandestinas operam no escuro absoluto.", "mod": "+20% de furtividade. -15% de visibilidade para forças de segurança.", "efeito": "furtividade_mafia", "valor": 20},
        {"cond": "Névoa de Cinzas de Transação", "desc": "Fumaça residual de documentos incinerados após uma reunião clandestina.", "mod": "+10% de chance de encobrir evidências financeiras.", "efeito": "evidencia_cobertura", "valor": 10},
        {"cond": "Silêncio Rádio-Elétrico Total", "desc": "Supressores de sinal arcano foram ativados. Nenhum grampo externo funciona neste momento.", "mod": "Comandos de espionagem e grampo externos têm 0% de eficácia neste canal.", "efeito": "antiespionagem", "valor": 100},
    ],
    # Default / outros locais
    "default": [
        {"cond": "Condições Nominais Registradas", "desc": "Os instrumentos de medição não detectam anomalias atmosféricas significativas neste perímetro.", "mod": "Sem modificadores ativos. Condições de baseline imperiais.", "efeito": None, "valor": 0},
        {"cond": "Variação Etérea de Baixa Intensidade", "desc": "Flutuações menores nas correntes de éter local. Imperceptíveis para a maioria dos cidadãos.", "mod": "+2% de todos os atributos. Variação residual sem impacto prático.", "efeito": "variacao_menor", "valor": 2},
        {"cond": "Pressão Atmosférica Imperial Estável", "desc": "Condições meteorológicas equilibradas. Nenhuma perturbação nas correntes de éter.", "mod": "Condições ideais para quaisquer atividades. Sem bônus ou penalidades.", "efeito": None, "valor": 0},
    ],
}

# ─── MAPEAMENTO DE local_atual → classe climática ─────────────────────────────
_LOCAL_MAP: dict[str, str] = {
    "cidadela": "cidadela", "cidadela_branca": "cidadela", "trono": "cidadela",
    "hospital": "hospital", "enfermaria": "hospital", "recepção": "hospital",
    "escola": "escola", "academia": "escola", "sala": "escola", "biblioteca": "escola",
    "beco": "beco", "subterrâneo": "beco", "submundo": "beco", "masmorra": "beco",
    "parque": "parque", "jardim": "parque", "praça": "praca", "praca": "praca",
    "cassino": "cassino", "jogo": "cassino",
    "laboratorio": "laboratorio", "laboratório": "laboratorio",
    "garagem": "garagem", "estacionamento": "garagem",
    "trem": "trem", "estação": "trem", "estacao": "trem",
    "banco": "banco",
    "condomínio": "condominio", "condominio": "condominio", "portaria": "condominio",
    "mafia": "mafia", "máfia": "mafia", "clube": "mafia",
}


def _detectar_classe_local(local_atual: str) -> str:
    if not local_atual:
        return "default"
    local_lower = local_atual.lower()
    for chave, classe in _LOCAL_MAP.items():
        if chave in local_lower:
            return classe
    return "default"


class ClimaIA:
    def __init__(self, bot):
        self.bot = bot
        self._loops_iniciados = False

    def cog_load(self):
        if not self._loops_iniciados:
            self._loops_iniciados = True
            self.bot.loop.create_task(self._loop_clima_global())

    async def handle_clima(self, message, args):
        u = get_user(message.author.id)
        local_atual = u.get("local_atual", "cidadela")
        classe = _detectar_classe_local(local_atual)
        opcoes = CLIMA_POR_LOCAL.get(classe, CLIMA_POR_LOCAL["default"])
        clima = random.choice(opcoes)

        # Gera variação narrativa via IA se disponível
        descricao_final = clima["desc"]
        try:
            from cogs.loremaster import _gerar, DIRETRIZ_ORIGINALIDADE
            from cogs.eras import get_tom_ia
            sys_clima = (
                f"Você é o Meteorologista Imperial de Tenshi. Descreva em 2-3 frases formais, "
                f"sóbrias e documentais a condição climática '{clima['cond']}' observada em "
                f"'{local_atual}'. Use linguagem científica-imperial em Português Brasileiro. "
                f"Não use emojis. Não seja poético — seja técnico e preciso.\n\n"
                f"{DIRETRIZ_ORIGINALIDADE}"
            )
            descricao_ia = await _gerar(
                f"Condição: {clima['cond']}. Local: {local_atual}. Detalhes base: {clima['desc']}",
                sys_clima,
                temperatura=0.85
            )
            if descricao_ia and len(descricao_ia) > 30:
                descricao_final = descricao_ia
        except Exception:
            pass

        e = self._build_embed_clima(clima, local_atual, descricao_final, message.author)
        await message.channel.send(embed=e)

        # Aplicar modificador mecânico
        if clima["efeito"] and clima["valor"] != 0:
            await self._aplicar_modificador(message.author.id, clima["efeito"], clima["valor"])

    def _build_embed_clima(self, clima: dict, local: str, desc: str, autor) -> discord.Embed:
        from design import embed_doc, COR_GERAL, COR_HOSPITAL, COR_CRIME, COR_ADMIN
        # Cor por classe
        classe = _detectar_classe_local(local)
        cor = {
            "cidadela": COR_GERAL, "hospital": COR_HOSPITAL,
            "beco": COR_CRIME, "mafia": COR_CRIME,
            "parque": 0x1A5C2E, "praca": COR_GERAL, "cassino": 0x8B6914,
            "laboratorio": 0x4B0082, "garagem": COR_ADMIN,
            "trem": COR_ADMIN, "escola": COR_GERAL,
        }.get(classe, COR_GERAL)

        e = discord.Embed(
            title=f"Boletim Meteorológico Imperial — {local.replace('_',' ').title()}",
            description=f"---\n{desc}",
            color=cor
        )
        e.add_field(name="Condição Atmosférica", value=clima["cond"], inline=True)
        e.add_field(name="Perímetro Analisado", value=local.replace("_", " ").title(), inline=True)
        e.add_field(name="Modificador Atmosférico", value=clima["mod"], inline=False)
        e.set_footer(text=f"Serviço de Meteorologia Imperial  •  {__import__('datetime').datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC")
        return e

    async def _aplicar_modificador(self, user_id: int, efeito: str, valor: int):
        u = get_user(user_id)
        mods = u.setdefault("clima_mods", {})
        mods[efeito] = {"valor": valor, "expira": (__import__("datetime").datetime.utcnow() + __import__("datetime").timedelta(hours=6)).isoformat()}
        save_user(user_id, u)

    def get_modificador(self, user_id: int, efeito: str) -> int:
        u = get_user(user_id)
        mods = u.get("clima_mods", {})
        mod = mods.get(efeito)
        if not mod: return 0
        from datetime import datetime
        if datetime.utcnow() > datetime.fromisoformat(mod["expira"]):
            return 0
        return mod["valor"]

    async def _loop_clima_global(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = __import__("datetime").datetime.utcnow()
            if agora.hour in (6, 12, 18, 0) and agora.minute < 30:
                for guild in self.bot.guilds:
                    canal = self._canal(guild, "clima")
                    if canal:
                        try:
                            # Clima global da cidadela
                            opcoes = CLIMA_POR_LOCAL["cidadela"]
                            clima = random.choice(opcoes)
                            e = self._build_embed_clima(clima, "Cidadela Branca", clima["desc"],
                                                        type("obj", (), {"display_name": "Sistema"})())
                            await canal.send(embed=e)
                        except Exception: pass
            await asyncio.sleep(1800)

    def _canal(self, guild, nome: str):
        if not guild: return None
        for ch in guild.text_channels:
            if nome.lower() in ch.name.lower(): return ch
        return None
