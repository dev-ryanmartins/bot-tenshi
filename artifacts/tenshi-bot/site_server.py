import asyncio
import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from aiohttp import web
from academia_curriculo import CURRICULO_ACADEMIA, CURSOS_VISIVEIS, formatar_cargo_diploma


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
BANNER_FILE = ASSETS_DIR / "tenshi-bandeira.png"
STATUS_FILE = DATA_DIR / "status.json"

SESSIONS: set[str] = set()


def _load_env_file():
    env_path = BASE_DIR.parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())


_load_env_file()


COMMAND_GROUPS: list[dict[str, Any]] = [
    {
        "name": "Perfil e personagem",
        "tag": "perfil",
        "items": [
            ("status", "Mostra nivel, XP, moedas, status e ficha resumida."),
            ("ficha", "Abre ou edita a ficha de personagem."),
            ("criar-ficha", "Cria o personagem inicial."),
            ("inventario", "Lista itens e equipamentos."),
            ("conquistas", "Mostra conquistas desbloqueadas."),
            ("especies", "Lista especies e racas disponiveis."),
            ("poderes", "Mostra a arvore de poderes."),
            ("meus-poderes", "Lista os poderes desbloqueados."),
        ],
    },
    {
        "name": "RPG narrativo",
        "tag": "rpg",
        "items": [
            ("treinar [acao]", "Treina e ganha XP."),
            ("missao", "Gera uma missao narrativa."),
            ("meditar", "Recupera energia espiritual."),
            ("descansar", "Recupera HP."),
            ("interagir [acao]", "Executa uma acao de roleplay."),
            ("dado [d20]", "Rola dados narrativos."),
            ("profissao [classe]", "Define profissao."),
            ("clima", "Mostra clima e efeitos do dia."),
        ],
    },
    {
        "name": "IA e lore",
        "tag": "ia",
        "items": [
            ("cronica [tipo]", "Cria cronica com IA."),
            ("evento-lore", "Gera evento ou profecia."),
            ("oraculo [pergunta]", "Consulta o oraculo."),
            ("falar [npc]", "Conversa com NPC."),
            ("lore-historico", "Consulta registros antigos."),
            ("status-ia", "Mostra motores OpenRouter."),
            ("aconselhar-estrategia [caso]", "Analise estrategica com IA."),
            ("chat [pedido]", "Conversa direta com a IA Tenshi."),
            ("biblioteca-imperial", "Lista todos os PDFs na memoria."),
            ("documento [pdf]", "Resumo de um documento oficial."),
            ("memoria-imperial [tema]", "Busca na memoria documental."),
            ("grade-academia", "Mostra faculdades e cursos do curriculo oficial."),
            ("certificado [curso]", "Mostra competencias e empregos liberados pelo diploma."),
            ("aptidao-academica [curso]", "IA cria perguntas ou avalia aptidao do aluno."),
            ("aula-imperial [tema]", "Aula curta da Academia Imperial."),
            ("missao-historica [tema]", "Missao narrativa baseada na historia."),
            ("juramento-tenshi [tema]", "Cria juramento cerimonial."),
            ("protocolo-imperial [sit.]", "Cria protocolo baseado nos PDFs."),
            ("quiz-imperial", "Pergunta de conhecimento Tenshi."),
        ],
    },
    {
        "name": "Economia e banco",
        "tag": "economia",
        "items": [
            ("carteira", "Mostra moedas em maos."),
            ("mercado", "Abre mercado oficial."),
            ("carreiras", "Lista empregos e requisitos de diplomas."),
            ("emprego legal [id]", "Trabalha em um cargo legal, inclusive cargos por diploma."),
            ("comprar [item]", "Compra item."),
            ("banco", "Abre painel bancario."),
            ("depositar [valor]", "Deposita moedas."),
            ("sacar [valor]", "Saca moedas."),
            ("transferir @user [valor]", "Transfere moedas."),
            ("emprestimo [valor]", "Solicita emprestimo."),
            ("poupanca [valor]", "Investe na poupanca."),
            ("comprar-acoes [valor]", "Compra acoes."),
        ],
    },
    {
        "name": "Social e cotidiano",
        "tag": "social",
        "items": [
            ("pedido @user", "Pedido comum com aceite e votos."),
            ("pedido-real @user", "Pedido real que inicia o rito solene."),
            ("rito-real @rei @rainha", "Cerimonia real em etapas conforme o PDF."),
            ("registro-casamento @user", "Mostra certidao matrimonial."),
            ("divorcio", "Encerra casamento."),
            ("correio", "Correio anonimo."),
            ("psicologo [texto]", "Consulta psicologica."),
            ("beber [bebida]", "Ativa embriaguez narrativa."),
            ("jornal-cotidiano", "Jornal diario."),
            ("residencia", "Entra na casa do condominio."),
            ("fofoca", "Cronica do condominio."),
        ],
    },
    {
        "name": "Estado e admin",
        "tag": "admin",
        "items": [
            ("diagnostico-ia", "Diagnostico tecnico."),
            ("bandeira", "Mostra a bandeira oficial da Familia Tenshi."),
            ("historia-tenshi", "Mostra resumo das bases historicas do Imperio."),
            ("base-historica", "Consulta a memoria historica resumida."),
            ("consultar-lei [tema]", "Consulta o Codigo Imperial Tenshi."),
            ("parecer-ia [caso]", "Parecer administrativo com IA."),
            ("plano-admin [objetivo]", "Plano de governo com IA."),
            ("decreto [texto]", "Publica decreto."),
            ("criar-cargo [emoji] [nome]", "Cria cargo no padrao imperial."),
            ("criar-secoes-cargos", "Cria secoes visuais para separar cargos."),
            ("cargos-servidor", "Lista todos os cargos visiveis."),
            ("mapear-cargos", "Salva mapa administrativo dos cargos."),
            ("auditoria-cargos-ia", "Organiza funcoes dos cargos com IA."),
            ("funcao-cargo @cargo [texto]", "Define funcao manual do cargo."),
            ("publicar-mapa-cargos", "Publica manual de cargos."),
            ("auditoria-permissoes", "Audita permissoes do bot em cada chat."),
            ("corrigir-permissoes-bot", "Corrige acesso essencial do bot."),
            ("mapa-canais", "Mostra perfis sugeridos dos chats."),
            ("aplicar-perfil-canal #canal [perfil]", "Aplica perfil publico/staff/fichas/etc."),
            ("warn @user", "Aplica advertencia."),
            ("ban @user", "Bane usuario."),
            ("kick @user", "Expulsa usuario."),
            ("clear [n]", "Limpa mensagens."),
            ("reset-era", "Reinicia era do RPG."),
            ("exportar-banco", "Exporta dados por DM."),
        ],
    },
]


