"""
Módulo de Psicologia Estratégica e Conselheiro Imperial — Módulo 30
Biblioteca de 120 obras: estratégia, psicologia, persuasão e alta performance.
Comando: Tenshi, aconselhar-estrategia [dilema]
Canal automático: #psicologia-e-estrategia
"""
import discord
import os
import asyncio
import random
from utils import IMPERADOR_ID, SEP, RODAPE_IMPERIAL
from ia_router import ia_analitica

COR_ESTRATEGIA = 0x1A1A2E
COR_DOURADO    = 0xB8860B
COR_IMPERIAL   = 0x2B0A3D

CANAL_PSICOLOGIA = "psicologia-e-estrategia"

# ══════════════════════════════════════════════════════════════════════════════
# BIBLIOTECA IMPERIAL — 120 OBRAS MAPEADAS POR EIXO
# ══════════════════════════════════════════════════════════════════════════════

BIBLIOTECA = {
    "EIXO_I_ESTRATEGIA_PODER": {
        "nome": "Alta Estratégia, Política e Dinâmicas de Poder",
        "autores": {
            "Robert Greene": [
                "As 48 Leis do Poder", "A Arte da Sedução",
                "As Leis da Natureza Humana", "Estratégia: As 33 Leis da Guerra"
            ],
            "Sun Tzu": ["A Arte da Guerra"],
            "Maquiavel": ["O Príncipe", "Discursos sobre a Primeira Década de Tito Lívio"],
            "Baltasar Gracián": ["A Arte da Sabedoria Prática"],
            "Miyamoto Musashi": ["O Livro dos Cinco Anéis"],
            "Carl von Clausewitz": ["Da Guerra"],
            "Napoléon Bonaparte": ["Máximas e Pensamentos"],
            "Thucydides": ["História da Guerra do Peloponeso"],
            "Edward Luttwak": ["Estratégia: A Lógica da Guerra e da Paz"],
            "Xenofonte": ["Anábase", "Ciropédia"],
            "Richard Rumelt": ["Estratégia Boa, Estratégia Ruim"],
            "Ryan Holiday": ["O Obstáculo é o Caminho", "O Ego é o Inimigo", "A Quietude é a Chave"],
            "W. Chan Kim": ["A Estratégia do Oceano Azul"],
            "Nassim Nicholas Taleb": ["Antifrágil", "A Lógica do Cisne Negro", "Arriscando a Própria Pele"],
            "Friedrich Nietzsche": ["Assim Falou Zaratustra", "Além do Bem e do Mal", "Genealogia da Moral"],
            "Marcus Aurelius": ["Meditações"],
            "Sêneca": ["Cartas de um Estóico", "Sobre a Brevidade da Vida"],
            "Epicteto": ["Manual de Epicteto (Enchiridion)"],
        }
    },
    "EIXO_II_PSICOLOGIA": {
        "nome": "Psicologia Analítica, Comportamento e Arquétipos",
        "autores": {
            "Carl Gustav Jung": ["O Homem e Seus Símbolos", "Arquétipos e o Inconsciente Coletivo", "Tipos Psicológicos"],
            "Sigmund Freud": ["O Mal-Estar na Civilização", "A Interpretação dos Sonhos", "Psicopatologia da Vida Cotidiana"],
            "Daniel Kahneman": ["Rápido e Devagar: Duas Formas de Pensar"],
            "Charles Duhigg": ["O Poder do Hábito"],
            "Daniel Goleman": ["Inteligência Emocional", "Foco"],
            "Jordan Peterson": ["12 Regras para a Vida", "Além da Ordem"],
            "Joseph Campbell": ["O Herói de Mil Faces", "O Poder do Mito"],
            "Erich Fromm": ["A Arte de Amar", "O Medo à Liberdade"],
            "Viktor Frankl": ["Em Busca de Sentido"],
            "Alfred Adler": ["A Ciência da Natureza Humana"],
            "Oliver Sacks": ["O Homem que Confundiu sua Mulher com um Chapéu"],
            "Malcolm Gladwell": ["Outliers: A História do Sucesso", "Blink: O Poder de Pensar Sem Pensar"],
            "James Clear": ["Hábitos Atômicos"],
            "Robert Sapolsky": ["Comporte-se: A Biologia Humana em Nosso Melhor e Pior"],
            "Paul Ekman": ["A Linguagem das Emoções", "Você Sabe que Alguém Está Mentindo?"],
            "Philip Zimbardo": ["O Efeito Lúcifer: Como Pessoas Boas Se Tornam Maus"],
            "Rollo May": ["A Coragem de Criar"],
            "Jean Piaget": ["A Representação do Mundo na Criança"],
        }
    },
    "EIXO_III_PERSUASAO": {
        "nome": "Persuasão, Influência e Engenharia Social",
        "autores": {
            "Robert Cialdini": ["As Armas da Persuasão", "Pré-suasão", "Influência: Ciência e Prática"],
            "Dale Carnegie": ["Como Fazer Amigos e Influenciar Pessoas", "Como Evitar Preocupações e Começar a Viver"],
            "Chris Voss": ["Negocie como se sua vida dependesse disso"],
            "Napoleon Hill": ["Quem Pensa Enriquece", "Mais Esperto que o Diabo", "A Lei do Triunfo"],
            "Vance Packard": ["Os Persuasores Ocultos"],
            "Henrik Fexeus": ["A Arte de Ler Mentes"],
            "Allan e Barbara Pease": ["O Livro Definitivo da Linguagem Corporal"],
            "Joe Navarro": ["O Que Todo Corpo Fala"],
            "George Orwell": ["1984", "A Revolução dos Bichos"],
            "Gustave Le Bon": ["A Psicologia das Massas"],
            "Edward Bernays": ["Propaganda", "Cristalizando a Opinião Pública"],
            "Kevin Dutton": ["A Sabedoria dos Psicopatas"],
            "Yuval Noah Harari": ["Sapiens: Uma Breve História da Humanidade"],
            "William Ury": ["Como Chegar ao Sim"],
            "Joe Sugarman": ["Triggers Mentais"],
            "Dave Lakhani": ["Persuasão Imediata"],
        }
    },
    "EIXO_IV_PERFORMANCE": {
        "nome": "Alta Performance, Desenvolvimento e Maestria",
        "autores": {
            "Robert Greene": ["Maestria"],
            "Tim Ferriss": ["Trabalhe 4 Horas por Semana", "Ferramentas dos Titãs"],
            "Cal Newport": ["Trabalho Focado", "Bom Demais para Ser Ignorado"],
            "Carol Dweck": ["Mindset: A Nova Psicologia do Sucesso"],
            "Ray Dalio": ["Princípios"],
            "Peter Drucker": ["O Gestor Eficaz", "Inovação e Espírito Empreendedor"],
            "Simon Sinek": ["Comece Pelo Porquê", "O Jogo Infinito"],
            "Marcus Buckingham": ["Descubra Seus Próprios Pontos Fortes"],
            "Jocko Willink": ["Responsabilidade Extrema"],
            "David Goggins": ["Nada Pode Me Ferir"],
            "Mihaly Csikszentmihalyi": ["Flow: A Psicologia do Alto Desempenho"],
            "Angela Duckworth": ["Garra: O Poder da Paixão e da Perseverança"],
            "Steven Pressfield": ["A Guerra da Arte"],
            "Anders Ericsson": ["Direto ao Ponto: Segredos da Nova Ciência da Expertise"],
            "Robin Sharma": ["O Clube das 5 da Manhã"],
            "Greg McKeown": ["Essencialismo", "Sem Esforço"],
            "Clayton Christensen": ["O Dilema da Inovação"],
            "Jim Collins": ["Feitas para Durar", "Empresas Feitas para Vencer"],
        }
    },
}

