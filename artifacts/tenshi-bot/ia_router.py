"""
Motor central de IA via OpenRouter.

Configure a chave em OPENROUTER_API_KEY no ambiente da hospedagem.
"""
import os
import aiohttp
from lei_imperial import prompt_lei_imperial


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
APP_TITLE = os.environ.get("OPENROUTER_APP_TITLE", "Tenshi Bot")
APP_URL = os.environ.get("OPENROUTER_APP_URL", "")


_MODELOS = {
    "narrativa": {
        "model": os.environ.get("OPENROUTER_MODEL_NARRATIVA", "meta-llama/llama-3.1-70b-instruct"),
        "fallback": "analitica",
    },
    "rapida": {
        "model": os.environ.get("OPENROUTER_MODEL_RAPIDA", "meta-llama/llama-3.1-8b-instruct"),
        "fallback": "analitica",
    },
    "analitica": {
        "model": os.environ.get("OPENROUTER_MODEL_ANALITICA", "openai/gpt-4o-mini"),
        "fallback": None,
    },
    "relatorio": {
        "model": os.environ.get("OPENROUTER_MODEL_RELATORIO", "google/gemini-flash-1.5"),
        "fallback": "analitica",
    },
    "soberana": {
        "model": os.environ.get("OPENROUTER_MODEL_SOBERANA", "anthropic/claude-3.5-sonnet"),
        "fallback": "analitica",
    },
    "economia": {
        "model": os.environ.get("OPENROUTER_MODEL_ECONOMIA", "openai/gpt-4o-mini"),
        "fallback": "analitica",
    },
    "npc": {
        "model": os.environ.get("OPENROUTER_MODEL_NPC", "meta-llama/llama-3.1-8b-instruct"),
        "fallback": "rapida",
    },
}

_ALIASES = {
    "llama4_maverick": "narrativa",
    "llama4_scout": "rapida",
    "llama3_70b": "analitica",
    "mixtral": "relatorio",
    "gemma2": "npc",
    "gpt120b": "soberana",
    "gpt20b": "economia",
}


def _api_key() -> str | None:
    return os.environ.get("OPENROUTER_API_KEY")


def _headers(api_key: str) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if APP_TITLE:
        headers["X-Title"] = APP_TITLE
    if APP_URL:
        headers["HTTP-Referer"] = APP_URL
    return headers


def _modelo_cfg(modelo: str) -> tuple[str, dict]:
    key = _ALIASES.get(modelo, modelo)
    cfg = _MODELOS.get(key) or _MODELOS["analitica"]
    return key, cfg


def _sistema_com_lei(sistema: str) -> str:
    if os.environ.get("TENSHI_LEGAL_GUARD", "1").strip().lower() in {"0", "false", "nao", "não", "off"}:
        return sistema
    return f"{prompt_lei_imperial()}\n\nInstrucao especifica do modulo:\n{sistema}"


async def chamar_ia(
    sistema: str,
    usuario: str,
    modelo: str = "analitica",
    max_tokens: int = 900,
    temperature: float = 0.8,
) -> str:
    """
    Chama a IA de forma assíncrona pelo OpenRouter.

    Parâmetros:
        sistema: prompt de sistema
        usuario: mensagem/contexto do usuário
        modelo: chave semântica do modelo
        max_tokens: limite de tokens na resposta
        temperature: criatividade
    """
    api_key = _api_key()
    if not api_key:
        return "⚠️ *A IA está indisponível. Configure OPENROUTER_API_KEY no ambiente.*"

    modelo_key, cfg = _modelo_cfg(modelo)
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": _sistema_com_lei(sistema)},
            {"role": "user", "content": usuario},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(OPENROUTER_URL, headers=_headers(api_key), json=payload) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    detail = data.get("error", data)
                    raise RuntimeError(str(detail)[:180])
                return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        fallback = cfg.get("fallback")
        if fallback and fallback != modelo_key:
            return await chamar_ia(sistema, usuario, fallback, max_tokens, temperature)
        return f"⚠️ *Erro na IA OpenRouter ({cfg['model']}): {str(exc)[:120]}*"


async def ia_narrativa(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    return await chamar_ia(sistema, usuario, "narrativa", max_tokens, 0.9)


async def ia_rapida(sistema: str, usuario: str, max_tokens: int = 400) -> str:
    return await chamar_ia(sistema, usuario, "rapida", max_tokens, 0.7)


async def ia_analitica(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    return await chamar_ia(sistema, usuario, "analitica", max_tokens, 0.75)


async def ia_relatorio(sistema: str, usuario: str, max_tokens: int = 1200) -> str:
    return await chamar_ia(sistema, usuario, "relatorio", max_tokens, 0.6)


async def ia_soberana(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    return await chamar_ia(sistema, usuario, "soberana", max_tokens, 0.8)


async def ia_economia(sistema: str, usuario: str, max_tokens: int = 600) -> str:
    return await chamar_ia(sistema, usuario, "economia", max_tokens, 0.5)


async def ia_npc(sistema: str, usuario: str, max_tokens: int = 350) -> str:
    return await chamar_ia(sistema, usuario, "npc", max_tokens, 0.85)


def status_motores() -> dict:
    """Retorna os motores OpenRouter configurados."""
    tem_chave = bool(_api_key())
    return {
        key: {
            "modelo": cfg["model"],
            "ativo": tem_chave,
        }
        for key, cfg in _MODELOS.items()
    }