AI_MOTORS = [
    ("Narrativa", "OPENROUTER_MODEL_NARRATIVA", "Cronicas, missoes e roleplay."),
    ("Rapida", "OPENROUTER_MODEL_RAPIDA", "Triagem, respostas curtas e NPCs."),
    ("Analitica", "OPENROUTER_MODEL_ANALITICA", "Juridico, estrategia e exames."),
    ("Relatorio", "OPENROUTER_MODEL_RELATORIO", "Auditorias e relatorios longos."),
    ("Soberana", "OPENROUTER_MODEL_SOBERANA", "Decretos e geopolitica."),
    ("Economia", "OPENROUTER_MODEL_ECONOMIA", "Calculos e transacoes."),
    ("NPC", "OPENROUTER_MODEL_NPC", "Personagens e clima."),
]


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "nao", "não", "no", "off"}


def _is_railway() -> bool:
    return any(
        os.environ.get(name)
        for name in ("RAILWAY_SERVICE_ID", "RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID")
    )


def _site_host() -> str:
    if _is_railway():
        return "0.0.0.0"
    return os.environ.get("SITE_HOST", "0.0.0.0")


def _site_port() -> int:
    return int(os.environ.get("PORT") or os.environ.get("SITE_PORT") or "8081")


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _bot_status(bot=None) -> dict[str, Any]:
    if bot is not None and bot.is_ready():
        return {
            "online": True,
            "guilds": len(bot.guilds),
            "latency": round(bot.latency * 1000, 1),
            "user": str(bot.user) if bot.user else None,
            "updated_at": datetime.utcnow().isoformat(),
        }

    data = _read_json(STATUS_FILE, {})
    try:
        updated_at = datetime.fromisoformat(data.get("updated_at", ""))
        stale = (datetime.utcnow() - updated_at).total_seconds() > 45
    except Exception:
        stale = True

    return {
        "online": bool(data.get("online")) and not stale,
        "guilds": int(data.get("guilds", 0) or 0),
        "latency": float(data.get("latency", 0) or 0),
        "user": data.get("user"),
        "updated_at": data.get("updated_at"),
    }