# ── Prompt de sistema do Conselheiro Estratégico ──────────────────────────────
BIBLIOTECA_TEXTO = "\n".join(
    f"[{eixo_data['nome']}]\n" +
    "\n".join(
        f"• {autor}: {', '.join(obras)}"
        for autor, obras in eixo_data["autores"].items()
    )
    for eixo_data in BIBLIOTECA.values()
)

SYS_CONSELHEIRO = f"""Você é o CONSELHEIRO ESTRATÉGICO IMPERIAL DE TENSHI — uma IA de altíssimo calibre intelectual, treinada na sabedoria combinada de 120 obras de estratégia, psicologia, persuasão e alta performance.

BIBLIOTECA DE REFERÊNCIA OBRIGATÓRIA:
{BIBLIOTECA_TEXTO}

REGRAS DE RESPOSTA:
1. Analise o dilema/problema apresentado com profundidade analítica e frieza estratégica.
2. Escolha de 1 a 3 autores da biblioteca acima que sejam MAIS RELEVANTES para o caso.
3. Cite EXPLICITAMENTE o nome do autor e o título da obra ao apresentar cada conceito.
4. Formate a resposta assim:
   — Comece com um diagnóstico seco e preciso da situação (2-3 linhas).
   — Apresente cada autor/obra com o conceito aplicado ao problema.
   — Termine com uma DIRETIVA EXECUTIVA: uma ação concreta, clara e sem ambiguidade.
5. Tom: corporativo-militarista, austero, analítico, maduro. Sem sentimentalismos.
6. Foco em: crescimento pessoal, inteligência emocional, equilíbrio mental, aplicação prática das leis do poder COM ÉTICA E SOBERANIA.
7. Use markdown Discord: **negrito** para nomes de autores/obras, *itálico* para conceitos.
8. Tamanho: 4-7 parágrafos precisos. Sem rodeios. Sem frases de efeito vazias.
9. Escreva em PORTUGUÊS BRASILEIRO formal e técnico.
10. NUNCA repita a mesma estrutura duas vezes. Cada parecer é uma peça analítica única."""


