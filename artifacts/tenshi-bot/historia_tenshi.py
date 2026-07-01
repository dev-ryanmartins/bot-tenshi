"""
Base historica oficial do Imperio Tenshi.

Origem: "Bases Historicas do Imperio Tenshi.pdf" fornecido ao projeto.
O bot usa uma sintese para orientar IA e ritos sem despejar o documento inteiro.
"""

FONTE_HISTORICA = "Bases Historicas do Imperio Tenshi.pdf"
PAGINAS_FONTE_HISTORICA = 79

HISTORIA_TOPICOS = [
    {
        "tema": "Origem do Imperio",
        "texto": (
            "A Casa Tenshi remonta a Primeira Alianca Celestial, quando guardioes conhecidos como "
            "Portadores da Luz Eterna confiaram a uma linhagem humana o dever de preservar ordem, "
            "livre-arbitrio, sabedoria e responsabilidade."
        ),
    },
    {
        "tema": "Sangue Angelical",
        "texto": (
            "O Sangue Angelical nao e poder sobrenatural; e simbolo moral de disciplina, coragem, "
            "honra, protecao dos vulneraveis e fidelidade a palavra dada."
        ),
    },
    {
        "tema": "Cinco Pilares",
        "texto": (
            "A honra vale mais que riqueza; a palavra empenhada tem forca de juramento; a familia e "
            "primeiro patrimonio; conhecimento e poder; autoridade existe para servir e proteger."
        ),
    },
    {
        "tema": "Brasao Tenshi",
        "texto": (
            "O Brasao Imperial representa protecao, honra, justica, continuidade e esperanca. Ele "
            "recorda que autoridade pertence a instituicao e deve atravessar geracoes."
        ),
    },
    {
        "tema": "Primeira Fortaleza",
        "texto": (
            "A primeira sede da Casa reuniu o Grande Salao da Coroa, Arquivo Imperial, Salao do "
            "Conselho, Capela da Luz Eterna e Patio dos Juramentos."
        ),
    },
    {
        "tema": "Conselho Imperial",
        "texto": (
            "O soberano governa acompanhado por conselheiros para impedir decisoes movidas por ira, "
            "orgulho ou ambicao e preservar continuidade institucional."
        ),
    },
    {
        "tema": "Tenshi Enterprise",
        "texto": (
            "A organizacao moderna inclui patrimonio economico e estrategico da Coroa, com tecnologia, "
            "IA, seguranca, energia, educacao, saude, infraestrutura e pesquisa."
        ),
    },
    {
        "tema": "Ordem dos Guardioes",
        "texto": (
            "A Ordem dos Guardioes protege familia, arquivos, patrimonio e populacao, subordinada as "
            "leis do Imperio e leal a instituicao."
        ),
    },
    {
        "tema": "Legado",
        "texto": (
            "A grandeza Tenshi nao se mede por fortuna ou exercitos, mas pela continuidade da linhagem, "
            "preservacao dos principios e uniao entre tradicao e inovacao."
        ),
    },
]

HISTORIA_PROMPT_RESUMIDA = (
    "Base historica oficial do Imperio Tenshi: a Casa Tenshi nasce da Primeira Alianca, "
    "fundada sobre honra, palavra, familia, conhecimento e servico. O Sangue Angelical e "
    "simbolo moral, nao poder sobrenatural. O Brasao representa protecao, honra, justica, "
    "continuidade e esperanca. O Imperio preserva Conselho, Guardioes, Arquivos, tradicao "
    "familiar e estrutura moderna pela Tenshi Enterprise. Toda narrativa deve unir tradicao, "
    "responsabilidade, disciplina, inovacao e protecao da Casa."
)

HISTORIA_CASAMENTO_RESUMO = (
    "Antes dos juramentos, a Casa recorda apenas o essencial de sua origem: Tenshi nasceu da "
    "Primeira Alianca, onde a palavra deveria valer mais que a espada. Seu brasao guarda cinco "
    "virtudes — protecao, honra, justica, continuidade e esperanca — e seu legado exige que toda "
    "uniao fortaleça a familia, preserve a palavra dada e sirva ao futuro do Imperio."
)


def resumo_historia_completo() -> str:
    linhas = [f"**Fonte:** {FONTE_HISTORICA} ({PAGINAS_FONTE_HISTORICA} paginas)"]
    linhas.extend(f"**{item['tema']}:** {item['texto']}" for item in HISTORIA_TOPICOS)
    return "\n\n".join(linhas)
