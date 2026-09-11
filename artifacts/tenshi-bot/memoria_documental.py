"""
Memoria documental oficial do bot Tenshi.

Todos os PDFs colocados na raiz do projeto sao contabilizados aqui como fontes
canonicas resumidas para comandos, IA e consultas de RPG.
"""

from historia_tenshi import HISTORIA_CASAMENTO_RESUMO, HISTORIA_PROMPT_RESUMIDA, HISTORIA_TOPICOS


DOCUMENTOS_IMPERIAIS = {
    "codigo": {
        "titulo": "Codigo Imperial Tenshi 2026",
        "arquivo": "Codigo_Imperial_Tenshi- 2026 .pdf",
        "paginas": 55,
        "aliases": ("codigo", "código", "lei", "constituicao", "constituição", "legal"),
        "resumo": (
            "Constituicao e base legal do Imperio Tenshi. Define fundamentos, soberania, "
            "Imperador, Rainha, Familia Imperial, Chancelaria, ministerios, arquivos, "
            "autoridade, proporcionalidade, razoabilidade e limites narrativos do RPG."
        ),
        "topicos": [
            "Honra, lealdade, boa-fe, justica, disciplina, respeito e estabilidade institucional.",
            "Alloy Tenshi e o Imperador, chefe supremo e guardiao da unidade imperial.",
            "A Rainha Imperial integra a Coroa apos casamento formal e exerce funcoes delegadas.",
            "Atos oficiais devem preservar harmonia, equilibrio narrativo e interesse institucional.",
            "Ministerios, Chancelaria e Arquivo Geral organizam a memoria e os decretos da Coroa.",
        ],
    },
    "rito": {
        "titulo": "Rito Solene do Matrimonio Imperial Tenshi",
        "arquivo": "Rito Solene do Matrimônio Imperial Tenshi.pdf",
        "paginas": 5,
        "aliases": ("rito", "matrimonio", "matrimônio", "casamento", "cerimonia", "cerimônia"),
        "resumo": (
            "Cerimonial oficial do casamento real. Descreve preparacao do santuario, entrada "
            "solene, saudacao imperial, resumo historico, intencoes, ritual magico, juramentos, "
            "aliancas, assinaturas, proclamacao, bencao, caminho dos soberanos e encerramento."
        ),
        "topicos": [
            "No altar ficam apenas Brasao, Livro dos Juramentos, Aliancas, Chama e Calice.",
            "O rito exige livre vontade dos noivos e confirmacao formal dos juramentos.",
            "Rei e Rainha fazem juramentos separados perante a Casa e o Imperio.",
            "A proclamacao final registra a uniao perante a Familia Imperial.",
            f"No casamento, a historia deve ser citada apenas assim: {HISTORIA_CASAMENTO_RESUMO}",
        ],
    },
    "bases": {
        "titulo": "Bases Historicas do Imperio Tenshi",
        "arquivo": "Bases Históricas do Império Tenshi.pdf",
        "paginas": 79,
        "aliases": ("bases", "historia", "história", "origem", "linhagem", "brasao", "brasão"),
        "resumo": HISTORIA_PROMPT_RESUMIDA,
        "topicos": [f"{item['tema']}: {item['texto']}" for item in HISTORIA_TOPICOS],
    },
    "academia": {
        "titulo": "Academia Imperial Tenshi - Curriculo Oficial RPG",
        "arquivo": "Academia_Imperial_Tenshi_Curriculo_RPG.pdf",
        "paginas": 2,
        "aliases": ("academia", "curriculo", "currículo", "faculdade", "curso", "aula", "herdeiros"),
        "resumo": (
            "Curriculo oficial ficticio da Academia Imperial Tenshi. Reune faculdades de governo, "
            "Enterprise, tecnologia, militar, diplomacia, linguas, medicina, artes, etiqueta, "
            "formacao da Familia Imperial, academias especiais e programa obrigatorio dos herdeiros."
        ),
        "topicos": [
            "Faculdade Imperial de Governo: lideranca, ciencia politica, direito, etica e gestao de crises.",
            "Tenshi Enterprise: administracao, economia, compliance, mercado financeiro e patrimonio.",
            "Tecnologia: computacao, IA, cloud, engenharia, seguranca digital e criptografia.",
            "Militar e diplomacia: estrategia, inteligencia, protecao executiva, protocolo e mediacao.",
            "Herdeiros estudam historia da dinastia, administracao da Coroa, oratoria e psicologia da lideranca.",
        ],
    },
}


def prompt_memoria_documental() -> str:
    blocos = []
    for doc in DOCUMENTOS_IMPERIAIS.values():
        blocos.append(
            f"- {doc['titulo']} ({doc['paginas']} paginas): {doc['resumo']}"
        )
    return "Memoria documental oficial contabilizada pelo bot:\n" + "\n".join(blocos)


def listar_documentos() -> list[dict]:
    return [
        {
            "id": key,
            "titulo": value["titulo"],
            "arquivo": value["arquivo"],
            "paginas": value["paginas"],
            "resumo": value["resumo"],
        }
        for key, value in DOCUMENTOS_IMPERIAIS.items()
    ]


def obter_documento(identificador: str) -> tuple[str, dict] | tuple[None, None]:
    termo = identificador.lower().strip()
    for key, doc in DOCUMENTOS_IMPERIAIS.items():
        if termo == key or termo in doc["aliases"]:
            return key, doc
    for key, doc in DOCUMENTOS_IMPERIAIS.items():
        alvo = f"{doc['titulo']} {doc['arquivo']}".lower()
        if termo and termo in alvo:
            return key, doc
    return None, None


def buscar_memoria(consulta: str) -> list[tuple[str, dict, list[str]]]:
    termos = [t.lower() for t in consulta.split() if len(t) > 2]
    resultados = []
    for key, doc in DOCUMENTOS_IMPERIAIS.items():
        texto_doc = f"{doc['titulo']} {doc['arquivo']} {doc['resumo']} {' '.join(doc['topicos'])}".lower()
        if not termos or any(t in texto_doc for t in termos):
            topicos = [t for t in doc["topicos"] if not termos or any(term in t.lower() for term in termos)]
            resultados.append((key, doc, topicos or doc["topicos"][:3]))
    return resultados