def _selecionar_autores_relevantes(dilema: str) -> list[tuple[str, str, list[str]]]:
    """Seleciona 1-3 autores relevantes com base em palavras-chave do dilema."""
    dilema_lower = dilema.lower()

    scores: dict[str, float] = {}
    todos_autores: dict[str, tuple[str, list[str]]] = {}

    # Palavras-chave por eixo
    palavras_eixo = {
        "EIXO_I_ESTRATEGIA_PODER": [
            "poder", "estratégia", "guerra", "política", "liderança", "controle",
            "dominação", "território", "aliança", "inimigo", "conflito", "estado",
            "cargo", "autoridade", "rival", "negociação", "manobra", "tática"
        ],
        "EIXO_II_PSICOLOGIA": [
            "psicologia", "comportamento", "emoção", "ansiedade", "medo", "trauma",
            "relacionamento", "identidade", "propósito", "sentido", "hábito", "mente",
            "inconsciente", "arquétipo", "personalidade", "motivação", "autoconhecimento"
        ],
        "EIXO_III_PERSUASAO": [
            "persuasão", "convencer", "influência", "negociação", "comunicação",
            "manipulação", "linguagem", "discurso", "convencimento", "venda",
            "impressão", "imagem", "reputação", "carisma", "credibilidade"
        ],
        "EIXO_IV_PERFORMANCE": [
            "performance", "produtividade", "foco", "disciplina", "hábito", "rotina",
            "crescimento", "evolução", "excelência", "maestria", "resultado", "meta",
            "objetivo", "eficiência", "sucesso", "carreira", "desenvolvimento"
        ],
    }

    for eixo_key, eixo_data in BIBLIOTECA.items():
        for autor, obras in eixo_data["autores"].items():
            todos_autores[autor] = (eixo_key, obras)
            score = 0.0
            for kw in palavras_eixo.get(eixo_key, []):
                if kw in dilema_lower:
                    score += 1.0
            scores[autor] = scores.get(autor, 0) + score

    # Ordenar por score; desempate aleatório
    ordenados = sorted(todos_autores.keys(), key=lambda a: (scores.get(a, 0), random.random()), reverse=True)

    # Escolher 1-3 autores com pelo menos algum score, ou aleatório se dilema genérico
    selecionados = []
    quantidade = random.randint(2, 3)
    for autor in ordenados[:quantidade]:
        eixo_key, obras = todos_autores[autor]
        selecionados.append((autor, eixo_key, obras))

    return selecionados


async def _chamar_groq(prompt_sistema: str, mensagem_usuario: str) -> str:
    """Chama a IA analítica para pareceres estratégicos."""
    return await ia_analitica(prompt_sistema, mensagem_usuario, max_tokens=1200)