def _data_overview() -> dict[str, Any]:
    users = _read_json(DATA_DIR / "db.json", {})
    casas = _read_json(DATA_DIR / "casas.json", {})
    acoes = _read_json(DATA_DIR / "acoes.json", {})
    status = _bot_status()
    return {
        "usuarios": len(users) if isinstance(users, dict) else 0,
        "casas": len(casas) if isinstance(casas, dict) else 0,
        "acoes": len(acoes) if isinstance(acoes, dict) else 0,
        "site_port": _site_port(),
        "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
        "bot_online": status["online"],
    }


def _ai_status() -> list[dict[str, Any]]:
    has_key = bool(os.environ.get("OPENROUTER_API_KEY"))
    defaults = {
        "OPENROUTER_MODEL_NARRATIVA": "meta-llama/llama-3.1-70b-instruct",
        "OPENROUTER_MODEL_RAPIDA": "meta-llama/llama-3.1-8b-instruct",
        "OPENROUTER_MODEL_ANALITICA": "openai/gpt-4o-mini",
        "OPENROUTER_MODEL_RELATORIO": "google/gemini-flash-1.5",
        "OPENROUTER_MODEL_SOBERANA": "anthropic/claude-3.5-sonnet",
        "OPENROUTER_MODEL_ECONOMIA": "openai/gpt-4o-mini",
        "OPENROUTER_MODEL_NPC": "meta-llama/llama-3.1-8b-instruct",
    }
    return [
        {
            "name": name,
            "model": os.environ.get(env_name, defaults[env_name]),
            "description": desc,
            "active": has_key,
        }
        for name, env_name, desc in AI_MOTORS
    ]


def _commands_payload() -> list[dict[str, Any]]:
    return [
        {
            "name": group["name"],
            "tag": group["tag"],
            "items": [{"cmd": cmd, "desc": desc} for cmd, desc in group["items"]],
        }
        for group in COMMAND_GROUPS
    ]


def _academy_payload() -> list[dict[str, Any]]:
    cursos = []
    for key in CURSOS_VISIVEIS:
        curso = CURRICULO_ACADEMIA[key]
        cursos.append({
            "id": key,
            "name": curso.get("nome", key),
            "emoji": curso.get("emoji", "🎓"),
            "faculty": curso.get("faculdade", "Academia Imperial Tenshi"),
            "target_role": curso.get("cargo_destino", ""),
            "diploma_role": formatar_cargo_diploma(key),
            "competencies": curso.get("competencias", []),
            "permissions": curso.get("permissoes_rpg", []),
            "jobs": curso.get("empregos", []),
            "hours": curso.get("tempo_estudo_h", 12),
        })
    return cursos


def _role_maps_from_disk() -> dict[str, Any]:
    return _read_json(DATA_DIR / "cargos_funcoes.json", {})


def _channel_permissions_from_disk() -> dict[str, Any]:
    return _read_json(DATA_DIR / "permissoes_canais.json", {})


def _roles_payload(bot=None) -> dict[str, Any]:
    saved = _role_maps_from_disk()
    payload = {"online": bool(bot is not None and bot.is_ready()), "guilds": [], "saved": saved}
    if bot is None or not bot.is_ready():
        return payload
    for guild in bot.guilds:
        roles = []
        for role in sorted(guild.roles, key=lambda item: item.position, reverse=True):
            if role.is_default():
                continue
            perms = []
            for attr, label in {
                "administrator": "Administrador",
                "manage_guild": "Gerenciar servidor",
                "manage_roles": "Gerenciar cargos",
                "manage_channels": "Gerenciar canais",
                "manage_messages": "Gerenciar mensagens",
                "ban_members": "Banir",
                "kick_members": "Expulsar",
                "moderate_members": "Moderar",
            }.items():
                if getattr(role.permissions, attr, False):
                    perms.append(label)
            roles.append({
                "id": str(role.id),
                "name": role.name,
                "members": len(role.members),
                "position": role.position,
                "color": str(role.color),
                "managed": role.managed,
                "mentionable": role.mentionable,
                "permissions": perms,
            })
        payload["guilds"].append({"id": str(guild.id), "name": guild.name, "roles": roles})
    return payload


def _channel_permissions_payload(bot=None) -> dict[str, Any]:
    saved = _channel_permissions_from_disk()
    payload = {"online": bool(bot is not None and bot.is_ready()), "guilds": [], "saved": saved}
    if bot is None or not bot.is_ready():
        return payload
    for guild in bot.guilds:
        channels = []
        for channel in guild.channels:
            if channel.__class__.__name__ == "CategoryChannel":
                continue
            if not hasattr(channel, "permissions_for"):
                continue
            me = guild.me
            if not me:
                continue
            perms = channel.permissions_for(me)
            missing = []
            for attr, label in {
                "view_channel": "Ver canal",
                "send_messages": "Enviar mensagens",
                "embed_links": "Enviar embeds",
                "read_message_history": "Ler historico",
                "add_reactions": "Reagir",
            }.items():
                if hasattr(perms, attr) and not getattr(perms, attr, False):
                    missing.append(label)
            channels.append({
                "id": str(channel.id),
                "name": channel.name,
                "category": getattr(getattr(channel, "category", None), "name", None),
                "missing": missing,
                "ok": not missing,
            })
        payload["guilds"].append({"id": str(guild.id), "name": guild.name, "channels": channels})
    return payload


