"""
Base normativa resumida do Codigo Imperial Tenshi 2026 e do Rito Solene.

Este arquivo transforma os PDFs fornecidos pelo dono do bot em regras
operacionais curtas para prompts, validacoes e comandos do RPG.
"""
from historia_tenshi import HISTORIA_CASAMENTO_RESUMO, HISTORIA_PROMPT_RESUMIDA
from memoria_documental import prompt_memoria_documental

PRINCIPIOS_IMPERIAIS = [
    "honra",
    "lealdade",
    "boa-fe",
    "justica",
    "disciplina",
    "respeito mutuo",
    "dignidade dos membros",
    "estabilidade institucional",
]

ARTIGOS_CHAVE = [
    {
        "ref": "Arts. 1-5",
        "tema": "fundamentos",
        "texto": (
            "O Imperio Tenshi e uma organizacao ficticia de RPG. Toda interpretacao deve "
            "preservar harmonia, equilibrio narrativo, proporcionalidade, razoabilidade e "
            "interesse institucional."
        ),
    },
    {
        "ref": "Arts. 16-20",
        "tema": "imperador",
        "texto": (
            "O Imperador e Chefe Supremo: sanciona leis, promulga decretos, nomeia autoridades, "
            "concede titulos, reconhece membros e comanda a Guarda Imperial."
        ),
    },
    {
        "ref": "Arts. 21-25",
        "tema": "pessoa do imperador",
        "texto": (
            "Alloy Tenshi deve preservar a unidade do Imperio, proteger a Familia Imperial, "
            "agir com imparcialidade administrativa e observar a Constituicao."
        ),
    },
    {
        "ref": "Arts. 26-35",
        "tema": "rainha imperial",
        "texto": (
            "A Rainha Imperial e autoridade maxima ao lado do Imperador, conferida exclusivamente "
            "ao conjuge oficialmente reconhecido apos Casamento Imperial; pode representar o Imperio, "
            "integrar o Conselho da Coroa, aconselhar o Imperador e exercer funcoes delegadas."
        ),
    },
    {
        "ref": "Arts. 36-40",
        "tema": "familia imperial",
        "texto": (
            "A Familia Imperial e formada por membros oficialmente reconhecidos pela Coroa. "
            "Ingresso exige ato formal do Imperador ou Decreto Imperial especifico."
        ),
    },
    {
        "ref": "Arts. 166-180",
        "tema": "chancelaria e ministerios",
        "texto": (
            "Atos oficiais devem ser registrados. Ministerios e cargos administrativos existem para "
            "auxiliar a Coroa e podem ser criados, nomeados ou revogados pelo Imperador."
        ),
    },
]

RITO_REAL_PASSOS = [
    {
        "titulo": "I - Preparacao do Santuario Imperial",
        "texto": (
            "O recinto deve estar preparado com o Circulo Imperial Tenshi. No Altar permanecem apenas "
            "o Brasao Imperial, Livro dos Juramentos, Aliancas, Chama da Eternidade e Calice da Alianca."
        ),
    },
    {
        "titulo": "II - Entrada Solene",
        "texto": (
            "A Guarda Imperial anuncia o inicio do rito. O Rei ingressa primeiro, acompanhado por "
            "Guardiões Imperiais. A Rainha entra com seu representante de honra."
        ),
    },
    {
        "titulo": "III - Saudacao Imperial",
        "texto": (
            "O Celebrante proclama que duas historias passam a formar uma unica Casa, firmada pela "
            "honra, lealdade e eternidade. Todos respondem: Assim seja."
        ),
    },
    {
        "titulo": "IV - Historia da Casa Tenshi",
        "texto": HISTORIA_CASAMENTO_RESUMO,
    },
    {
        "titulo": "V - Declaracao das Intencoes",
        "texto": (
            "O Celebrante pergunta a cada noivo se vem livremente para unir sua vida diante da Casa "
            "Imperial. Ambos devem confirmar por livre vontade."
        ),
    },
    {
        "titulo": "VI - Ritual Magico Tenshi",
        "texto": (
            "As maos sao unidas sobre o Brasao Imperial e envolvidas pela Faixa Escarlate da Uniao. "
            "A Chama da Eternidade simboliza coragem, responsabilidade e compromisso."
        ),
    },
    {
        "titulo": "VII - Juramento do Rei",
        "texto": (
            "O Rei promete proteger a Casa com honra, agir com justica e jamais abandonar quem recebe "
            "sua palavra."
        ),
    },
    {
        "titulo": "VIII - Juramento da Rainha",
        "texto": (
            "A Rainha promete caminhar ao lado de quem escolheu, preservar a Casa e permanecer leal em "
            "paz e dificuldade."
        ),
    },
    {
        "titulo": "IX - Consagracao das Aliancas",
        "texto": (
            "As aliancas sao consagradas sobre o Brasao Imperial e trocadas como circulos sem inicio "
            "nem fim."
        ),
    },
    {
        "titulo": "X - Assinatura do Livro Imperial",
        "texto": (
            "Assinam Rei, Rainha, Celebrante, duas testemunhas e Guardiao da Casa Tenshi. O Livro passa "
            "a integrar os registros oficiais."
        ),
    },
    {
        "titulo": "XI - Proclamacao da Uniao",
        "texto": (
            "O Celebrante declara oficialmente unidos o Rei e a Rainha perante a Familia e o Imperio."
        ),
    },
    {
        "titulo": "XII - Bencao da Casa Imperial",
        "texto": (
            "A Casa recebe votos de firmeza, coragem, sabedoria, prosperidade e honra por todas as "
            "geracoes."
        ),
    },
    {
        "titulo": "XIII - Caminho dos Soberanos",
        "texto": (
            "O casal atravessa o portal simbolico da Guarda Imperial. Anuncia-se o inicio de uma nova "
            "Casa dentro do Imperio Tenshi."
        ),
    },
    {
        "titulo": "XIV - Encerramento",
        "texto": (
            "A Guarda presta continencia, o Brasao e erguido e o rito e encerrado formalmente."
        ),
    },
]


def prompt_lei_imperial() -> str:
    artigos = "\n".join(f"- {a['ref']} ({a['tema']}): {a['texto']}" for a in ARTIGOS_CHAVE)
    principios = ", ".join(PRINCIPIOS_IMPERIAIS)
    return (
        "Voce e a IA administrativa do Imperio Tenshi. Responda sempre dentro do RPG, "
        "sem alegar autoridade no mundo real. Siga estritamente estes principios: "
        f"{principios}.\n\nBase legal resumida:\n{artigos}\n\n"
        f"Base historica resumida:\n{HISTORIA_PROMPT_RESUMIDA}\n\n"
        f"{prompt_memoria_documental()}\n\n"
        "Regras de seguranca: nao recomende perseguicao pessoal fora da narrativa; preserve "
        "proporcionalidade, razoabilidade e equilibrio narrativo; quando houver risco de abuso, "
        "proponha revisao por Alloy/Imperador."
    )


def buscar_artigos(consulta: str) -> list[dict]:
    termos = [t.lower() for t in consulta.split() if len(t) > 2]
    if not termos:
        return ARTIGOS_CHAVE[:4]
    achados = []
    for artigo in ARTIGOS_CHAVE:
        alvo = f"{artigo['ref']} {artigo['tema']} {artigo['texto']}".lower()
        if any(t in alvo for t in termos):
            achados.append(artigo)
    return achados or ARTIGOS_CHAVE[:4]