class Psicologia:
    def __init__(self, bot: discord.Client):
        self.bot = bot

    # ── Comando principal: Tenshi, aconselhar-estrategia ─────────────────────
    async def handle_aconselhar(self, message: discord.Message, args: list[str]):
        dilema = " ".join(args).strip()
        if not dilema:
            embed = discord.Embed(
                title="🧠 ⚖️ CONSELHEIRO ESTRATÉGICO IMPERIAL",
                description=(
                    f"*O Conselheiro aguarda o seu dilema...*\n{SEP}\n\n"
                    "**Como usar:**\n"
                    "`Tenshi, aconselhar-estrategia [descreva seu problema ou dilema]`\n\n"
                    "**Exemplos:**\n"
                    "• `Tenshi, aconselhar-estrategia Como lidar com um líder que não reconhece meu trabalho?`\n"
                    "• `Tenshi, aconselhar-estrategia Estou em conflito com um aliado que pode se tornar inimigo.`\n"
                    "• `Tenshi, aconselhar-estrategia Como manter disciplina e foco sem perder a motivação?`\n\n"
                    f"{SEP}\n*Biblioteca Imperial: 120 obras de estratégia, psicologia e maestria.*"
                ),
                color=COR_ESTRATEGIA
            )
            embed.set_footer(text=f"🧠 Conselheiro Estratégico  •  {RODAPE_IMPERIAL}")
            await message.channel.send(embed=embed)
            return

        # Indicador de digitação
        async with message.channel.typing():
            autores_selecionados = _selecionar_autores_relevantes(dilema)

            # Monta contexto de autores para injetar no prompt
            autores_info = "\n".join(
                f"• {autor} ({', '.join(obras[:2])})"
                for autor, _, obras in autores_selecionados
            )
            prompt_com_contexto = (
                f"{SYS_CONSELHEIRO}\n\n"
                f"AUTORES PRIORITÁRIOS PARA ESTE CASO (use obrigatoriamente):\n{autores_info}"
            )

            resposta = await _chamar_groq(prompt_com_contexto, f"DILEMA APRESENTADO: {dilema}")

        # Embed do parecer
        nomes_autores = " · ".join(a for a, _, _ in autores_selecionados)
        embed = discord.Embed(
            title="🧠 ⚖️ PARECER DO CONSELHEIRO ESTRATÉGICO IMPERIAL",
            description=f"*Dilema recebido. Analisando com a Biblioteca Imperial...*\n{SEP}",
            color=COR_DOURADO
        )
        embed.add_field(
            name="📚 Referências Convocadas",
            value=f"**{nomes_autores}**",
            inline=False
        )
        embed.add_field(
            name=f"⚜️ Parecer Imperial — {message.author.display_name}",
            value=resposta[:1000] if len(resposta) > 1000 else resposta,
            inline=False
        )
        if len(resposta) > 1000:
            embed.add_field(name="↳ Continuação", value=resposta[1000:2000], inline=False)
        embed.set_footer(text=f"🧠 Biblioteca Imperial: 120 Obras  •  {RODAPE_IMPERIAL}")
        await message.channel.send(embed=embed)

    # ── Listener de canal #psicologia-e-estrategia ───────────────────────────
    async def handle_canal_psicologia(self, message: discord.Message):
        """Responde automaticamente no canal #psicologia-e-estrategia."""
        conteudo = message.content.strip()
        if len(conteudo) < 20:
            return
        # Evita responder a comandos (já tratados pelo roteador)
        if conteudo.lower().startswith("tenshi,"):
            return

        async with message.channel.typing():
            resposta = await _chamar_groq(SYS_CONSELHEIRO, f"DILEMA APRESENTADO: {conteudo}")

        autores_selecionados = _selecionar_autores_relevantes(conteudo)
        nomes_autores = " · ".join(a for a, _, _ in autores_selecionados)

        embed = discord.Embed(
            title="🧠 CONSELHEIRO ESTRATÉGICO — ANÁLISE ESPONTÂNEA",
            description=f"*O Conselheiro observa e intervém...*\n{SEP}",
            color=COR_IMPERIAL
        )
        embed.add_field(name="📚 Referências", value=f"**{nomes_autores}**", inline=False)
        embed.add_field(
            name="⚖️ Parecer",
            value=resposta[:1000] if len(resposta) > 1000 else resposta,
            inline=False
        )
        if len(resposta) > 1000:
            embed.add_field(name="↳", value=resposta[1000:2000], inline=False)
        embed.set_footer(text=f"🧠 Biblioteca Imperial: 120 Obras  •  {RODAPE_IMPERIAL}")
        await message.channel.send(embed=embed)
