import json
import os
import uuid
from datetime import datetime

DB_FILE        = "data/db.json"
CASAS_FILE     = "data/casas.json"
EMPRESAS_FILE  = "data/empresas.json"
FAMILIAS_FILE  = "data/familias.json"
BANCO_FILE     = "data/banco.json"
CASAMENTOS_FILE = "data/casamentos.json"
INFRACOES_FILE  = "data/infracoes.json"
INTERNADOS_FILE = "data/internados.json"

def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _save(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# USUÁRIOS
# ─────────────────────────────────────────────

def get_user(user_id: int) -> dict:
    data = _load(DB_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = _default_user()
        _save(DB_FILE, data)
    else:
        # Migrar campos novos para usuários antigos
        defaults = _default_user()
        for k, v in defaults.items():
            if k not in data[uid]:
                data[uid][k] = v
        _save(DB_FILE, data)
    return data[uid]

def save_user(user_id: int, user_data: dict):
    data = _load(DB_FILE)
    data[str(user_id)] = user_data
    _save(DB_FILE, data)

def get_all_users() -> dict:
    return _load(DB_FILE)

def _default_user() -> dict:
    return {
        # Identidade
        "nome": None,
        "titulo": "Cidadão do Império",
        "pegada": "imperial",  # imperial | familia | mafia | enterprise
        "avatar_desc": None,
        "historia": None,
        "habilidades": [],
        # Espécie e atributos
        "especie": None,
        "atributos": {"vida": 100, "mana": 100, "forca": 100, "agilidade": 100},
        "poderes": [],
        "ficha_aprovada": False,
        # Localização
        "local_atual": "cidadela",
        # RPG
        "nivel": 1,
        "xp": 0,
        "poder": 100,
        "inventario": [],
        "faccao": None,
        "faccao_pontos": 0,
        "status_bonus": {},
        "missoes_completas": 0,
        # Cooldowns
        "ultimo_treino": None,
        "ultima_missao": None,
        "ultimo_tarot": None,
        "ultimo_duelo": None,
        "ultimo_trabalho": None,
        # PvP
        "vitorias_duelo": 0,
        "derrotas_duelo": 0,
        # Financeiro
        "moedas": 100,
        "conta_banco": 0,
        "emprestimos": [],
        "historico_financeiro": [],
        # Social
        "casa_id": None,
        "casa_condominio": None,
        "fadiga": 0,
        "ultimo_descanso_lazer": None,
        "empresa_id": None,
        "cargo_empresa": None,
        "salario": 0,
        "familia_id": None,
        "cargo_familia": None,
        # Ficha completa
        "ficha": {},
    }

def _template_usuario() -> dict:
    """Template limpo para reset de era — preservar apenas conquistas/títulos/diplomas."""
    return {
        "nome": None, "titulo": "Cidadão do Império", "pegada": "imperial",
        "avatar_desc": None, "historia": None, "habilidades": [],
        "especie": None, "atributos": {"vida": 100, "mana": 100, "forca": 100, "agilidade": 100},
        "poderes": [], "ficha_aprovada": False, "local_atual": "cidadela",
        "nivel": 1, "xp": 0, "poder": 100, "inventario": [],
        "faccao": None, "faccao_pontos": 0, "status_bonus": {}, "missoes_completas": 0,
        "ultimo_treino": None, "ultima_missao": None, "ultimo_tarot": None,
        "ultimo_duelo": None, "ultimo_trabalho": None,
        "vitorias_duelo": 0, "derrotas_duelo": 0,
        "moedas": 100, "conta_banco": 0, "emprestimos": [], "historico_financeiro": [],
        "casa_id": None, "casa_condominio": None, "fadiga": 0,
        "ultimo_descanso_lazer": None, "empresa_id": None, "cargo_empresa": None,
        "salario": 0, "familia_id": None, "cargo_familia": None, "ficha": {},
        # Módulos 13-15
        "divida": 0, "juros_acumulados": 0, "banco_congelado": False,
        "isento_fiscal": False, "cidadania": False, "estrangeiro": True,
        "registro_civil": None, "nome_rp": None, "exilado": False,
        "foragido": False, "quarentena": False, "imortal": False,
        "seguro_vida": False, "aposentado": False, "co_soberano": False,
        "conquistas": [], "titulos": [], "diplomas": [],
    }

def calcular_nivel(xp: int):
    nivel = 1
    xp_necessario = 100
    xp_restante = xp
    while xp_restante >= xp_necessario:
        xp_restante -= xp_necessario
        nivel += 1
        xp_necessario = int(xp_necessario * 1.5)
    return nivel, xp_necessario - xp_restante

# ─────────────────────────────────────────────
# CASAS
# ─────────────────────────────────────────────

CATALOGO_CASAS = {
    "chalé_sombras": {"nome": "Chalé das Sombras", "emoji": "🏚️", "tipo": "Modesta", "preco": 300, "dono": None, "descricao": "Uma cabana humilde nas bordas do Império. Simples, mas segura.", "comodos": 2},
    "mansão_imperial": {"nome": "Mansão Imperial", "emoji": "🏛️", "tipo": "Nobre", "preco": 1500, "dono": None, "descricao": "Uma mansão de mármore branco com jardins eternos e salões dourados.", "comodos": 10},
    "torre_esotérica": {"nome": "Torre Esotérica", "emoji": "🗼", "tipo": "Mística", "preco": 800, "dono": None, "descricao": "Uma torre negra que toca as nuvens, onde segredos antigos pulsam nas paredes.", "comodos": 5},
    "forte_fronteira": {"nome": "Forte da Fronteira", "emoji": "🏰", "tipo": "Militar", "preco": 600, "dono": None, "descricao": "Uma fortaleza nas bordas do Império. Construída para guerreiros, por guerreiros.", "comodos": 6},
    "villa_nobreza": {"nome": "Villa da Nobreza", "emoji": "🏡", "tipo": "Luxuosa", "preco": 1000, "dono": None, "descricao": "Uma villa elegante com vinhedos, lagoa particular e aposentos imponentes.", "comodos": 8},
    "palácio_sombrio": {"nome": "Palácio Sombrio", "emoji": "🏯", "tipo": "Lendária", "preco": 3000, "dono": None, "descricao": "O palácio mais imponente de Tenshi. Apenas os mais poderosos ousam habitá-lo.", "comodos": 20},
    "cabana_floresta": {"nome": "Cabana da Floresta Negra", "emoji": "🌲", "tipo": "Rústica", "preco": 200, "dono": None, "descricao": "Escondida entre árvores milenares. Perfeita para quem busca paz e mistério.", "comodos": 2},
    "covil_mafia": {"nome": "Covil da Máfia", "emoji": "🏢", "tipo": "Clandestina", "preco": 900, "dono": None, "descricao": "Um QG secreto com entradas ocultas, cofres e salas de reunião blindadas.", "comodos": 7},
}

def get_casas() -> dict:
    dados = _load(CASAS_FILE)
    if not dados:
        dados = {k: dict(v) for k, v in CATALOGO_CASAS.items()}
        _save(CASAS_FILE, dados)
    else:
        # Garantir que novas casas do catálogo existam
        for k, v in CATALOGO_CASAS.items():
            if k not in dados:
                dados[k] = dict(v)
        _save(CASAS_FILE, dados)
    return dados

def comprar_casa(user_id: int, casa_id: str) -> tuple[bool, str]:
    casas = get_casas()
    if casa_id not in casas:
        return False, "Casa não encontrada."
    casa = casas[casa_id]
    if casa["dono"] is not None:
        return False, f"Esta propriedade já pertence a outro habitante."
    user = get_user(user_id)
    if user.get("casa_id"):
        return False, "Você já possui uma propriedade. Venda a atual primeiro."
    total = user["moedas"] + user.get("conta_banco", 0)
    if total < casa["preco"]:
        return False, f"Você precisa de {casa['preco']} moedas. Você tem {total}."
    restante = casa["preco"]
    if user["moedas"] >= restante:
        user["moedas"] -= restante
    else:
        restante -= user["moedas"]
        user["moedas"] = 0
        user["conta_banco"] -= restante
    user["casa_id"] = casa_id
    casas[casa_id]["dono"] = str(user_id)
    save_user(user_id, user)
    _save(CASAS_FILE, casas)
    return True, "Compra realizada com sucesso!"

def vender_casa(user_id: int) -> tuple[bool, str, int]:
    casas = get_casas()
    user = get_user(user_id)
    casa_id = user.get("casa_id")
    if not casa_id or casa_id not in casas:
        return False, "Você não possui uma propriedade.", 0
    casa = casas[casa_id]
    valor_venda = int(casa["preco"] * 0.7)
    user["moedas"] += valor_venda
    user["casa_id"] = None
    casas[casa_id]["dono"] = None
    save_user(user_id, user)
    _save(CASAS_FILE, casas)
    return True, casa["nome"], valor_venda

# ─────────────────────────────────────────────
# EMPRESAS
# ─────────────────────────────────────────────

def get_empresas() -> dict:
    return _load(EMPRESAS_FILE)

def save_empresas(data: dict):
    _save(EMPRESAS_FILE, data)

def criar_empresa(dono_id: int, nome: str) -> tuple[bool, str]:
    empresas = get_empresas()
    user = get_user(dono_id)
    if user.get("empresa_id"):
        return False, "Você já possui ou trabalha em uma empresa."
    for eid, e in empresas.items():
        if e["nome"].lower() == nome.lower():
            return False, "Já existe uma empresa com esse nome."
    custo = 500
    if user["moedas"] < custo:
        return False, f"Fundar uma empresa custa {custo} moedas. Você tem {user['moedas']}."
    eid = str(uuid.uuid4())[:8]
    empresas[eid] = {
        "nome": nome,
        "dono": str(dono_id),
        "saldo": 0,
        "fundada": datetime.utcnow().isoformat(),
        "funcionarios": {
            str(dono_id): {
                "cargo": "CEO",
                "salario": 0,
                "permissoes": ["contratar", "demitir", "pagar", "ver_financeiro"],
                "data_contratacao": datetime.utcnow().isoformat(),
            }
        },
        "historico": [],
    }
    user["moedas"] -= custo
    user["empresa_id"] = eid
    user["cargo_empresa"] = "CEO"
    save_user(dono_id, user)
    save_empresas(empresas)
    return True, eid

def contratar_funcionario(empresa_id: str, dono_id: int, alvo_id: int, cargo: str, salario: int) -> tuple[bool, str]:
    empresas = get_empresas()
    if empresa_id not in empresas:
        return False, "Empresa não encontrada."
    empresa = empresas[empresa_id]
    func = empresa["funcionarios"].get(str(dono_id), {})
    if "contratar" not in func.get("permissoes", []) and empresa["dono"] != str(dono_id):
        return False, "Você não tem permissão para contratar."
    alvo = get_user(alvo_id)
    if alvo.get("empresa_id"):
        return False, "Este usuário já trabalha em uma empresa."
    empresa["funcionarios"][str(alvo_id)] = {
        "cargo": cargo,
        "salario": salario,
        "permissoes": [],
        "data_contratacao": datetime.utcnow().isoformat(),
    }
    alvo["empresa_id"] = empresa_id
    alvo["cargo_empresa"] = cargo
    alvo["salario"] = salario
    save_user(alvo_id, alvo)
    save_empresas(empresas)
    return True, f"{cargo} contratado com salário de {salario} moedas."

def demitir_funcionario(empresa_id: str, dono_id: int, alvo_id: int) -> tuple[bool, str]:
    empresas = get_empresas()
    if empresa_id not in empresas:
        return False, "Empresa não encontrada."
    empresa = empresas[empresa_id]
    if empresa["dono"] == str(alvo_id):
        return False, "Não é possível demitir o CEO."
    if str(alvo_id) not in empresa["funcionarios"]:
        return False, "Este usuário não é funcionário desta empresa."
    del empresa["funcionarios"][str(alvo_id)]
    alvo = get_user(alvo_id)
    alvo["empresa_id"] = None
    alvo["cargo_empresa"] = None
    alvo["salario"] = 0
    save_user(alvo_id, alvo)
    save_empresas(empresas)
    return True, "Funcionário demitido."

def pagar_salarios(empresa_id: str, dono_id: int) -> tuple[bool, str, list]:
    empresas = get_empresas()
    if empresa_id not in empresas:
        return False, "Empresa não encontrada.", []
    empresa = empresas[empresa_id]
    if empresa["dono"] != str(dono_id):
        func = empresa["funcionarios"].get(str(dono_id), {})
        if "pagar" not in func.get("permissoes", []):
            return False, "Sem permissão para pagar salários.", []
    total = sum(f["salario"] for f in empresa["funcionarios"].values() if f["salario"] > 0)
    if empresa["saldo"] < total:
        return False, f"Saldo insuficiente. Precisam de {total} moedas, empresa tem {empresa['saldo']}.", []
    pagos = []
    for uid, func in empresa["funcionarios"].items():
        if func["salario"] > 0:
            user = get_user(int(uid))
            user["moedas"] += func["salario"]
            reg = {"tipo": "salario", "valor": func["salario"], "de": empresa["nome"], "data": datetime.utcnow().isoformat()}
            user.setdefault("historico_financeiro", []).append(reg)
            save_user(int(uid), user)
            pagos.append({"uid": uid, "cargo": func["cargo"], "valor": func["salario"]})
    empresa["saldo"] -= total
    empresa["historico"].append({"tipo": "pagamento_salarios", "total": total, "data": datetime.utcnow().isoformat()})
    save_empresas(empresas)
    return True, f"Salários pagos! Total: {total} moedas.", pagos

def depositar_empresa(empresa_id: str, user_id: int, valor: int) -> tuple[bool, str]:
    empresas = get_empresas()
    if empresa_id not in empresas:
        return False, "Empresa não encontrada."
    user = get_user(user_id)
    if user["moedas"] < valor:
        return False, "Moedas insuficientes."
    user["moedas"] -= valor
    empresas[empresa_id]["saldo"] += valor
    save_user(user_id, user)
    save_empresas(empresas)
    return True, f"{valor} moedas depositadas no caixa da empresa."

# ─────────────────────────────────────────────
# FAMÍLIAS / MÁFIAS
# ─────────────────────────────────────────────

def get_familias() -> dict:
    return _load(FAMILIAS_FILE)

def save_familias(data: dict):
    _save(FAMILIAS_FILE, data)

def criar_familia(lider_id: int, nome: str, tipo: str) -> tuple[bool, str]:
    familias = get_familias()
    user = get_user(lider_id)
    if user.get("familia_id"):
        return False, "Você já pertence a uma família/máfia."
    for fid, f in familias.items():
        if f["nome"].lower() == nome.lower():
            return False, "Já existe uma organização com esse nome."
    custo = 300
    if user["moedas"] < custo:
        return False, f"Fundar uma organização custa {custo} moedas."
    fid = str(uuid.uuid4())[:8]
    familias[fid] = {
        "nome": nome,
        "tipo": tipo,  # familia | mafia | clã
        "lider": str(lider_id),
        "pontos": 0,
        "saldo": 0,
        "membros": {
            str(lider_id): {
                "cargo": "Patriarca" if tipo == "familia" else "Don" if tipo == "mafia" else "Líder",
                "data_entrada": datetime.utcnow().isoformat(),
            }
        },
        "fundada": datetime.utcnow().isoformat(),
        "missoes_completas": 0,
    }
    user["moedas"] -= custo
    user["familia_id"] = fid
    user["cargo_familia"] = familias[fid]["membros"][str(lider_id)]["cargo"]
    save_user(lider_id, user)
    save_familias(familias)
    return True, fid

def entrar_familia(user_id: int, familia_id: str) -> tuple[bool, str]:
    familias = get_familias()
    user = get_user(user_id)
    if user.get("familia_id"):
        return False, "Você já pertence a uma organização."
    if familia_id not in familias:
        return False, "Organização não encontrada."
    familia = familias[familia_id]
    tipo = familia["tipo"]
    cargo = "Membro" if tipo == "familia" else "Soldado" if tipo == "mafia" else "Associado"
    familia["membros"][str(user_id)] = {
        "cargo": cargo,
        "data_entrada": datetime.utcnow().isoformat(),
    }
    user["familia_id"] = familia_id
    user["cargo_familia"] = cargo
    save_user(user_id, user)
    save_familias(familias)
    return True, cargo

# ─────────────────────────────────────────────
# BANCO / FINANCEIRO
# ─────────────────────────────────────────────

def transferir(de_id: int, para_id: int, valor: int) -> tuple[bool, str]:
    de = get_user(de_id)
    para = get_user(para_id)
    total_de = de["moedas"] + de.get("conta_banco", 0)
    if de["moedas"] < valor:
        return False, f"Moedas insuficientes. Você tem {de['moedas']} moedas em mãos."
    de["moedas"] -= valor
    para["moedas"] += valor
    reg_de = {"tipo": "transferencia_saida", "valor": valor, "para": str(para_id), "data": datetime.utcnow().isoformat()}
    reg_para = {"tipo": "transferencia_entrada", "valor": valor, "de": str(de_id), "data": datetime.utcnow().isoformat()}
    de.setdefault("historico_financeiro", []).append(reg_de)
    para.setdefault("historico_financeiro", []).append(reg_para)
    save_user(de_id, de)
    save_user(para_id, para)
    return True, "Transferência realizada!"

def depositar_banco(user_id: int, valor: int) -> tuple[bool, str]:
    user = get_user(user_id)
    if user["moedas"] < valor:
        return False, "Moedas insuficientes."
    user["moedas"] -= valor
    user["conta_banco"] = user.get("conta_banco", 0) + valor
    reg = {"tipo": "deposito", "valor": valor, "data": datetime.utcnow().isoformat()}
    user.setdefault("historico_financeiro", []).append(reg)
    save_user(user_id, user)
    return True, f"{valor} moedas depositadas no banco."

def sacar_banco(user_id: int, valor: int) -> tuple[bool, str]:
    user = get_user(user_id)
    saldo = user.get("conta_banco", 0)
    if saldo < valor:
        return False, f"Saldo bancário insuficiente. Você tem {saldo} no banco."
    user["conta_banco"] = saldo - valor
    user["moedas"] += valor
    reg = {"tipo": "saque", "valor": valor, "data": datetime.utcnow().isoformat()}
    user.setdefault("historico_financeiro", []).append(reg)
    save_user(user_id, user)
    return True, f"{valor} moedas sacadas."

def pedir_emprestimo(user_id: int, valor: int) -> tuple[bool, str]:
    user = get_user(user_id)
    emprestimos = user.get("emprestimos", [])
    divida_total = sum(e["valor_restante"] for e in emprestimos)
    if divida_total > 500:
        return False, f"Você já tem {divida_total} moedas de dívida. Quite antes de pedir mais."
    if valor > 1000:
        return False, "Empréstimos acima de 1000 moedas não são liberados pelo Banco Imperial."
    taxa = int(valor * 0.2)
    emprestimos.append({
        "valor_original": valor,
        "valor_restante": valor + taxa,
        "taxa": taxa,
        "data": datetime.utcnow().isoformat(),
    })
    user["emprestimos"] = emprestimos
    user["moedas"] += valor
    reg = {"tipo": "emprestimo", "valor": valor, "data": datetime.utcnow().isoformat()}
    user.setdefault("historico_financeiro", []).append(reg)
    save_user(user_id, user)
    return True, f"Empréstimo de {valor} moedas concedido. Dívida total: {valor + taxa} (20% de juros)."

def pagar_emprestimo(user_id: int, valor: int) -> tuple[bool, str]:
    user = get_user(user_id)
    emprestimos = user.get("emprestimos", [])
    if not emprestimos:
        return False, "Você não possui empréstimos ativos."
    if user["moedas"] < valor:
        return False, "Moedas insuficientes."
    restante = valor
    novos = []
    for e in emprestimos:
        if restante <= 0:
            novos.append(e)
        elif restante >= e["valor_restante"]:
            restante -= e["valor_restante"]
            e["valor_restante"] = 0
        else:
            e["valor_restante"] -= restante
            restante = 0
            novos.append(e)
    user["emprestimos"] = novos
    user["moedas"] -= valor
    reg = {"tipo": "pagamento_emprestimo", "valor": valor, "data": datetime.utcnow().isoformat()}
    user.setdefault("historico_financeiro", []).append(reg)
    save_user(user_id, user)
    return True, f"{valor} moedas pagas. Dívida restante: {sum(e['valor_restante'] for e in novos)}."

# ─────────────────────────────────────────────
# LOJA
# ─────────────────────────────────────────────

LOJA_ITEMS = [
    {"id": "espada_imperial", "nome": "Espada Imperial", "preco": 200, "tipo": "arma", "bonus_poder": 50, "descricao": "Forjada nas chamas eternas do trono."},
    {"id": "pocao_forca", "nome": "Poção de Força", "preco": 80, "tipo": "pocao", "bonus_poder": 20, "descricao": "Eleva seu poder temporariamente."},
    {"id": "manto_sombrio", "nome": "Manto Sombrio", "preco": 150, "tipo": "armadura", "bonus_poder": 30, "descricao": "Tecido com fios de noite pura."},
    {"id": "titulo_senhor", "nome": "Título: Senhor das Sombras", "preco": 500, "tipo": "titulo", "bonus_poder": 0, "descricao": "Um título que ressoa com autoridade."},
    {"id": "amuleto_tarot", "nome": "Amuleto do Tarot", "preco": 120, "tipo": "amuleto", "bonus_poder": 10, "descricao": "Amplifica os poderes místicos das cartas."},
    {"id": "runa_ancia", "nome": "Runa Anciã", "preco": 300, "tipo": "runa", "bonus_poder": 80, "descricao": "Uma runa de poder incalculável das eras antigas."},
    {"id": "distintivo_mafia", "nome": "Distintivo da Máfia", "preco": 400, "tipo": "titulo", "bonus_poder": 40, "descricao": "Marca de respeito no submundo de Tenshi."},
    {"id": "alianca_familia", "nome": "Aliança da Família", "preco": 350, "tipo": "amuleto", "bonus_poder": 35, "descricao": "Símbolo de lealdade inabalável ao clã."},
    {"id": "pasta_executivo", "nome": "Pasta Executiva", "preco": 250, "tipo": "acessorio", "bonus_poder": 15, "descricao": "O poder nos negócios da Tenshi Enterprise."},
]

# ─────────────────────────────────────────────
# FACÇÕES
# ─────────────────────────────────────────────

FACCOES_FILE    = "data/faccoes.json"
VIZINHANCA_FILE = "data/vizinhanca.json"

def get_faccoes() -> dict:
    if not os.path.exists(FACCOES_FILE):
        faccoes = {
            "Guarda Imperial": {"pontos": 0, "membros": [], "descricao": "Os guardiões do Império, mestres do combate nas fronteiras."},
            "Corte de Tenshi": {"pontos": 0, "membros": [], "descricao": "A nobreza política, arquitetos do poder e da intriga palaciana."},
            "Ordem Esotérica": {"pontos": 0, "membros": [], "descricao": "Os místicos e magos, guardiões dos segredos antigos de Tenshi."},
        }
        _save(FACCOES_FILE, faccoes)
        return faccoes
    return _load(FACCOES_FILE)

def _save_faccoes(data: dict):
    _save(FACCOES_FILE, data)

def add_membro_faccao(user_id: int, faccao: str) -> bool:
    faccoes = get_faccoes()
    uid = str(user_id)
    if faccao not in faccoes:
        return False
    for f in faccoes.values():
        if uid in f["membros"]:
            f["membros"].remove(uid)
    faccoes[faccao]["membros"].append(uid)
    _save_faccoes(faccoes)
    return True

def add_pontos_faccao(faccao: str, pontos: int):
    faccoes = get_faccoes()
    if faccao in faccoes:
        faccoes[faccao]["pontos"] += pontos
        _save_faccoes(faccoes)

# ─────────────────────────────────────────────
# VIZINHANÇA / CONDOMÍNIO
# ─────────────────────────────────────────────

def get_vizinhanca() -> dict:
    dados = _load(VIZINHANCA_FILE)
    if not dados:
        dados = {}
        from datetime import datetime
        for n in range(1, 19):
            dados[str(n)] = {
                "numero": n,
                "nome": f"Casa-{n}",
                "id_canal": None,
                "id_dono": None,
                "lista_moradores": [],
                "status_aluguel": "disponivel",
                "data_aquisicao": None,
                "ultima_cobranca": None,
            }
        _save(VIZINHANCA_FILE, dados)
    else:
        for n in range(1, 19):
            chave = str(n)
            if chave not in dados:
                dados[chave] = {
                    "numero": n,
                    "nome": f"Casa-{n}",
                    "id_canal": None,
                    "id_dono": None,
                    "lista_moradores": [],
                    "status_aluguel": "disponivel",
                    "data_aquisicao": None,
                    "ultima_cobranca": None,
                }
        _save(VIZINHANCA_FILE, dados)
    return dados

def save_vizinhanca(data: dict):
    _save(VIZINHANCA_FILE, data)

def registrar_casa_canal(numero: int, canal_id: str):
    dados = get_vizinhanca()
    chave = str(numero)
    if chave in dados:
        dados[chave]["id_canal"] = canal_id
        _save(VIZINHANCA_FILE, dados)

def get_casa_by_canal(canal_id: str) -> dict | None:
    dados = get_vizinhanca()
    for chave, casa in dados.items():
        if str(casa.get("id_canal", "")) == str(canal_id):
            return casa
    return None

# ─────────────────────────────────────────────
# CASAMENTOS
# ─────────────────────────────────────────────

def get_casamentos() -> dict:
    return _load(CASAMENTOS_FILE)

def save_casamentos(data: dict):
    _save(CASAMENTOS_FILE, data)


# ─────────────────────────────────────────────
# INFRAÇÕES / WARNS
# ─────────────────────────────────────────────

def registrar_infracao(user_id: int, tipo: str, descricao: str, moderador: str = "Sistema_IA") -> str:
    dados = _load(INFRACOES_FILE)
    uid   = str(user_id)
    if uid not in dados:
        dados[uid] = []
    inf_id = str(uuid.uuid4())[:8]
    dados[uid].append({
        "id":         inf_id,
        "tipo":       tipo,
        "artigo":     tipo,
        "descricao":  descricao[:300],
        "data_hora":  datetime.utcnow().isoformat(),
        "moderador":  moderador,
    })
    _save(INFRACOES_FILE, dados)
    return inf_id

def get_infrações(user_id: int) -> list:
    dados = _load(INFRACOES_FILE)
    return dados.get(str(user_id), [])

def remover_infracao(user_id: int, inf_id: str) -> bool:
    dados = _load(INFRACOES_FILE)
    uid   = str(user_id)
    if uid not in dados:
        return False
    antes = len(dados[uid])
    dados[uid] = [i for i in dados[uid] if i.get("id") != inf_id]
    _save(INFRACOES_FILE, dados)
    return len(dados[uid]) < antes


# ─────────────────────────────────────────────
# INTERNADOS (hospital)
# ─────────────────────────────────────────────

def get_internados() -> dict:
    return _load(INTERNADOS_FILE)

def save_internados(data: dict):
    _save(INTERNADOS_FILE, data)


def cobrar_condominio_semanal() -> list[dict]:
    """Cobra taxa semanal de todas as casas. Retorna lista de despejados."""
    from datetime import datetime
    dados = get_vizinhanca()
    despejados = []
    TAXA = 50
    for chave, casa in dados.items():
        dono_id = casa.get("id_dono")
        if not dono_id:
            continue
        ultima = casa.get("ultima_cobranca")
        if ultima:
            diff = (datetime.utcnow() - datetime.fromisoformat(ultima)).total_seconds()
            if diff < 6 * 24 * 3600:
                continue
        user = get_user(int(dono_id))
        total = user.get("moedas", 0) + user.get("conta_banco", 0)
        if total >= TAXA:
            if user["moedas"] >= TAXA:
                user["moedas"] -= TAXA
            else:
                resto = TAXA - user["moedas"]
                user["moedas"] = 0
                user["conta_banco"] = user.get("conta_banco", 0) - resto
            casa["ultima_cobranca"] = datetime.utcnow().isoformat()
            save_user(int(dono_id), user)
        else:
            despejados.append({"casa": int(chave), "dono_id": dono_id, "dados": dict(casa)})
            n = int(chave)
            dados[chave] = {
                "numero": n, "nome": f"Casa-{n}",
                "id_canal": casa.get("id_canal"),
                "id_dono": None, "lista_moradores": [],
                "status_aluguel": "disponivel",
                "data_aquisicao": None, "ultima_cobranca": None,
            }
            user["casa_condominio"] = None
            save_user(int(dono_id), user)
    _save(VIZINHANCA_FILE, dados)
    return despejados
