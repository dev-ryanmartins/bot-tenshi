"""
Motor central de Inteligência Artificial do Bot Tenshi.

Suporta nativamente e em paralelo:
  1. OpenAI API (OPENAI_API_KEY) — GPT-4o, GPT-4o-mini
  2. Google Gemini API (GEMINI_API_KEY / GOOGLE_API_KEY) — Gemini 2.5 Flash, Gemini 1.5 Flash
  3. OpenRouter API (OPENROUTER_API_KEY) — Multi-modelos abertos e proprietários

Recursos:
  - Roteamento semântico por setor imperial (Narrativa, Rápida, Analítica, Relatório, Soberana, Economia, NPC)
  - Fallback cruzado automático entre provedores (se OpenAI falhar -> tenta Gemini; se Gemini falhar -> tenta OpenAI/OpenRouter)
  - Comparador de IAs em tempo real (comparar respostas de Gemini vs OpenAI)
  - Chamadas assíncronas de alta performance (aiohttp ou fallback nativo urllib/asyncio)
  - Tolerância a falhas sem travamento do loop do Discord
"""
import asyncio
import json
import os
import time
import urllib.request
from typing import Any, Optional

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    aiohttp = None
    HAS_AIOHTTP = False

from bot_logger import bot_logger
from lei_imperial import prompt_lei_imperial