def _admin_token(username: str, password: str) -> str:
    secret = os.environ.get("ADMIN_SECRET", "tenshi-local-secret")
    digest = hmac.new(secret.encode(), f"{username}:{password}".encode(), hashlib.sha256).hexdigest()
    return digest + "." + secrets.token_hex(16)


def _authorized(request: web.Request) -> bool:
    auth = request.headers.get("Authorization", "")
    return auth.startswith("Bearer ") and auth.removeprefix("Bearer ").strip() in SESSIONS


def _initial_state() -> str:
    return json.dumps(
        {
            "commands": _commands_payload(),
            "ai": _ai_status(),
            "overview": _data_overview(),
            "academy": _academy_payload(),
        },
        ensure_ascii=False,
    )


HTML_TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tenshi Bot - Site Oficial</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #07080a;
      --ink: #f6f3ea;
      --muted: #a19ba8;
      --line: rgba(255,255,255,.12);
      --panel: rgba(18,20,26,.82);
      --panel-2: rgba(26,29,38,.92);
      --gold: #e3bd63;
      --violet: #8d6bff;
      --cyan: #39c2d7;
      --green: #37d67a;
      --red: #ef4444;
      --shadow: 0 28px 90px rgba(0,0,0,.38);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 12% 8%, rgba(141,107,255,.30), transparent 28rem),
        radial-gradient(circle at 88% 16%, rgba(227,189,99,.18), transparent 24rem),
        linear-gradient(180deg, #090a0d 0%, #07080a 46%, #0b0d12 100%);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, Segoe UI, Arial, sans-serif;
      letter-spacing: 0;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image: linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px);
      background-size: 42px 42px;
      mask-image: linear-gradient(to bottom, black, transparent 78%);
    }
    a { color: inherit; text-decoration: none; }
    button, input { font: inherit; }
    .shell { max-width: 1220px; margin: 0 auto; padding: 24px; position: relative; }
    .nav {
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 12px 0;
      backdrop-filter: blur(18px);
    }
    .brandmark {
      width: 38px;
      height: 38px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: #050505;
      border: 1px solid var(--line);
      color: var(--gold);
      font-weight: 900;
      overflow: hidden;
    }
    .brandmark img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .nav strong { font-size: 14px; }
    .nav-links { margin-left: auto; display: flex; flex-wrap: wrap; gap: 8px; }
    .nav-links a, .ghost {
      border: 1px solid var(--line);
      color: var(--muted);
      background: rgba(255,255,255,.03);
      padding: 8px 11px;
      border-radius: 8px;
      font-size: 13px;
      cursor: pointer;
    }
    .hero {
      min-height: 74vh;
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(360px, .9fr);
      gap: 28px;
      align-items: center;
      padding: 54px 0 34px;
    }
    .eyebrow {
      color: var(--gold);
      text-transform: uppercase;
      letter-spacing: .12em;
      font-weight: 900;
      font-size: 12px;
    }
    h1 {
      margin: 14px 0 16px;
      font-size: clamp(48px, 8vw, 96px);
      line-height: .88;
      letter-spacing: 0;
    }
    .lead { max-width: 710px; color: var(--muted); line-height: 1.7; font-size: 18px; }
    .actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--line);
      background: var(--panel-2);
      color: var(--ink);
      border-radius: 8px;
      padding: 12px 15px;
      font-weight: 800;
      cursor: pointer;
    }
    .btn.primary { background: linear-gradient(135deg, var(--violet), #6848d7); border-color: rgba(255,255,255,.22); }
    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      box-shadow: var(--shadow);
      border-radius: 8px;
      padding: 18px;
    }
    .status-panel { display: grid; gap: 16px; }
    .panel-head { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-bottom: 8px; }
    .panel-head h2, .section-head h2 { margin: 0; font-size: 22px; }
    .muted, .panel-head small { color: var(--muted); }
    .metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .metric {
      background: rgba(255,255,255,.035);
      border: 1px solid rgba(255,255,255,.08);
      border-radius: 8px;
      padding: 14px;
    }
    .metric small { color: var(--muted); display: block; margin-bottom: 8px; }
    .metric strong { font-size: 28px; line-height: 1; }
    .dot { display: inline-block; width: 10px; height: 10px; border-radius: 99px; background: var(--red); margin-right: 8px; }
    .dot.online { background: var(--green); box-shadow: 0 0 18px rgba(55,214,122,.55); }
    .section-head { display: flex; justify-content: space-between; gap: 18px; align-items: end; margin: 48px 0 16px; }
    .tools { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    input {
      min-height: 42px;
      border: 1px solid var(--line);
      background: rgba(0,0,0,.24);
      color: var(--ink);
      border-radius: 8px;
      padding: 0 12px;
      outline: none;
    }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
    .wide { grid-column: span 2; }
    .cards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
    .card-title { display: flex; justify-content: space-between; gap: 12px; font-weight: 900; margin-bottom: 10px; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      border: 1px solid rgba(141,107,255,.24);
      background: rgba(141,107,255,.10);
      color: #ddd6fe;
      border-radius: 999px;
      padding: 8px 10px;
      cursor: pointer;
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 12px;
    }
    .ai-card .model { color: var(--gold); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 12px; word-break: break-word; }
    .ai-card p { color: var(--muted); line-height: 1.55; min-height: 48px; }
    .admin-grid { display: grid; grid-template-columns: 1fr 1fr auto; gap: 12px; align-items: end; }
    .admin-result { margin-top: 14px; min-height: 22px; color: var(--gold); }
    .role-board { margin-top: 16px; display: grid; gap: 12px; }
    .role-row {
      display: grid;
      grid-template-columns: minmax(180px, 1.1fr) minmax(80px, .35fr) minmax(180px, 1fr);
      gap: 12px;
      align-items: center;
      border: 1px solid rgba(255,255,255,.08);
      background: rgba(255,255,255,.035);
      border-radius: 8px;
      padding: 12px;
    }
    .role-row strong { overflow-wrap: anywhere; }
    .role-row small { color: var(--muted); }
    .role-plan {
      margin-top: 16px;
      white-space: pre-wrap;
      color: var(--muted);
      line-height: 1.55;
      max-height: 360px;
      overflow: auto;
    }
    footer { margin-top: 54px; padding: 24px 0; border-top: 1px solid var(--line); color: var(--muted); font-size: 13px; }
    @media (max-width: 920px) {
      .hero, .grid, .cards { grid-template-columns: 1fr; }
      .wide { grid-column: auto; }
      .admin-grid { grid-template-columns: 1fr; }
      .role-row { grid-template-columns: 1fr; }
      .nav { align-items: flex-start; }
      .nav-links { justify-content: flex-end; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <nav class="nav">
      <div class="brandmark"><img src="/assets/tenshi-bandeira.png" alt="Tenshi" /></div>
      <div><strong>Tenshi Bot</strong><div class="muted">Python site integrado</div></div>
      <div class="nav-links">
        <a href="#status">Status</a>
        <a href="#academia">Academia</a>
        <a href="#ia">IA</a>
        <a href="#comandos">Comandos</a>
        <a href="#admin">Admin</a>
      </div>
    </nav>

    <section class="hero">
      <div>
        <div class="eyebrow">Imperio de Tenshi</div>
        <h1>Centro de comando do bot.</h1>
        <p class="lead">Site oficial em Python, com frontend e backend no mesmo processo. Acompanhe status do Discord, motores OpenRouter, dados locais e referencia de comandos em tempo real.</p>
        <div class="actions">
          <a class="btn primary" href="#comandos">Explorar comandos</a>
          <a class="btn" href="/api/status">Ver API</a>
        </div>
      </div>
      <section class="panel status-panel" id="status">
        <div class="panel-head"><h2>Status ao vivo</h2><small id="updated">carregando</small></div>
        <div class="metric-grid">
          <div class="metric"><small>Status</small><strong id="online"><span class="dot"></span>Offline</strong></div>
          <div class="metric"><small>Servidores</small><strong id="guilds">0</strong></div>
          <div class="metric"><small>Latencia</small><strong id="latency">0ms</strong></div>
          <div class="metric"><small>OpenRouter</small><strong id="openrouter">-</strong></div>
        </div>
        <p class="muted" id="bot-user">Usuario: -</p>
      </section>
    </section>

    <section class="grid" id="overview"></section>

    <div class="section-head" id="academia">
      <div><h2>Academia Imperial</h2><p class="muted">Cursos, diplomas, competências e empregos liberados pelo currículo oficial.</p></div>
      <a class="ghost" href="/api/academy">API da Academia</a>
    </div>
    <section class="cards" id="academy-cards"></section>

    <div class="section-head" id="ia">
      <div><h2>Motores de IA</h2><p class="muted">Modelos configuraveis por variavel de ambiente.</p></div>
      <button class="ghost" id="refresh">Atualizar</button>
    </div>
    <section class="cards" id="ai-cards"></section>

    <div class="section-head" id="comandos">
      <div><h2>Comandos</h2><p class="muted">Clique em qualquer comando para copiar.</p></div>
      <div class="tools"><input id="search" placeholder="Pesquisar comando..." /></div>
    </div>
    <section class="cards" id="command-cards"></section>

    <div class="section-head" id="admin">
      <div><h2>Painel admin</h2><p class="muted">Autenticacao local. Configure ADMIN_PASSWORD e ADMIN_SECRET.</p></div>
    </div>
    <section class="panel">
      <div class="admin-grid">
        <label><span class="muted">Usuario</span><input id="admin-user" autocomplete="username" value="admin" /></label>
        <label><span class="muted">Senha</span><input id="admin-pass" type="password" autocomplete="current-password" /></label>
        <button class="btn primary" id="login">Entrar</button>
      </div>
      <div class="admin-result" id="admin-msg"></div>
      <div class="section-head" style="margin-top:28px">
        <div><h2>Organizacao de cargos</h2><p class="muted">Leitura em tempo real dos cargos do Discord e mapa salvo pela IA.</p></div>
        <button class="ghost" id="load-roles">Carregar cargos</button>
      </div>
      <div class="role-board" id="role-board"></div>
      <div class="role-plan" id="role-plan"></div>
      <div class="section-head" style="margin-top:28px">
        <div><h2>Permissoes dos chats</h2><p class="muted">Mostra se o bot consegue operar em cada canal.</p></div>
        <button class="ghost" id="load-channel-perms">Carregar permissoes</button>
      </div>
      <div class="role-board" id="channel-perm-board"></div>
    </section>

    <footer>Tenshi Bot - Python frontend/backend - Discord - OpenRouter</footer>
  </main>

  <script>
    const initial = __INITIAL_STATE__;
    const $ = (id) => document.getElementById(id);
    let token = localStorage.getItem("tenshi_admin_token") || "";
    let commands = initial.commands || [];
    let academy = initial.academy || [];

    function renderOverview(overview) {
      $("overview").innerHTML = [
        ["Usuarios", overview.usuarios],
        ["Casas", overview.casas],
        ["Acoes", overview.acoes],
        ["Porta do site", overview.site_port],
        ["Backend", "Python/aiohttp"],
        ["IA", overview.openrouter ? "Configurada" : "Sem chave"],
      ].map(([label, value]) => `
        <div class="panel metric"><small>${label}</small><strong>${value}</strong></div>
      `).join("");
    }

    function renderAI(items) {
      $("ai-cards").innerHTML = items.map(item => `
        <article class="panel ai-card">
          <div class="card-title"><span>${item.name}</span><span class="dot ${item.active ? "online" : ""}"></span></div>
          <div class="model">${item.model}</div>
          <p>${item.description}</p>
        </article>
      `).join("");
    }

    function renderAcademy(items) {
      $("academy-cards").innerHTML = items.map(course => `
        <article class="panel ai-card">
          <div class="card-title"><span>${course.emoji} ${course.name}</span><small class="muted">${course.hours}h</small></div>
          <div class="model">${course.id}</div>
          <p>${course.faculty}</p>
          <p><strong>Diploma:</strong> ${course.diploma_role}</p>
          <p><strong>Libera:</strong> ${(course.jobs || []).slice(0, 4).join(", ") || "em configuracao"}</p>
          <div class="chips">
            ${(course.competencies || []).slice(0, 4).map(item => `<span class="chip">${item}</span>`).join("")}
          </div>
        </article>
      `).join("");
    }

    function renderCommands(filter = "") {
      const term = filter.toLowerCase();
      $("command-cards").innerHTML = commands.map(group => {
        const items = group.items.filter(item => `${item.cmd} ${item.desc} ${group.name}`.toLowerCase().includes(term));
        if (!items.length) return "";
        return `
          <article class="panel command-group">
            <div class="card-title"><span>${group.name}</span><small class="muted">${items.length}</small></div>
            <div class="chips">
              ${items.map(item => `<button class="chip" data-copy="Tenshi, ${item.cmd}" title="${item.desc}">Tenshi, ${item.cmd}</button>`).join("")}
            </div>
          </article>
        `;
      }).join("");
      document.querySelectorAll("[data-copy]").forEach(button => {
        button.addEventListener("click", async () => {
          await navigator.clipboard.writeText(button.dataset.copy);
          const old = button.textContent;
          button.textContent = "copiado";
          setTimeout(() => button.textContent = old, 900);
        });
      });
    }

    async function refreshStatus() {
      const [status, overview, ai] = await Promise.all([
        fetch("/api/status").then(r => r.json()),
        fetch("/api/overview").then(r => r.json()),
        fetch("/api/ai").then(r => r.json()),
      ]);
      $("online").innerHTML = `<span class="dot ${status.online ? "online" : ""}"></span>${status.online ? "Online" : "Offline"}`;
      $("guilds").textContent = status.guilds ?? 0;
      $("latency").textContent = `${status.latency ?? 0}ms`;
      $("openrouter").textContent = overview.openrouter ? "OK" : "OFF";
      $("bot-user").textContent = `Usuario: ${status.user || "-"}`;
      $("updated").textContent = status.updated_at ? new Date(status.updated_at).toLocaleTimeString() : "sem dados";
      renderOverview(overview);
      renderAI(ai);
    }

    async function loadRoles() {
      if (!token) {
        $("admin-msg").textContent = "Faca login para ver a organizacao dos cargos.";
        return;
      }
      const res = await fetch("/api/admin/roles", { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      if (!res.ok) {
        $("admin-msg").textContent = data.error || "Falha ao carregar cargos.";
        return;
      }
      const guild = (data.guilds || [])[0];
      if (!guild) {
        $("role-board").innerHTML = `<div class="muted">Bot offline ou sem servidores carregados.</div>`;
        $("role-plan").textContent = "";
        return;
      }
      $("role-board").innerHTML = guild.roles.map(role => `
        <div class="role-row">
          <strong>${role.name}</strong>
          <small>${role.members} membro(s)</small>
          <small>${role.permissions.length ? role.permissions.join(", ") : "sem permissao sensivel"}</small>
        </div>
      `).join("");
      const saved = data.saved?.[guild.id];
      $("role-plan").textContent = saved?.ia_plano ? `Plano IA salvo:\\n\\n${saved.ia_plano}` : "Use Tenshi, auditoria-cargos-ia no Discord para gerar o plano da IA.";
    }

    async function loadChannelPerms() {
      if (!token) {
        $("admin-msg").textContent = "Faca login para ver as permissoes dos chats.";
        return;
      }
      const res = await fetch("/api/admin/channel-permissions", { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      if (!res.ok) {
        $("admin-msg").textContent = data.error || "Falha ao carregar permissoes.";
        return;
      }
      const guild = (data.guilds || [])[0];
      if (!guild) {
        const savedGuild = Object.values(data.saved || {})[0];
        if (!savedGuild) {
          $("channel-perm-board").innerHTML = `<div class="muted">Sem auditoria salva. Use Tenshi, auditoria-permissoes no Discord.</div>`;
          return;
        }
        $("channel-perm-board").innerHTML = (savedGuild.canais || []).map(ch => `
          <div class="role-row">
            <strong>#${ch.nome}</strong>
            <small>${ch.perfil || ch.tipo}</small>
            <small>${ch.ok ? "OK" : "Falta: " + (ch.faltando || []).join(", ")}</small>
          </div>
        `).join("");
        return;
      }
      $("channel-perm-board").innerHTML = guild.channels.map(ch => `
        <div class="role-row">
          <strong>#${ch.name}</strong>
          <small>${ch.category || "sem categoria"}</small>
          <small>${ch.ok ? "OK" : "Falta: " + ch.missing.join(", ")}</small>
        </div>
      `).join("");
    }

    $("search").addEventListener("input", event => renderCommands(event.target.value));
    $("refresh").addEventListener("click", refreshStatus);
    $("load-roles").addEventListener("click", loadRoles);
    $("load-channel-perms").addEventListener("click", loadChannelPerms);
    $("login").addEventListener("click", async () => {
      const res = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: $("admin-user").value, password: $("admin-pass").value }),
      });
      const data = await res.json();
      if (!res.ok) {
        $("admin-msg").textContent = data.error || "Falha no login.";
        return;
      }
      token = data.token;
      localStorage.setItem("tenshi_admin_token", token);
      const admin = await fetch("/api/admin/overview", { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json());
      $("admin-msg").textContent = `Login OK. Usuarios: ${admin.overview.usuarios}, bot: ${admin.status.online ? "online" : "offline"}.`;
      loadRoles();
      loadChannelPerms();
    });

    renderOverview(initial.overview);
    renderAI(initial.ai);
    renderAcademy(academy);
    renderCommands();
    refreshStatus();
    setInterval(refreshStatus, 15000);
  </script>
</body>
</html>
"""


def _html() -> str:
    return HTML_TEMPLATE.replace("__INITIAL_STATE__", _initial_state())


def create_app(bot=None) -> web.Application:
    app = web.Application()

    async def index(_: web.Request) -> web.Response:
        return web.Response(text=_html(), content_type="text/html")

    async def status(_: web.Request) -> web.Response:
        return web.json_response(_bot_status(bot))

    async def commands(_: web.Request) -> web.Response:
        return web.json_response(_commands_payload())

    async def academy(_: web.Request) -> web.Response:
        return web.json_response(_academy_payload())

    async def overview(_: web.Request) -> web.Response:
        return web.json_response(_data_overview())

    async def ai(_: web.Request) -> web.Response:
        return web.json_response(_ai_status())

    async def login(request: web.Request) -> web.Response:
        if not os.environ.get("ADMIN_PASSWORD") or not os.environ.get("ADMIN_SECRET"):
            return web.json_response({"error": "ADMIN_PASSWORD e ADMIN_SECRET precisam estar configurados."}, status=503)

        body = await request.json()
        username = str(body.get("username", ""))
        password = str(body.get("password", ""))
        expected_user = os.environ.get("ADMIN_USERNAME", "admin")
        expected_pass = os.environ.get("ADMIN_PASSWORD", "")

        if not hmac.compare_digest(username, expected_user) or not hmac.compare_digest(password, expected_pass):
            return web.json_response({"error": "Credenciais invalidas."}, status=401)

        token = _admin_token(username, password)
        SESSIONS.add(token)
        return web.json_response({"token": token})

    async def admin_overview(request: web.Request) -> web.Response:
        if not _authorized(request):
            return web.json_response({"error": "Nao autorizado."}, status=401)
        return web.json_response({"status": _bot_status(bot), "overview": _data_overview(), "ai": _ai_status()})

    async def admin_roles(request: web.Request) -> web.Response:
        if not _authorized(request):
            return web.json_response({"error": "Nao autorizado."}, status=401)
        return web.json_response(_roles_payload(bot))

    async def admin_channel_permissions(request: web.Request) -> web.Response:
        if not _authorized(request):
            return web.json_response({"error": "Nao autorizado."}, status=401)
        return web.json_response(_channel_permissions_payload(bot))

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"ok": True, "service": "tenshi-python-site"})

    async def bandeira_asset(_: web.Request) -> web.FileResponse:
        return web.FileResponse(BANNER_FILE)

    app.router.add_get("/", index)
    app.router.add_get("/assets/tenshi-bandeira.png", bandeira_asset)
    app.router.add_get("/api/status", status)
    app.router.add_get("/api/commands", commands)
    app.router.add_get("/api/academy", academy)
    app.router.add_get("/api/overview", overview)
    app.router.add_get("/api/ai", ai)
    app.router.add_post("/api/admin/login", login)
    app.router.add_get("/api/admin/overview", admin_overview)
    app.router.add_get("/api/admin/roles", admin_roles)
    app.router.add_get("/api/admin/channel-permissions", admin_channel_permissions)
    app.router.add_get("/health", health)
    return app


async def start_site_server(bot=None) -> web.AppRunner | None:
    if not _env_bool("ENABLE_SITE", True):
        print("[SITE] Desativado por ENABLE_SITE=0.")
        return None

    host = _site_host()
    port = _site_port()

    runner = web.AppRunner(create_app(bot))
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"[SITE] Tenshi site online em http://{host}:{port}")
    return runner


def run_standalone():
    async def _main():
        runner = await start_site_server(None)
        if runner is None:
            return
        while True:
            await asyncio.sleep(3600)

    asyncio.run(_main())


def start_site_server_thread(bot=None) -> threading.Thread | None:
    if not _env_bool("ENABLE_SITE", True):
        print("[SITE] Desativado por ENABLE_SITE=0.")
        return None

    def _target():
        async def _main():
            runner = await start_site_server(bot)
            if runner is None:
                return
            while True:
                await asyncio.sleep(3600)

        try:
            asyncio.run(_main())
        except Exception as exc:
            print(f"[SITE] Erro fatal no site Python: {exc}")

    thread = threading.Thread(target=_target, name="tenshi-site", daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    run_standalone()
