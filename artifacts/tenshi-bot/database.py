import json
import os
import asyncio
from datetime import datetime

DB_FILE = "data/db.json"

_lock = asyncio.Lock()

def _load() -> dict:
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _save(data: dict):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id: int) -> dict:
    data = _load()
    uid = str(user_id)
    if uid not in data:
        data[uid] = _default_user()
        _save(data)
    return data[uid]

def save_user(user_id: int, user_data: dict):
    data = _load()
    data[str(user_id)] = user_data
    _save(data)

def get_all_users() -> dict:
    return _load()

def _default_user() -> dict:
    return {
        "nome": None,
        "titulo": "Cidadão do Império",
        "nivel": 1,
        "xp": 0,
        "poder": 100,
        "moedas": 50,
        "inventario": [],
        "faccao": None,
        "faccao_pontos": 0,
        "ultimo_treino": None,
        "ultima_missao": None,
        "ultimo_tarot": None,
        "ultimo_duelo": None,
        "vitorias_duelo": 0,
        "derrotas_duelo": 0,
        "status_bonus": {},
    }

# Facções
FACCOES_FILE = "data/faccoes.json"

def get_faccoes() -> dict:
    if not os.path.exists(FACCOES_FILE):
        faccoes = {
            "Guarda Imperial": {"pontos": 0, "membros": [], "descricao": "Os guardiões do Império, mestres do combate nas fronteiras."},
            "Corte de Tenshi": {"pontos": 0, "membros": [], "descricao": "A nobreza política, arquitetos do poder e da intriga palaciana."},
            "Ordem Esotérica": {"pontos": 0, "membros": [], "descricao": "Os místicos e magos, guardiões dos segredos antigos de Tenshi."},
        }
        _save_faccoes(faccoes)
        return faccoes
    with open(FACCOES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_faccoes(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(FACCOES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

# Loja
LOJA_ITEMS = [
    {"id": "espada_imperial", "nome": "Espada Imperial", "preco": 200, "tipo": "arma", "bonus_poder": 50, "descricao": "Forjada nas chamas eternas do trono."},
    {"id": "pocao_forca", "nome": "Poção de Força", "preco": 80, "tipo": "pocao", "bonus_poder": 20, "descricao": "Eleva seu poder temporariamente."},
    {"id": "manto_sombrio", "nome": "Manto Sombrio", "preco": 150, "tipo": "armadura", "bonus_poder": 30, "descricao": "Tecido com fios de noite pura."},
    {"id": "titulo_senhor", "nome": "Título: Senhor das Sombras", "preco": 500, "tipo": "titulo", "bonus_poder": 0, "descricao": "Um título que ressoa com autoridade."},
    {"id": "amuleto_tarot", "nome": "Amuleto do Tarot", "preco": 120, "tipo": "amuleto", "bonus_poder": 10, "descricao": "Amplifica os poderes místicos das cartas."},
    {"id": "runa_anciã", "nome": "Runa Anciã", "preco": 300, "tipo": "runa", "bonus_poder": 80, "descricao": "Uma runa de poder incalculável das eras antigas."},
]