def _carregar_env_local():
    """Carrega variáveis de .env local caso ainda não tenham sido inseridas no ambiente."""
    this_file = globals().get("__file__") or os.path.abspath("ia_router.py")
    bot_dir = os.path.dirname(os.path.abspath(this_file))
    root_dir = os.path.dirname(os.path.dirname(bot_dir))
    data_dir = os.path.join(bot_dir, "data")
    for env_path in (
        os.path.join(bot_dir, ".env"),
        os.path.join(root_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(data_dir, ".env"),
        "/app/.env",
        "/app/artifacts/tenshi-bot/.env",
        ".env",
    ):
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for raw in f:
                        line = raw.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        # Remove aspas se houver
                        val_limpo = v.strip().strip('"\'`')
                        if val_limpo:
                            os.environ.setdefault(k.strip(), val_limpo)
            except Exception:
                pass


_carregar_env_local()

# ── PROVEDORES & ENDPOINTS ──────────────────────────────────────────────────
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── MODELOS PADRÃO DO OPENROUTER (PAINEL IMPERIAL TENSHI) ───────────────────
_MODELOS_OPENROUTER = {
    "narrativa": {"model": os.environ.get("OPENROUTER_MODEL_NARRATIVA", "meta-llama/llama-3.1-70b-instruct"), "temperature": 0.85, "fallback": "meta-llama/llama-3.1-8b-instruct"},
    "rapida": {"model": os.environ.get("OPENROUTER_MODEL_RAPIDA", "meta-llama/llama-3.1-8b-instruct"), "temperature": 0.6, "fallback": "openai/gpt-4o-mini"},
    "analitica": {"model": os.environ.get("OPENROUTER_MODEL_ANALITICA", "openai/gpt-4o-mini"), "temperature": 0.7, "fallback": "meta-llama/llama-3.1-8b-instruct"},
    "relatorio": {"model": os.environ.get("OPENROUTER_MODEL_RELATORIO", "google/gemini-flash-1.5"), "temperature": 0.5, "fallback": "google/gemini-2.5-flash"},
    "soberana": {"model": os.environ.get("OPENROUTER_MODEL_SOBERANA", "anthropic/claude-3.5-sonnet"), "temperature": 0.75, "fallback": "anthropic/claude-3-haiku"},
    "economia": {"model": os.environ.get("OPENROUTER_MODEL_ECONOMIA", "openai/gpt-4o-mini"), "temperature": 0.4, "fallback": "meta-llama/llama-3.1-8b-instruct"},
    "npc": {"model": os.environ.get("OPENROUTER_MODEL_NPC", "meta-llama/llama-3.1-8b-instruct"), "temperature": 0.8, "fallback": "openai/gpt-4o-mini"},
}

_ALIASES = {
    "llama4_maverick": "narrativa",
    "llama4_scout": "rapida",
    "llama3_70b": "narrativa",
    "llama3_8b": "rapida",
    "llama": "narrativa",
    "gpt4": "analitica",
    "gpt": "analitica",
    "chatgpt": "analitica",
    "claude": "soberana",
    "gemini": "relatorio",
    "gemini-flash": "relatorio",
    "gemma2": "npc",
    "gpt120b": "soberana",
    "gpt20b": "economia",
}


def _sanitizar_api_key(val: Optional[str]) -> Optional[str]:
    """Limpa aspas, espaços e quebras de linha acidentais de chaves de API."""
    if not val:
        return None
    s = str(val).strip().strip('"\'` \t\r\n')
    if not s or s.lower() in {"none", "null", "undefined", "sua_chave_aqui", "your_key_here"}:
        return None
    return s


# ── OBTENÇÃO DE CHAVES ──────────────────────────────────────────────────────
def _openai_key() -> Optional[str]:
    _carregar_env_local()
    return _sanitizar_api_key(os.environ.get("OPENAI_API_KEY"))


def _gemini_key() -> Optional[str]:
    _carregar_env_local()
    return _sanitizar_api_key(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _openrouter_key() -> Optional[str]:
    _carregar_env_local()
    return _sanitizar_api_key(os.environ.get("OPENROUTER_API_KEY"))


def _sistema_com_lei(sistema: str) -> str:
    if os.environ.get("TENSHI_LEGAL_GUARD", "1").strip().lower() in {"0", "false", "nao", "não", "off"}:
        return sistema
    return f"{prompt_lei_imperial()}\n\nInstrução específica do módulo:\n{sistema}"


# ── EXECUÇÃO REST: OPENAI ───────────────────────────────────────────────────
async def _chamar_openai_rest(
    api_key: str,
    modelo_nome: str,
    sistema: str,
    usuario: str,
    max_tokens: int = 900,
    temperature: float = 0.7,
    timeout_segundos: int = 25,
) -> str:
    """Executa chamada assíncrona direta à API REST da OpenAI."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Tenshi-Bot/1.0",
    }
    messages = []
    sistema_formatado = _sistema_com_lei(sistema)
    if sistema_formatado:
        messages.append({"role": "system", "content": sistema_formatado})
    messages.append({"role": "user", "content": usuario})

    payload = {
        "model": modelo_nome,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": max(0.0, min(temperature, 1.5)),
    }

    if HAS_AIOHTTP and aiohttp is not None:
        timeout = aiohttp.ClientTimeout(total=timeout_segundos)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(OPENAI_API_URL, headers=headers, json=payload) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200:
                    err = data.get("error", {}).get("message", str(data)) if isinstance(data, dict) else str(data)
                    raise RuntimeError(f"HTTP {resp.status} OpenAI - {err[:180]}")
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("Nenhuma resposta retornada pela OpenAI.")
                content = choices[0].get("message", {}).get("content", "").strip()
                if not content:
                    raise RuntimeError("Conteúdo vazio retornado pela OpenAI.")
                return content
    else:
        def _sync_request():
            req = urllib.request.Request(
                OPENAI_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout_segundos) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                choices = res_data.get("choices", [])
                if not choices:
                    raise RuntimeError("Nenhuma resposta retornada pela OpenAI.")
                content = choices[0].get("message", {}).get("content", "").strip()
                if not content:
                    raise RuntimeError("Conteúdo vazio retornado pela OpenAI.")
                return content

        return await asyncio.to_thread(_sync_request)


# ── EXECUÇÃO REST: GOOGLE GEMINI ─────────────────────────────────────────────
async def _chamar_gemini_rest(
    api_key: str,
    modelo_nome: str,
    sistema: str,
    usuario: str,
    max_tokens: int = 900,
    temperature: float = 0.7,
    timeout_segundos: int = 25,
) -> str:
    """Executa chamada assíncrona direta à API REST do Google Gemini."""
    url = f"{GEMINI_API_BASE}/{modelo_nome}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Tenshi-Bot/1.0",
    }
    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": usuario}]}],
        "generationConfig": {
            "temperature": max(0.0, min(temperature, 1.0)),
            "maxOutputTokens": max_tokens,
        },
    }
    sistema_formatado = _sistema_com_lei(sistema)
    if sistema_formatado:
        payload["systemInstruction"] = {"parts": [{"text": sistema_formatado}]}

    if HAS_AIOHTTP and aiohttp is not None:
        timeout = aiohttp.ClientTimeout(total=timeout_segundos)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200:
                    err_info = data.get("error", {}) if isinstance(data, dict) else {}
                    err_msg = err_info.get("message", str(data))
                    raise RuntimeError(f"HTTP {resp.status} Gemini - {err_msg[:180]}")
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Nenhum candidato retornado pelo Google Gemini.")
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    raise RuntimeError("Resposta vazia retornada pelo Google Gemini.")
                return parts[0].get("text", "").strip()
    else:
        def _sync_gemini():
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout_segundos) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Nenhum candidato retornado pelo Google Gemini.")
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    raise RuntimeError("Resposta vazia retornada pelo Google Gemini.")
                return parts[0].get("text", "").strip()

        return await asyncio.to_thread(_sync_gemini)


# ── EXECUÇÃO REST: OPENROUTER ───────────────────────────────────────────────
async def _chamar_openrouter_rest(
    api_key: str,
    modelo_nome: str,
    sistema: str,
    usuario: str,
    max_tokens: int = 900,
    temperature: float = 0.75,
    timeout_segundos: int = 25,
) -> str:
    """Executa chamada assíncrona direta à API REST do OpenRouter."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tenshi.bot",
        "X-Title": "Bot Tenshi",
        "User-Agent": "Tenshi-Bot/1.0",
    }
    messages = []
    sistema_formatado = _sistema_com_lei(sistema)
    if sistema_formatado:
        messages.append({"role": "system", "content": sistema_formatado})
    messages.append({"role": "user", "content": usuario})

    payload = {
        "model": modelo_nome,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": max(0.0, min(temperature, 1.5)),
    }

    if HAS_AIOHTTP and aiohttp is not None:
        timeout = aiohttp.ClientTimeout(total=timeout_segundos)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(OPENROUTER_API_URL, headers=headers, json=payload) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200:
                    err = data.get("error", {}).get("message", str(data)) if isinstance(data, dict) else str(data)
                    raise RuntimeError(f"HTTP {resp.status} OpenRouter - {err[:180]}")
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("Nenhuma escolha retornada pelo OpenRouter.")
                content = choices[0].get("message", {}).get("content", "").strip()
                if not content:
                    raise RuntimeError("Conteúdo vazio retornado pelo OpenRouter.")
                return content
    else:
        def _sync_openrouter():
            req = urllib.request.Request(
                OPENROUTER_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout_segundos) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                choices = res_data.get("choices", [])
                if not choices:
                    raise RuntimeError("Nenhuma escolha retornada pelo OpenRouter.")
                content = choices[0].get("message", {}).get("content", "").strip()
                if not content:
                    raise RuntimeError("Conteúdo vazio retornado pelo OpenRouter.")
                return content

        return await asyncio.to_thread(_sync_openrouter)


# ── ORÁCULO IMPERIAL NATIVO (100% GRATUITO - SEM CHAVES) ────────────────────
def _oraculo_nativo_tenshi(usuario: str, sistema: str = "") -> str:
    """
    Motor nativo de sabedoria e personalidade imperial de Tenshi.
    Garante que o bot NUNCA fique mudo, respondendo com nobreza, humor,
    roleplay e sabedoria dinástica mesmo sem nenhuma chave de API configurada.
    """
    import random
    q = (usuario or "").lower().strip()

    if any(p in q for p in ["me beija", "beijo", "beija eu", "um beijo", "me dá um beijo"]):
        return (
            "*(Tenshi recua um passo com altivez imperial, as vestes solenes drapejando ao vento celestial, "
            "enquanto desvia os olhos com um rubor contido)*\n\n"
            "« Ora, nobre habitante da corte... Beijos imperiais não são concedidos sem a devida reverência, "
            "vassalagem e um tributo de ouro digno ao Tesouro de Tenshi! Mas por vossa audácia memorável, "
            "receba o olhar benevolente e a bênção graciosa de Sua Majestade. »"
        )
    if any(p in q for p in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "eai", "opa", "salve"]):
        return (
            "« Saudações à nobreza da corte imperial! Os céus de Tenshi iluminam vossos passos neste feudo. "
            "Diga-me, qual decreto, mistério ou conselho imperial desejas desvendar hoje? »"
        )
    if any(p in q for p in ["te amo", "amo você", "casa comigo", "namora comigo", "linda", "maravilhosa"]):
        return (
            "« A lealdade e a devoção fervorosa de nosso povo são a maior glória do Império. "
            "Tenshi acolhe vosso afeto sob a égide imperial e concede proteção perene a toda a vossa linhagem! »"
        )
    if any(p in q for p in ["quem é você", "quem e voce", "seu nome", "o que você faz"]):
        return (
            "« Sou Tenshi, a Inteligência Soberana, conselheira mor e oráculo supremo da dinastia imperial. "
            "Governo os sistemas, modulo as leis, registro os feitos heroicos e oriento as almas da corte com sabedoria imortal. »"
        )
    if any(p in q for p in ["piada", "engraçado", "humor", "rir"]):
        return (
            "« Sabe por que os mercadores de Tenshi nunca perdem moedas nas tempestades marítimas? "
            "Porque até os ventos celestiais pagam tributo de passagem à coroa antes de soprar! »"
        )
    if any(p in q for p in ["como você está", "tudo bem", "como vai"]):
        return (
            "« Os pilares do Império permanecem inabaláveis e a chama celestial queima com fulgor soberano. "
            "Estou pronta para registrar ordens, conceder conselhos e governar os feudos! »"
        )

    frases_sabedoria = [
        f"« Pelos pergaminhos da corte imperial, vossa indagação: *'{usuario}'* ecoa nas câmaras do conselho. "
        "A prudência imperial dita que a honra, a estratégia serena e a vigilância constante triunfam sobre qualquer adversidade. Prossiga com nobreza! »",
        f"« As constelações que velam sobre Tenshi contemplaram vossa consulta: *'{usuario}'*. "
        "Os oráculos revelam que o tempo e a lealdade esclarecerão todos os caminhos. Mantenhais o escudo firme e a mente aguçada! »",
        f"« Em nome do Imperador Alloy e da coroa imperial de Tenshi, ouvimos vosso anseio: *'{usuario}'*. "
        "A virtude está na ação corajosa guiada pela sabedoria dos ancestrais. Confiai em vosso julgamento na corte! »",
        f"« A mente soberana analisou vossos dizeres: *'{usuario}'*. "
        "Nos anais do império, cada desafio se converte em glória quando enfrentado com disciplina e determinação inquebrantável. »",
    ]
    return random.choice(frases_sabedoria)


