"""
Motor Central de IA — Roteamento Inteligente por Modelo
Cada função do bot usa o modelo mais adequado para o tipo de tarefa.
"""
import os
import asyncio
from groq import Groq

# ══════════════════════════════════════════════════════════════════════════════
# MAPA DE MODELOS & CHAVES
# ══════════════════════════════════════════════════════════════════════════════
_MODELOS = {
    # Narrativa épica, roleplay imersivo, crônicas — mais criativo e fluente
    "llama4_maverick": {
        "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "key_env": "GROQ_KEY_LLAMA4_MAVERICK",
        "fallback": "llama3_70b",
    },
    # Raciocínio rápido, respostas curtas, moderação, triagem
    "llama4_scout": {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "key_env": "GROQ_KEY_LLAMA4_SCOUT",
        "fallback": "llama3_70b",
    },
    # Análise profunda, jurídico, estratégia, exames acadêmicos
    "llama3_70b": {
        "model": "llama-3.3-70b-versatile",
        "key_env": "GROQ_KEY_LLAMA3_70B",
        "fallback": "mixtral",
    },
    # Contexto longo, econômico, relatórios, auditorias
    "mixtral": {
        "model": "mixtral-8x7b-32768",
        "key_env": "GROQ_KEY_MIXTRAL",
        "fallback": "gemma2",
    },
    # Respostas rápidas, NPCs simples, clima, dados curtos
    "gemma2": {
        "model": "gemma2-9b-it",
        "key_env": "GROQ_KEY_GEMMA2",
        "fallback": "llama3_70b",
    },
    # Raciocínio avançado, geopolítica, soberania, decretos
    "gpt120b": {
        "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "key_env": "GROQ_KEY_GPT120B",
        "fallback": "llama4_maverick",
    },
    # Tarefas rápidas, economia, transações simples
    "gpt20b": {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "key_env": "GROQ_KEY_GPT20B",
        "fallback": "llama4_scout",
    },
}

# Chave principal de fallback global
_KEY_GLOBAL = os.environ.get("GROQ_API_KEY")

# Cache de clientes Groq inicializados
_clientes: dict = {}

def _get_cliente(modelo_key: str) -> tuple:
    """Retorna (client, model_name) para o modelo solicitado, com fallback."""
    if modelo_key in _clientes:
        return _clientes[modelo_key]

    cfg = _MODELOS.get(modelo_key)
    if not cfg:
        return _get_fallback_global()

    api_key = os.environ.get(cfg["key_env"]) or _KEY_GLOBAL
    if not api_key:
        fallback = cfg.get("fallback")
        if fallback:
            return _get_cliente(fallback)
        return _get_fallback_global()

    try:
        client = Groq(api_key=api_key)
        result = (client, cfg["model"])
        _clientes[modelo_key] = result
        return result
    except Exception:
        fallback = cfg.get("fallback")
        if fallback:
            return _get_cliente(fallback)
        return _get_fallback_global()


def _get_fallback_global():
    """Fallback final usando GROQ_API_KEY com llama3-70b."""
    if not _KEY_GLOBAL:
        return (None, None)
    try:
        client = Groq(api_key=_KEY_GLOBAL)
        return (client, "llama-3.3-70b-versatile")
    except Exception:
        return (None, None)


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL DE CHAMADA
# ══════════════════════════════════════════════════════════════════════════════
async def chamar_ia(
    sistema: str,
    usuario: str,
    modelo: str = "llama3_70b",
    max_tokens: int = 900,
    temperature: float = 0.8,
) -> str:
    """
    Chama a IA de forma assíncrona com o modelo indicado.
    Em caso de erro, tenta fallback automaticamente.

    Parâmetros:
        sistema: prompt de sistema (personalidade/regras)
        usuario: mensagem/contexto do usuário
        modelo: chave do modelo (ver _MODELOS acima)
        max_tokens: limite de tokens na resposta
        temperature: criatividade (0.0 = determinístico, 1.0 = criativo)
    """
    client, model_name = _get_cliente(modelo)
    if not client:
        return "⚠️ *A IA está temporariamente indisponível. Configure as chaves nos secrets.*"

    def _sync():
        return client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user",   "content": usuario},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        ).choices[0].message.content.strip()

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _sync)
    except Exception as e:
        # Tenta fallback do modelo
        cfg = _MODELOS.get(modelo, {})
        fallback = cfg.get("fallback")
        if fallback and fallback != modelo:
            return await chamar_ia(sistema, usuario, fallback, max_tokens, temperature)
        return f"⚠️ *Erro na IA ({model_name}): {str(e)[:100]}*"


# ══════════════════════════════════════════════════════════════════════════════
# ATALHOS SEMÂNTICOS — use estes nos cogs
# ══════════════════════════════════════════════════════════════════════════════

async def ia_narrativa(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    """Narrativa épica, crônicas, roleplay imersivo — LLaMA 4 Maverick."""
    return await chamar_ia(sistema, usuario, "llama4_maverick", max_tokens, 0.9)

async def ia_rapida(sistema: str, usuario: str, max_tokens: int = 400) -> str:
    """Respostas rápidas, NPCs, clima, triagem — LLaMA 4 Scout."""
    return await chamar_ia(sistema, usuario, "llama4_scout", max_tokens, 0.7)

async def ia_analitica(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    """Análise profunda, jurídico, estratégia, exames — LLaMA 3 70B."""
    return await chamar_ia(sistema, usuario, "llama3_70b", max_tokens, 0.75)

async def ia_relatorio(sistema: str, usuario: str, max_tokens: int = 1200) -> str:
    """Relatórios longos, auditorias, economia, RH — Mixtral 8x7b."""
    return await chamar_ia(sistema, usuario, "mixtral", max_tokens, 0.6)

async def ia_soberana(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    """Decretos, geopolítica, soberania — GPT-OSS-120b / Maverick."""
    return await chamar_ia(sistema, usuario, "gpt120b", max_tokens, 0.8)

async def ia_economia(sistema: str, usuario: str, max_tokens: int = 600) -> str:
    """Economia, transações, cálculos — GPT-OSS-20b / Scout."""
    return await chamar_ia(sistema, usuario, "gpt20b", max_tokens, 0.5)

async def ia_npc(sistema: str, usuario: str, max_tokens: int = 350) -> str:
    """NPCs simples, respostas curtas, clima — Gemma 2 9B."""
    return await chamar_ia(sistema, usuario, "gemma2", max_tokens, 0.85)


# ══════════════════════════════════════════════════════════════════════════════
# DIAGNÓSTICO — chamado por "Tenshi, status-ia"
# ══════════════════════════════════════════════════════════════════════════════
def status_motores() -> dict:
    """Retorna quais motores estão com chave configurada."""
    resultado = {}
    for key, cfg in _MODELOS.items():
        tem_chave = bool(os.environ.get(cfg["key_env"]) or _KEY_GLOBAL)
        resultado[key] = {
            "modelo": cfg["model"],
            "ativo": tem_chave,
        }
    return resultado