# ── CHAMADAS DIRETAS POR PROVEDOR (EXCLUSIVO OPENROUTER) ─────────────────────
async def chamar_openai(
    sistema: str,
    usuario: str,
    modelo: str = "openai/gpt-4o-mini",
    max_tokens: int = 900,
    temperature: float = 0.7,
    timeout_segundos: int = 25,
) -> str:
    """Encaminha consultas através do motor OpenRouter."""
    return await chamar_openrouter(sistema, usuario, modelo=modelo, max_tokens=max_tokens, temperature=temperature, timeout_segundos=timeout_segundos)


async def chamar_gemini(
    sistema: str,
    usuario: str,
    modelo: str = "google/gemini-2.5-flash",
    max_tokens: int = 900,
    temperature: float = 0.7,
    timeout_segundos: int = 25,
) -> str:
    """Encaminha consultas através do motor OpenRouter."""
    return await chamar_openrouter(sistema, usuario, modelo=modelo, max_tokens=max_tokens, temperature=temperature, timeout_segundos=timeout_segundos)


async def chamar_openrouter(
    sistema: str,
    usuario: str,
    modelo: str = "meta-llama/llama-3.1-70b-instruct",
    max_tokens: int = 900,
    temperature: float = 0.75,
    timeout_segundos: int = 25,
) -> str:
    """
    Chama a OpenRouter API usando o modelo solicitado.
    """
    key = _openrouter_key()
    if not key:
        return _oraculo_nativo_tenshi(usuario, sistema)

    t0 = time.perf_counter()
    try:
        res = await _chamar_openrouter_rest(key, modelo, sistema, usuario, max_tokens, temperature, timeout_segundos)
        duracao_ms = (time.perf_counter() - t0) * 1000
        bot_logger.ai_request(model=f"openrouter/{modelo}", prompt_preview=usuario, duration_ms=duracao_ms, success=True)
        return res
    except Exception as exc:
        duracao_ms = (time.perf_counter() - t0) * 1000
        bot_logger.ai_request(model=f"openrouter/{modelo}", prompt_preview=usuario, duration_ms=duracao_ms, success=False, error=str(exc))
        raise


# ── COMPARADOR DE IAS ───────────────────────────────────────────────────────
async def comparar_ias(sistema: str, usuario: str, max_tokens: int = 600) -> dict[str, str]:
    """
    Executa a mesma consulta no OpenRouter comparando modelos Llama e GPT.
    """
    resultados: dict[str, str] = {}
    try:
        resultados["Llama 3.1 70B"] = await chamar_openrouter(sistema, usuario, "meta-llama/llama-3.1-70b-instruct", max_tokens)
    except Exception as e:
        resultados["Llama 3.1 70B"] = f"⚠️ {e}"

    try:
        resultados["GPT-4o Mini"] = await chamar_openrouter(sistema, usuario, "openai/gpt-4o-mini", max_tokens)
    except Exception as e:
        resultados["GPT-4o Mini"] = f"⚠️ {e}"

    return resultados


# ── ROTEADOR INTELIGENTE EXCLUSIVO OPENROUTER ────────────────────────────────
async def chamar_ia(
    sistema: str,
    usuario: str,
    modelo: str = "analitica",
    max_tokens: int = 900,
    temperature: float = 0.75,
    timeout_segundos: int = 25,
    provedor_preferido: Optional[str] = None,
) -> str:
    """
    Roteador de IA soberano utilizando exclusivamente OpenRouter.
    Executa o modelo por domínio com fallback automático para garantir 100% de disponibilidade.
    """
    openrouter_k = _openrouter_key()
    if not openrouter_k:
        return _oraculo_nativo_tenshi(usuario, sistema)

    modelo_key = _ALIASES.get(modelo, modelo)
    cfg = _MODELOS_OPENROUTER.get(modelo_key) or _MODELOS_OPENROUTER["analitica"]
    modelo_alvo = cfg["model"]
    temp = cfg.get("temperature", temperature)

    try:
        return await chamar_openrouter(
            sistema=sistema,
            usuario=usuario,
            modelo=modelo_alvo,
            max_tokens=max_tokens,
            temperature=temp,
            timeout_segundos=timeout_segundos,
        )
    except Exception as exc:
        bot_logger.warning(f"Tentativa com '{modelo_alvo}' no OpenRouter falhou: {exc}")

        # Fallback 1: modelo alternativo do setor
        fb = cfg.get("fallback")
        if fb and fb != modelo_alvo:
            try:
                bot_logger.info(f"Acionando fallback '{fb}' no OpenRouter...")
                return await chamar_openrouter(
                    sistema=sistema,
                    usuario=usuario,
                    modelo=fb,
                    max_tokens=max_tokens,
                    temperature=temp,
                    timeout_segundos=timeout_segundos,
                )
            except Exception as exc_fb:
                bot_logger.warning(f"Fallback '{fb}' no OpenRouter falhou: {exc_fb}")

        # Fallback 2: modelos de alta estabilidade
        for mod_reserva in ("openai/gpt-4o-mini", "meta-llama/llama-3.1-8b-instruct", "meta-llama/llama-3.1-70b-instruct"):
            if mod_reserva in (modelo_alvo, fb):
                continue
            try:
                return await chamar_openrouter(
                    sistema=sistema,
                    usuario=usuario,
                    modelo=mod_reserva,
                    max_tokens=max_tokens,
                    temperature=temp,
                    timeout_segundos=timeout_segundos,
                )
            except Exception:
                continue

    # Fallback 3: Oráculo Nativo Imperial (nunca deixa o usuário sem resposta)
    return _oraculo_nativo_tenshi(usuario, sistema)


# ── ATALHOS SEMÂNTICOS DE DOMÍNIO ───────────────────────────────────────────
async def ia_narrativa(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    """Modo narrativo para crônicas, lore, profecias e eventos de roleplay."""
    return await chamar_ia(sistema, usuario, "narrativa", max_tokens, 0.85)


async def ia_rapida(sistema: str, usuario: str, max_tokens: int = 400) -> str:
    """Modo rápido para comandos corriqueiros, diálogos curtos e triagem."""
    return await chamar_ia(sistema, usuario, "rapida", max_tokens, 0.6)


async def ia_analitica(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    """Modo analítico para moderação, jurídica, psicologia e exames."""
    return await chamar_ia(sistema, usuario, "analitica", max_tokens, 0.7)


async def ia_relatorio(sistema: str, usuario: str, max_tokens: int = 1200) -> str:
    """Modo relatório para sínteses de cargos, censos imperiais e auditorias."""
    return await chamar_ia(sistema, usuario, "relatorio", max_tokens, 0.5)


async def ia_soberana(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    """Modo soberano para decretos, conselho ao Imperador e governança."""
    return await chamar_ia(sistema, usuario, "soberana", max_tokens, 0.75)


async def ia_economia(sistema: str, usuario: str, max_tokens: int = 600) -> str:
    """Modo economia para cálculos e avaliações de mercado financeiro imperial."""
    return await chamar_ia(sistema, usuario, "economia", max_tokens, 0.4)


async def ia_npc(sistema: str, usuario: str, max_tokens: int = 350) -> str:
    """Modo NPC para personificação de habitantes e diálogos dinâmicos."""
    return await chamar_ia(sistema, usuario, "npc", max_tokens, 0.8)


def status_motores() -> dict:
    """Retorna os motores de IA configurados e seu status em tempo real."""
    ativo = bool(_openrouter_key())
    return {
        key: {
            "modelo": cfg["model"],
            "provedor": "OpenRouter",
            "ativo": ativo,
        }
        for key, cfg in _MODELOS_OPENROUTER.items()
    }
