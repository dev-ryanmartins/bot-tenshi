import asyncio
import json
import os
import sys
from datetime import UTC, datetime

import discord
from discord.ext import commands


def _configurar_console_utf8():
    import sys

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


_configurar_console_utf8()


def _carregar_env_local():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip())


_carregar_env_local()

from data_paths import configurar_diretorio_dados, data_file

configurar_diretorio_dados()


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)

from confirmacoes import processar_resposta
from database import get_user, save_user
from site_server import start_site_server_thread
from utils import (
    IMPERADOR_ID,
    PREFIXO,
    RODAPE_IMPERIAL,
    SEP,
    embed_imperial,
    install_discord_safety_patch,
)

install_discord_safety_patch()

from cogs.academia import Academia
from cogs.ajuda import AjudaCog, enviar_ajuda
from cogs.assistente_ia import AssistenteIA
from cogs.automacao_servidor import AutomacaoServidor
from cogs.avancado import Avancado
from cogs.biblioteca_imperial import BibliotecaImperial
from cogs.cargos_admin import CargosAdmin
from cogs.casas import Casas
from cogs.clero import Clero
from cogs.clima_ia import ClimaIA
from cogs.correio import Correio
from cogs.cotidiano import CotidianoCog
from cogs.crime import Crime
from cogs.duelo import Duelo
from cogs.economia import Economia
from cogs.empregos import Empregos
from cogs.empresa import Empresa
from cogs.eras import Eras
from cogs.especies import Especies
from cogs.estado import Estado
from cogs.eventos import Eventos
from cogs.faccoes import Faccoes
from cogs.familia import Familia
from cogs.financeiro import Financeiro
from cogs.geopolitica import Geopolitica
from cogs.governanca_ia import GovernancaIA
from cogs.infractions import Infractions
from cogs.infraestrutura_critica import InfraestruturaCritica
from cogs.inteligencia import Inteligencia
from cogs.interacoes_locais import InteracoesLocais
from cogs.juridico import Juridico
from cogs.loremaster import LoreMaster
from cogs.matrimonio import Matrimonio
from cogs.mistico import Mistico
from cogs.moderacao import Moderacao
from cogs.mundo import Mundo
from cogs.npcs import NPCs
from cogs.parentesco import Parentesco, aplicar_membro_inicial, garantir_parentesco_patriarca
from cogs.painel_admin import PainelAdmin
from cogs.perfil_config import PerfilConfig
from cogs.permissoes_canais import PermissoesCanais
from cogs.poderes import Poderes
from cogs.psicologia import Psicologia
from cogs.rpg import RPG
from cogs.soberano import Soberano, aplicar_perfil_supremo_imperador, garantir_cargos_supremos
from cogs.sistema_teste import SistemaTeste
from cogs.social import Social
from cogs.temporadas import Temporadas
from cogs.vizinhanca import Vizinhanca
from cogs.embed_topics import EmbedTopics
from cogs.ai_chatbot import AIChatbot
from cogs.music import Music
from cogs.stock_market import StockMarket
from cogs.minigames import MiniGames
from cogs.automod import AutoMod
from cogs.custom_commands import CustomCommands
from cogs.level_rewards import LevelRewards
from cogs.protecao_parcerias import ProtecaoParcerias
from cogs.moderacao_conteudo import ModeracaoConteudo
from cogs.event_system import EventSystem

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds   = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("tenshi ", "tenshi, ", "tenshi,"),
    intents=intents,
    help_command=None,
)

# ── Módulos ───────────────────────────────────────────────────────────────────
rpg         = RPG(bot)
economia    = Economia(bot)
faccoes     = Faccoes(bot)
mistico     = Mistico(bot)
duelo       = Duelo(bot)
eventos     = Eventos(bot)
moderacao   = Moderacao(bot)
loremaster  = LoreMaster(bot)
casas       = Casas(bot)
empresa     = Empresa(bot)
financeiro  = Financeiro(bot)
familia     = Familia(bot)
parentesco  = Parentesco(bot)
painel_admin = PainelAdmin(bot)
automacao   = AutomacaoServidor(bot)
mundo       = Mundo(bot)
locais      = InteracoesLocais(bot)
perfil_cfg  = PerfilConfig(bot)
especies    = Especies(bot)
poderes_cog = Poderes(bot)
empregos    = Empregos(bot)
vizinhanca  = Vizinhanca(bot)
avancado    = Avancado(bot)
social_cog  = Social(bot)
crime_cog   = Crime(bot)
cotidiano   = CotidianoCog(bot)
correio_cog = Correio(bot)
temporadas  = Temporadas(bot)
clero_cog   = Clero(bot)
juridico    = Juridico(bot)
intel       = Inteligencia(bot)
soberano    = Soberano(bot)
sistema_teste = SistemaTeste(bot)
protecao_parcerias = ProtecaoParcerias(bot)
moderacao_conteudo = ModeracaoConteudo(bot)
geopolitica = Geopolitica(bot)
estado      = Estado(bot)
eras_cog    = Eras(bot)
clima_cog   = ClimaIA(bot)
academia    = Academia(bot)
infra       = InfraestruturaCritica(bot)
npcs_cog    = NPCs(bot)
psicologia  = Psicologia(bot)
matrimonio  = Matrimonio(bot)
governanca_ia = GovernancaIA(bot)
cargos_admin = CargosAdmin(bot)
assistente_ia = AssistenteIA(bot)
permissoes_canais = PermissoesCanais(bot)
biblioteca_imperial = BibliotecaImperial(bot)
infractions = Infractions(bot)
embed_topics = EmbedTopics(bot)
ai_chatbot = AIChatbot(bot)
music = Music(bot)
stock_market = StockMarket(bot)
minigames = MiniGames(bot)
automod = AutoMod(bot)
custom_commands = CustomCommands(bot)
level_rewards = LevelRewards(bot)
event_system = EventSystem(bot)

# ── Fundação de Tenshi ────────────────────────────────────────────────────────
FUNDACAO_TENSHI = datetime(2016, 6, 6)

_imperador_saudado: set = set()
_aniversario_anunciado: set = set()

# ── Verificação de Canais ─────────────────────────────────────────────────────
import json
import os

CANAIS_CONFIG_FILE = "data/canais_comandos.json"

def _carregar_canais_config() -> dict:
    if not os.path.exists(CANAIS_CONFIG_FILE):
        return {"canais_comandos": {}, "categorias": {}}
    try:
        with open(CANAIS_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"canais_comandos": {}, "categorias": {}}

def _verificar_canal_permitido(message, cmd: str) -> bool:
    """Verifica se o comando pode ser usado no canal atual."""
    config = _carregar_canais_config()
    canais = config.get("canais_comandos", {})
    
    # Se não houver configuração, permitir em todos os canais
    if not canais:
        return True
    
    # Imperador pode usar comandos em qualquer lugar
    if message.author.id == IMPERADOR_ID:
        return True
    
    canal_nome = message.channel.name.lower() if hasattr(message.channel, 'name') else ""
    canal_id = str(message.channel.id)
    
    # Verificar se o canal está na lista de canais permitidos
    for nome_canal, id_canal in canais.items():
        if id_canal == canal_id or canal_nome == nome_canal.lower():
            return True
    
    # Verificar por categoria de comando
    categorias = config.get("categorias", {})
    for categoria, canais_permitidos in categorias.items():
        if canal_id in canais_permitidos or any(canal_nome == c.lower() for c in canais_permitidos):
            # Verificar se o comando pertence a esta categoria
            if cmd in _comandos_por_categoria.get(categoria, []):
                return True
    
    return False

# Mapeamento de comandos por categoria
_comandos_por_categoria = {
    "economia": ["carteira", "saldo", "wallet", "moedas", "mercado", "loja", "shop", "comprar", "compra", "buy", "leilao", "leilão", "sorteio", "sorteio-real", "giveaway"],
    "banco": ["banco", "bank", "extrato", "depositar", "deposit", "sacar", "saque", "withdraw", "transferir", "pagar", "pix", "emprestimo", "empréstimo", "loan", "pagar-divida", "poupanca", "poupança", "comprar-acoes", "seguro-vida", "aposentar"],
    "rpg": ["status", "ficha", "criar-ficha", "pegada", "inventario", "conquistas", "especies", "treinar", "missao", "meditar", "descansar", "interagir", "dado", "trabalhar", "emprego", "carreiras", "profissao", "clima", "poderes", "meus-poderes"],
    "social": ["pedido", "pedido-real", "cerimonia", "iniciar-cerimonia", "rito-real", "registro-casamento", "divorcio", "casar", "abandonar-preparacao", "cancelar-casamento", "anular-casamento", "lavanderia", "sintetizar", "cartaz", "psicologo", "beber", "jornal-cotidiano", "correio", "estacoes", "entrevista", "socorrer", "vdd", "cassino"],
    "familia": ["familia", "família", "mafia", "máfia", "cla", "org", "parentesco", "vinculo-familiar", "vínculo-familiar", "cargo-familiar", "meu-parentesco", "parentesco-info", "ver-parentesco", "lista-parentescos", "parentescos", "tipos-parentesco", "arvore-familiar", "árvore-familiar", "familia-imperial", "casar-admin", "casamento-imperial", "uniao-imperial"],
    "admin": ["decreto", "promover", "criar-cargo", "cargo-imperial", "novo-cargo", "criar-secoes-cargos", "criar-seções-cargos", "separar-cargos", "cargos-servidor", "listar-cargos", "roles", "mapear-cargos", "sincronizar-cargos", "auditoria-cargos", "auditoria-cargos-ia", "organizar-cargos-ia", "organizar-servidor-ia", "cargo-info", "info-cargo", "funcao-cargo", "função-cargo", "definir-funcao-cargo", "publicar-mapa-cargos", "manual-cargos", "auditoria-permissoes", "auditoria-permissões", "checar-permissoes", "checar-permissões", "corrigir-permissoes-bot", "corrigir-permissões-bot", "arrumar-permissoes-bot", "mapa-canais", "mapa-chats", "estrutura-chats", "aplicar-perfil-canal", "perfil-canal", "organizar-chat", "punir-audacia", "punir", "julgamento", "julgar", "trial", "masmorra-prender", "prender", "masmorrar", "exilar", "anistia-real", "anistia", "trancar-portoes", "lockdown", "tesouro", "veto", "ban", "kick", "mute", "unmute", "desmutar", "dessilenciar", "unban", "clear", "slowmode", "warn", "aviso", "nota", "notas", "info", "historico", "ativar-embed", "embed-ativar", "mostrar-topic", "desativar-embed", "embed-desativar", "remover-topic", "criar-topico", "criar-tópico", "novo-topico", "listar-topics", "listar-tópicos", "topics", "painel-admin", "admin-panel", "painel-administrativo"],
    "utilitarios": ["ajuda", "help", "comandos", "menu", "ping", "servidor", "top", "backup", "bandeira", "brasao", "historia-tenshi", "base-historica", "status-ia", "aniversario"]
}

# ── Guard 1: dedup por ID de mensagem (mesma msg processada 2x) ───────────────
import time as _time
from collections import deque as _deque

_seen_msg_ids: set = set()
_seen_msg_deque: _deque = _deque(maxlen=500)
_recent_content_keys: dict = {}

def _ja_processou(mid: int) -> bool:
    if mid in _seen_msg_ids:
        return True
    # Remove o mais antigo do set quando a fila está cheia
    if len(_seen_msg_deque) >= 500:
        oldest = _seen_msg_deque[0]
        _seen_msg_ids.discard(oldest)
    _seen_msg_deque.append(mid)
    _seen_msg_ids.add(mid)
    return False


def _conteudo_repetido(message, conteudo: str) -> bool:
    agora = _time.monotonic()
    for key, ts in list(_recent_content_keys.items()):
        if agora - ts > 5.0:
            _recent_content_keys.pop(key, None)

    key = (message.author.id, message.channel.id, conteudo.strip().lower())
    ultimo = _recent_content_keys.get(key)
    if ultimo and agora - ultimo < 3.0:
        return True

    _recent_content_keys[key] = agora
    return False

# ── Guard 2: cooldown 2s por (user, cmd) — evita "digitou 2x rápido" ──────────
_cmd_timestamps: dict = {}  # (user_id, cmd) -> float

def _em_cooldown(user_id: int, cmd: str) -> bool:
    key = (user_id, cmd)
    agora = _time.monotonic()
    ultimo = _cmd_timestamps.get(key, 0.0)
    if agora - ultimo < 2.0:
        return True
    _cmd_timestamps[key] = agora
    return False

# ── Guard 3: flag para garantir que on_ready só inicializa tarefas UMA VEZ ────
_bg_tasks_initialized: bool = False
_task_aniversario = None
_task_status = None
_site_thread = None
STATUS_FILE = data_file("status.json")
SAUDACOES_FILE = data_file("saudacoes.json")
BANDEIRA_FILE = os.path.join(os.path.dirname(__file__), "assets", "tenshi-bandeira.png")


def _extrair_comando(conteudo: str) -> str | None:
    """Aceita `tenshi comando` e o formato histórico `Tenshi, comando`."""
    texto = conteudo.strip()
    texto_lower = texto.casefold()
    for prefixo in ("tenshi,", "tenshi"):
        if texto_lower == prefixo:
            return ""
        if texto_lower.startswith(prefixo + " "):
            return texto[len(prefixo):].strip()
    return None


def _salvar_status_bot(online: bool):
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    payload = {
        "online": online,
        "guilds": len(bot.guilds) if online and bot.is_ready() else 0,
        "latency": round(bot.latency * 1000, 1) if online and bot.is_ready() else 0,
        "user": str(bot.user) if online and bot.user else None,
        "updated_at": _utcnow().isoformat(),
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


async def _loop_status_bot():
    await bot.wait_until_ready()
    while not bot.is_closed():
        _salvar_status_bot(True)
        await asyncio.sleep(15)


def _carregar_saudacoes() -> dict:
    if not os.path.exists(SAUDACOES_FILE):
        return {}
    try:
        with open(SAUDACOES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _salvar_saudacoes(data: dict):
    os.makedirs(os.path.dirname(SAUDACOES_FILE), exist_ok=True)
    with open(SAUDACOES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@bot.event
async def on_ready():
    global _bg_tasks_initialized, _task_aniversario, _task_status

    print(f"⚜️  Bot Tenshi v2 online | {bot.user.name} ({bot.user.id})")
    print(f"🏛️  Servidores: {len(bot.guilds)}")
    print(f"👑  Imperador ID: {IMPERADOR_ID}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="o Império de Tenshi | Tenshi, ajuda"
        )
    )

    # Garante que as tarefas de background só são criadas UMA VEZ.
    # on_ready pode disparar múltiplas vezes em reconexões — sem este guard,
    # cada reconexão criaria novas tarefas duplicadas causando embeds duplos.
    if not _bg_tasks_initialized:
        _bg_tasks_initialized = True
        aplicar_perfil_supremo_imperador()
        for guild in bot.guilds:
            imperador = guild.get_member(IMPERADOR_ID)
            if imperador:
                try:
                    await garantir_cargos_supremos(imperador)
                    await garantir_parentesco_patriarca(imperador)
                except (discord.Forbidden, discord.HTTPException) as exc:
                    print(f"[AVISO] Cargos do fundador não aplicados em {guild.name}: {exc}")
        await bot.add_cog(infractions)
        await bot.add_cog(AjudaCog(bot))
        try:
            sincronizados = await bot.tree.sync()
            print(f"✅ {len(sincronizados)} comandos de barra sincronizados.")
        except Exception as exc:
            print(f"[AVISO] Não foi possível sincronizar comandos de barra: {exc}")
        eventos.cog_load()
        vizinhanca.cog_load()
        cotidiano.cog_load()
        crime_cog.cog_load()
        temporadas.cog_load()
        intel.cog_load()
        estado.cog_load()
        eras_cog.cog_load()
        clima_cog.cog_load()
        infra.cog_load()
        event_system.cog_load()
        protecao_parcerias.cog_load()
        moderacao_conteudo.cog_load()
        _task_aniversario = bot.loop.create_task(_loop_aniversario())
        _task_status = bot.loop.create_task(_loop_status_bot())
        print("✅ Tarefas de background inicializadas.")
    _salvar_status_bot(True)


async def _loop_aniversario():
    """Verifica diariamente se é aniversário de Tenshi (06/06)"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        agora = _utcnow()
        chave = f"{agora.year}-aniversario"
        if agora.month == 6 and agora.day == 6 and chave not in _aniversario_anunciado:
            _aniversario_anunciado.add(chave)
            anos = agora.year - FUNDACAO_TENSHI.year
            await _anunciar_aniversario(anos)
        # Verificar a cada hora
        await asyncio.sleep(3600)


async def _anunciar_aniversario(anos: int):
    """Anuncia o aniversário de Tenshi em todos os servidores"""
    numeral = {
        1: "Primeiro", 2: "Segundo", 3: "Terceiro", 4: "Quarto", 5: "Quinto",
        6: "Sexto", 7: "Sétimo", 8: "Oitavo", 9: "Nono", 10: "Décimo",
        11: "Décimo Primeiro", 12: "Décimo Segundo", 13: "Décimo Terceiro",
        14: "Décimo Quarto", 15: "Décimo Quinto",
    }.get(anos, f"{anos}°")

    marcos = {
        10: "Uma **DÉCADA** de glória imperial! Dez anos de batalhas, conquistas e lendas.",
        5: "**CINCO ANOS** de Império! Metade de uma década de poder e tradição.",
        15: "**QUINZE ANOS** de soberania eterna! O Império que não envelhece — apenas se fortalece.",
    }
    marco_texto = marcos.get(anos, f"**{anos} anos** de história, poder e lendas.")

    embed = discord.Embed(
        title=f"🎊 ⚜️ {anos}° ANIVERSÁRIO DO IMPÉRIO DE TENSHI ⚜️ 🎊",
        description=(
            f"*Em 06 de junho de 2016, o Imperador Alloy fundou o que seria um dos maiores impérios do Discord...*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏛️ **{numeral} Aniversário**\n{marco_texto}\n\n"
            f"*{anos} anos de guerreiros, lendas, intrigas, duelos, missões e crônicas.*\n"
            f"*{anos} anos do Imperador Alloy guiando esta nação com mão de ferro e coração de ouro.*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**Fundado em:** 06/06/2016\n"
            f"**Aniversariante:** {_utcnow().year}\n"
            f"**Imperador Eterno:** Alloy Tenshi\n\n"
            f"*Que o Império persista por mais {anos} anos — e muito além!*"
        ),
        color=0xFFD700
    )
    embed.set_footer(text=f"🎂 {anos} anos de glória  •  {RODAPE_IMPERIAL}")

    for guild in bot.guilds:
        canal = guild.system_channel
        if not canal:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    canal = ch
                    break
        if canal:
            try:
                await canal.send("@everyone 🎊🎂", embed=embed)
            except Exception:
                pass


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Marcar como processado ANTES de qualquer processamento
    if _ja_processou(message.id):
        return

    conteudo       = message.content.strip()
    conteudo_lower = conteudo.lower()
    resto_comando  = _extrair_comando(conteudo)
    eh_comando     = resto_comando is not None

    if eh_comando:
        resto = resto_comando
        partes = resto.split()
        if not partes:
            return
        cmd = partes[0].lower()
        args = partes[1:]
        
        # Verificar se o comando pode ser usado no canal atual
        # Comandos de ajuda e proteção imperial sempre permitidos em qualquer canal
        comandos_liberados = ["ajuda", "help", "comandos", "menu", "protecao-imperial", "protecaoimperial", "config-protecao", "ativar-protecao", "ativarprotecao", "enable-protection", "desativar-protecao", "desativarprotecao", "disable-protection", "confianca", "confiança", "trust", "add-trust", "remover-confianca", "removerconfianca", "remove-trust", "bloquear-servidor", "bloquearservidor", "block-server", "desbloquear-servidor", "desbloquearservidor", "unblock-server", "atividade-suspeita", "atividadesuspeita", "suspicious-activity", "teste-protecao", "testeprotecao", "test-protection", "config-moderacao", "configmoderacao", "bloquear-link", "bloquearlink", "desbloquear-link", "desbloquearlink", "adicionar-dominio-confianca", "adicionardominioconfianca", "remover-dominio-confianca", "removerdominioconfianca"]
        if cmd not in comandos_liberados:
            if not _verificar_canal_permitido(message, resto_comando.split()[0] if resto_comando else ""):
                await message.channel.send(embed=embed_imperial("🚫 Canal Incorreto", f"O comando só pode ser usado nos canais designados. Use o canal de comandos.", 0x6B0000))
                return
    if _conteudo_repetido(message, conteudo):
        return

    # Saudação automática ao Imperador (apenas em mensagens sem prefixo de comando)
    if message.author.id == IMPERADOR_ID and not eh_comando:
        await _saudar_imperador_se_necessario(message)

    # Invasão ativa
    if await eventos.processar_ataque_invasao(message):
        return

    # Verificar bloqueio (nocaute/prisão)
    if not eh_comando:
        u_data = get_user(message.author.id)
        bloq   = u_data.get("bloqueado_ate")
        if bloq:
            try:
                from datetime import datetime as _dt
                if _utcnow() < _dt.fromisoformat(bloq):
                    return
                else:
                    u_data["bloqueado_ate"] = None
                    save_user(message.author.id, u_data)
            except Exception:
                pass
        # Triagem jurídica automática (canais públicos)
        canal_nome = getattr(message.channel, "name", "")
        if any(c in canal_nome.lower() for c in ("geral", "beco", "cassino", "praça", "praca", "parque")):
            bloqueado = await juridico.triar_mensagem(message)
            if bloqueado:
                return
        # Embriaguez — distorcer texto no GERAL
        if "geral" in canal_nome.lower():
            texto_distorcido = cotidiano.processar_embriaguez(message.author.id, conteudo)
            if texto_distorcido:
                try:
                    await message.delete()
                    await message.channel.send(f"**{message.author.display_name}:** {texto_distorcido}")
                    return
                except Exception:
                    pass
        # Logging para crônicas do cotidiano
        if any(c in canal_nome.lower() for c in ("geral", "praça", "praca")):
            cotidiano.registrar_mensagem_geral(canal_nome, conteudo[:200])
        # Canal de Psicologia Estratégica — resposta automática da IA
        if "psicologia" in canal_nome.lower() and "estrategia" in canal_nome.lower():
            await psicologia.handle_canal_psicologia(message)
            return
        if await assistente_ia.talvez_responder(message, conteudo, PREFIXO):
            return
        await loremaster.handle_lore_natural(message, conteudo)
        return

    if cmd in ("confirmar", "confirmo", "sim"):
        await processar_resposta(message, confirmar=True)
        return

    if cmd in ("cancelar", "cancelo", "nao", "não"):
        await processar_resposta(message, confirmar=False)
        return

    # Guard 2 — cooldown 2s por usuário por comando
    if _em_cooldown(message.author.id, cmd):
        return

    # ══════════════════════════════════════════════════════════════════════════
    # ROTEADOR CENTRAL
    # ══════════════════════════════════════════════════════════════════════════

    # ── PERFIL & FICHA ────────────────────────────────────────────────────────
    if cmd in ("status", "perfil", "eu", "me"):
        await perfil_cfg.handle_status(message)
        return

    elif cmd in ("ficha",):
        await perfil_cfg.handle_ficha(message, args)
        return

    elif cmd in ("criar-ficha", "criarficha", "new-char", "novo-personagem", "registrar"):
        await especies.handle_criar_ficha(message)
        return

    elif cmd in ("pegada", "vibe", "estilo", "tema"):
        await perfil_cfg.handle_pegada(message, args)
        return

    elif cmd in ("inventario", "inventário", "inv"):
        await perfil_cfg.handle_inventario(message)
        return

    elif cmd in ("conquistas", "achievements"):
        await perfil_cfg.handle_conquistas(message)
        return

    # ── ESPÉCIES & LOCALIZAÇÃO ───────────────────────────────────────────────
    elif cmd in ("especies", "espécies", "racas", "raças"):
        await especies.handle_especies(message)
        return

    elif cmd in ("viajar", "travel", "mover", "ir"):
        await especies.handle_viajar(message)
        return

    elif cmd in ("mundo", "viajar-mundo", "viajando-pelo-mundo", "atlas-mundial"):
        await mundo.handle_mundo(message, args)
        return

    elif cmd in ("terminar-viagem", "encerrar-viagem", "voltar-de-viagem"):
        await mundo.handle_terminar_viagem(message, args)
        return

    elif cmd in ("viagem-atual", "onde-estou-mundo", "destino-atual"):
        await mundo.handle_viagem_atual(message, args)
        return

    elif cmd in ("local", "localizacao", "localização", "onde-estou", "mapa"):
        await especies.handle_meu_local(message)
        return

    # ── PODERES DE RP ─────────────────────────────────────────────────────────
    elif cmd in ("poderes", "poder", "habilidades", "skills", "arvore"):
        await poderes_cog.handle_poderes(message)
        return

    elif cmd in ("meus-poderes", "meuspoderes", "meus_poderes"):
        await poderes_cog.handle_meus_poderes(message)
        return

    # ── RPG NARRATIVO ─────────────────────────────────────────────────────────
    elif cmd in ("treinar", "treino", "train"):
        await rpg.handle_treinar(message, args)
        return

    elif cmd in ("missao", "missão", "mission"):
        await rpg.handle_missao(message, args)
        return

    elif cmd in ("meditar", "meditate"):
        await rpg.handle_meditar(message)
        return

    elif cmd in ("descansar", "rest"):
        await rpg.handle_descansar(message)
        return

    elif cmd in ("trabalhar", "trabalho", "work"):
        # Atalho rápido para emprego
        await empregos.handle_emprego(message, args)
        return

    elif cmd in ("emprego", "empregos", "jobs", "job"):
        if not args:
            await empregos.handle_trabalhos(message)
        else:
            await empregos.handle_emprego(message, args)
        return

    elif cmd in ("carreiras", "cargos-trabalho", "profissoes-disponiveis"):
        await empregos.handle_carreiras(message)
        return

    elif cmd in ("regras-trabalho", "regras-emprego", "normas-trabalho"):
        await empregos.handle_regras(message)
        return

    elif cmd in ("profissao", "profissão", "classe"):
        await rpg.handle_profissao(message, args)
        return

    elif cmd in ("interagir", "rp", "emote"):
        await rpg.handle_interagir(message, args)
        return

    elif cmd in ("dado", "dice", "rolar"):
        await rpg.handle_dado(message, args)
        return

    # ── LOREMASTER IA ─────────────────────────────────────────────────────────
    elif cmd in ("cronica", "crônica", "lore"):
        await loremaster.handle_cronica(message, args)
        return

    elif cmd in ("evento-lore", "profecia"):
        await loremaster.handle_evento_lore(message)
        return

    elif cmd in ("oraculo", "oráculo"):
        await loremaster.handle_oraculo(message, args)
        return

    elif cmd in ("falar", "npc"):
        await loremaster.handle_falar(message, args)
        return

    elif cmd in ("lore-historico", "cronicas-antigas"):
        await loremaster.handle_lore_historico(message)
        return

    elif cmd in ("quadro-avisos", "avisos", "missoes-diarias"):
        await loremaster.handle_quadro_avisos(message)
        return

    # ── MÍSTICO ───────────────────────────────────────────────────────────────
    elif cmd in ("tarot", "carta"):
        await mistico.handle_tarot(message)
        return

    elif cmd in ("runa", "rune"):
        await mistico.handle_runa(message)
        return

    elif cmd in ("astros", "constelacao", "horoscopo"):
        await mistico.handle_astros(message)
        return

    elif cmd in ("destino",):
        await mistico.handle_destino(message, args)
        return

    elif cmd in ("sacrificio", "sacrifício", "purificar"):
        await mistico.handle_sacrificio(message, args)
        return

    elif cmd in ("ritual-protecao", "ritual"):
        await mistico.handle_ritual(message)
        return

    # ── COMBATE ───────────────────────────────────────────────────────────────
    elif cmd in ("duelo", "duelar", "duel"):
        await duelo.handle_duelo(message, args)
        return

    elif cmd in ("aceitar-duelo", "aceitar"):
        await duelo.handle_aceitar_duelo(message)
        return

    elif cmd in ("invocar-chefe", "boss", "monstro"):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.administrator
        except: pass
        if tem_perm or message.author.id == IMPERADOR_ID:
            await eventos.iniciar_invasao(message.channel, args)
        else:
            await message.channel.send(embed=embed_imperial("🚫", "*Apenas administradores podem invocar criaturas.*", 0x6B0000))
        return

    elif cmd in ("invasao", "invasão"):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.administrator
        except: pass
        if tem_perm or message.author.id == IMPERADOR_ID:
            await eventos.iniciar_invasao(message.channel)
        else:
            await message.channel.send(embed=embed_imperial("🚫", "*Apenas administradores podem iniciar invasões.*", 0x6B0000))
        return

    # ── ECONOMIA ──────────────────────────────────────────────────────────────
    elif cmd in ("carteira", "saldo", "wallet", "moedas"):
        await economia.handle_carteira(message)
        return

    elif cmd in ("mercado", "loja", "shop"):
        await economia.handle_loja(message)
        return

    elif cmd in ("mercado-negro", "mercadonegro"):
        await economia.handle_mercado_negro(message)
        return

    elif cmd in ("comprar", "compra", "buy"):
        await economia.handle_comprar(message, args)
        return

    elif cmd in ("leilao", "leilão"):
        await economia.handle_leilao(message, args)
        return

    elif cmd in ("sorteio-real", "sorteio", "giveaway"):
        await economia.handle_sorteio(message)
        return

    # ── BANCO / FINANCEIRO ────────────────────────────────────────────────────
    elif cmd in ("banco", "bank", "extrato"):
        await financeiro.handle_banco(message)
        return

    elif cmd in ("depositar", "deposit"):
        await financeiro.handle_depositar(message, args)
        return

    elif cmd in ("sacar", "saque", "withdraw"):
        await financeiro.handle_sacar(message, args)
        return

    elif cmd in ("transferir", "pagar", "pix"):
        await financeiro.handle_transferir(message, args)
        return

    elif cmd in ("emprestimo", "empréstimo", "loan"):
        await financeiro.handle_emprestimo(message, args)
        return

    elif cmd in ("pagar-divida", "pagardivida", "quitar"):
        await financeiro.handle_pagar_divida(message, args)
        return

    elif cmd in ("historico", "histórico", "history"):
        if args or message.mentions:
            await infractions.handle_historico(message, args)
        else:
            await financeiro.handle_historico(message)
        return

    # ── CASAS (mercado imobiliário geral) ─────────────────────────────────────
    elif cmd in ("casas", "imoveis", "propriedades"):
        await vizinhanca.handle_portaria(message)
        return

    elif cmd in ("minha-casa", "minhacasa", "meu-lar"):
        if get_user(message.author.id).get("casa_condominio"):
            await vizinhanca.handle_meu_lar(message)
        else:
            await casas.handle_minha_casa(message)
        return

    elif cmd in ("vender-casa", "vendercasa"):
        if get_user(message.author.id).get("casa_condominio"):
            await vizinhanca.handle_devolver_casa(message)
        else:
            await casas.handle_vender_casa(message)
        return

    # ── VIZINHANÇA / CONDOMÍNIO ────────────────────────────────────────────────
    elif cmd in ("portaria", "condominio", "condomínio", "residencias"):
        await vizinhanca.handle_portaria(message)
        return

    elif cmd in ("sincronizar-condominio", "gerar-casas", "criar-canais-casas"):
        await vizinhanca.handle_sincronizar_canais(message, args)
        return

    elif cmd in ("organizar-canais", "automatizar-canais", "criar-canais-rpg"):
        await automacao.handle_organizar_canais(message, args)
        return

    elif cmd in ("meu-lar-cond", "meuların", "residencia", "residência"):
        await vizinhanca.handle_meu_lar(message)
        return

    elif cmd in ("convidar",):
        await vizinhanca.handle_convidar(message, args)
        return

    elif cmd in ("expulsar",):
        await vizinhanca.handle_expulsar(message, args)
        return

    elif cmd in ("devolver-casa", "devolvercasa", "sair-casa"):
        await vizinhanca.handle_devolver_casa(message)
        return

    elif cmd in ("moradores", "vizinhos"):
        await vizinhanca.handle_moradores(message)
        return

    elif cmd in ("cronica-cond", "fofoca", "crônica-cond"):
        await vizinhanca.handle_cronica_condominio(message)
        return

    elif cmd in ("descansar-lazer", "descanso-lazer", "relaxar"):
        await vizinhanca.handle_descanso_lazer(message)
        return

    # ── EMPRESA ───────────────────────────────────────────────────────────────
    elif cmd in ("empresa", "company", "corp", "enterprise", "negocio"):
        await empresa.handle_empresa(message, args)
        return

    # ── FAMÍLIA / MÁFIA ───────────────────────────────────────────────────────
    elif cmd in ("familia", "família", "mafia", "máfia", "cla", "org"):
        await familia.handle_familia(message, args)
        return

    elif cmd in ("parentesco", "vinculo-familiar", "vínculo-familiar", "cargo-familiar"):
        await parentesco.handle_parentesco(message, args)
        return

    elif cmd in ("meu-parentesco", "parentesco-info", "ver-parentesco"):
        await parentesco.handle_meu_parentesco(message, args)
        return

    elif cmd in ("lista-parentescos", "parentescos", "tipos-parentesco"):
        await parentesco.handle_lista_parentescos(message, args)
        return

    elif cmd in ("arvore-familiar", "árvore-familiar", "familia-imperial"):
        await parentesco.handle_arvore_familiar(message, args)
        return

    elif cmd in ("painel-admin", "admin-panel", "painel-administrativo"):
        await painel_admin.handle_painel_admin(message, args)
        return

    elif cmd in ("casar-admin", "casamento-imperial", "uniao-imperial"):
        await painel_admin.handle_casar_admin(message, args)
        return

    elif cmd in ("ativar-embed", "embed-ativar", "mostrar-topic"):
        await embed_topics.handle_ativar_embed(message, args)
        return

    elif cmd in ("desativar-embed", "embed-desativar", "remover-topic"):
        await embed_topics.handle_desativar_embed(message, args)
        return

    elif cmd in ("criar-topico", "criar-tópico", "novo-topico"):
        await embed_topics.handle_criar_topico(message, args)
        return

    elif cmd in ("listar-topics", "listar-tópicos", "topics"):
        await embed_topics.handle_listar_topics(message, args)
        return

    # ── SISTEMA DE TESTE ───────────────────────────────────────────────────────────
    elif cmd in ("teste-sistema", "testar-sistema", "diagnostico", "check"):
        await sistema_teste.handle_teste_sistema(message, args)
        return

    elif cmd in ("teste-embed", "testar-embed", "preview-embed"):
        await sistema_teste.handle_teste_embed(message, args)
        return

    elif cmd in ("teste-painel", "testar-painel"):
        await sistema_teste.handle_teste_painel(message, args)
        return

    # ── AI CHATBOT ───────────────────────────────────────────────────────────────
    elif cmd in ("chat", "conversar", "falar", "tenshi"):
        await ai_chatbot.handle_chat(message, args)
        return

    elif cmd in ("historico-chat", "chat-historico", "conversas"):
        await ai_chatbot.handle_historico_chat(message, args)
        return

    elif cmd in ("limpar-chat", "apagar-chat", "reset-chat"):
        await ai_chatbot.handle_limpar_chat(message, args)
        return

    elif cmd in ("pergunta", "perguntar", "duvida", "dúvida"):
        await ai_chatbot.handle_pergunta(message, args)
        return

    # ── MÚSICA ─────────────────────────────────────────────────────────────────
    elif cmd in ("join", "entrar", "conectar"):
        await music.handle_join(message, args)
        return

    elif cmd in ("leave", "sair", "disconnect"):
        await music.handle_leave(message, args)
        return

    elif cmd in ("play", "tocar", "p"):
        await music.handle_play(message, args)
        return

    elif cmd in ("skip", "pular"):
        await music.handle_skip(message, args)
        return

    elif cmd in ("queue", "fila", "playlist"):
        await music.handle_queue(message, args)
        return

    elif cmd in ("pause", "pausar"):
        await music.handle_pause(message, args)
        return

    elif cmd in ("resume", "retomar", "continuar"):
        await music.handle_resume(message, args)
        return

    elif cmd in ("stop", "parar"):
        await music.handle_stop(message, args)
        return

    elif cmd in ("volume", "vol"):
        await music.handle_volume(message, args)
        return

    elif cmd in ("np", "nowplaying", "tocando"):
        await music.handle_np(message, args)
        return

    # ── MERCADO DE AÇÕES ─────────────────────────────────────────────────────
    elif cmd in ("market", "mercado", "bolsa"):
        await stock_market.handle_market(message, args)
        return

    elif cmd in ("buy", "comprar"):
        await stock_market.handle_buy(message, args)
        return

    elif cmd in ("sell", "vender"):
        await stock_market.handle_sell(message, args)
        return

    elif cmd in ("portfolio", "carteira-acoes", "ações"):
        await stock_market.handle_portfolio(message, args)
        return

    elif cmd in ("stock-info", "info-acao", "ação-info"):
        await stock_market.handle_stock_info(message, args)
        return

    elif cmd in ("top-stocks", "top-ações", "melhores-ações"):
        await stock_market.handle_top_stocks(message, args)
        return

    # ── MINI-JOGOS ─────────────────────────────────────────────────────────────
    elif cmd in ("adivinhacao", "adivinhação", "guess-number"):
        await minigames.handle_adivinhacao(message, args)
        return

    elif cmd in ("guess", "adivinhar"):
        await minigames.handle_guess(message, args)
        return

    elif cmd in ("ppt", "pedra-papel-tesoura", "jokenpo"):
        await minigames.handle_pedra_papel_tesoura(message, args)
        return

    elif cmd in ("dado", "dado-sorte", "roll"):
        await minigames.handle_dado_sorte(message, args)
        return

    elif cmd in ("quiz", "pergunta", "quiz-rapido"):
        await minigames.handle_quiz(message, args)
        return

    elif cmd in ("quiz-answer", "quiz-resposta", "responder-quiz"):
        await minigames.handle_quiz_answer(message, args)
        return

    elif cmd in ("memoria", "jogo-memoria", "memory"):
        await minigames.handle_memoria(message, args)
        return

    elif cmd in ("memoria-responder", "memoria-resposta", "responder-memoria"):
        await minigames.handle_memoria_responder(message, args)
        return

    elif cmd in ("jogos", "games", "minigames"):
        await minigames.handle_jogos(message, args)
        return

    # ── AUTO-MOD ───────────────────────────────────────────────────────────────
    elif cmd in ("automod", "auto-mod", "automod-config"):
        await automod.handle_automod_config(message, args)
        return

    elif cmd in ("automod-stats", "automod-estatisticas"):
        await automod.handle_automod_stats(message, args)
        return

    # ── COMANDOS PERSONALIZADOS ─────────────────────────────────────────────
    elif cmd in ("criar-comando", "custom-create", "new-command"):
        await custom_commands.handle_criar_comando(message, args)
        return

    elif cmd in ("deletar-comando", "delete-command", "remove-command"):
        await custom_commands.handle_deletar_comando(message, args)
        return

    elif cmd in ("listar-comandos", "custom-list", "list-commands"):
        await custom_commands.handle_listar_comandos(message, args)
        return

    elif cmd in ("editar-comando", "edit-command", "update-command"):
        await custom_commands.handle_editar_comando(message, args)
        return

    elif cmd in ("info-comando", "command-info"):
        await custom_commands.handle_info_comando(message, args)
        return

    # Verificar comandos personalizados antes de continuar
    if await custom_commands.execute_custom_command(message, cmd):
        return

    # ── RECOMPENSAS DE NÍVEL ───────────────────────────────────────────────
    elif cmd in ("rewards", "recompensas", "level-rewards"):
        await level_rewards.handle_rewards(message, args)
        return

    elif cmd in ("claim-reward", "reivindicar", "pegar-recompensa"):
        await level_rewards.handle_claim_reward(message, args)
        return

    elif cmd in ("my-rewards", "minhas-recompensas", "recompensas-pendentes"):
        await level_rewards.handle_my_rewards(message, args)
        return

    elif cmd in ("add-reward", "adicionar-recompensa"):
        await level_rewards.handle_add_reward(message, args)
        return

    # ── PROTEÇÃO IMPERIAL ───────────────────────────────────
    elif cmd in ("protecao-imperial", "protecaoimperial", "config-protecao"):
        await protecao_parcerias.cmd_protecao_imperial(message)
        return

    elif cmd in ("ativar-protecao", "ativarprotecao", "enable-protection"):
        await protecao_parcerias.cmd_ativar_protecao(message)
        return

    elif cmd in ("desativar-protecao", "desativarprotecao", "disable-protection"):
        await protecao_parcerias.cmd_desativar_protecao(message)
        return

    elif cmd in ("confianca", "confiança", "trust", "add-trust"):
        if args and message.mentions:
            await protecao_parcerias.cmd_confianca(message, message.mentions[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi confianca @usuario*", 0x6B0000))
        return

    elif cmd in ("remover-confianca", "removerconfianca", "remove-trust"):
        if args and message.mentions:
            await protecao_parcerias.cmd_remover_confianca(message, message.mentions[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi remover-confianca @usuario*", 0x6B0000))
        return

    elif cmd in ("whitelist-fantasma", "whitelistfantasma", "ghost-whitelist", "whitelist-add", "whitelistadd"):
        if args and message.mentions:
            await protecao_parcerias.cmd_whitelist_fantasma(message, message.mentions[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi whitelist-fantasma @usuario*", 0x6B0000))
        return

    elif cmd in ("remover-whitelist-fantasma", "removerwhitelistfantasma", "remove-ghost-whitelist", "whitelist-remove", "whitelistremove"):
        if args and message.mentions:
            await protecao_parcerias.cmd_remover_whitelist_fantasma(message, message.mentions[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi remover-whitelist-fantasma @usuario*", 0x6B0000))
        return

    elif cmd in ("listar-whitelist-fantasma", "listarwhitelistfantasma", "list-ghost-whitelist", "whitelist-list", "whitelistlist"):
        await protecao_parcerias.cmd_listar_whitelist_fantasma(message)
        return

    elif cmd in ("criar-backup", "criarbackup", "create-backup", "backup-protecao", "backupprotecao"):
        await protecao_parcerias.cmd_criar_backup(message)
        return

    elif cmd in ("listar-backups", "listarbackups", "list-backups"):
        await protecao_parcerias.cmd_listar_backups(message)
        return

    elif cmd in ("restaurar-backup", "restaurarbackup", "restore-backup"):
        if args:
            await protecao_parcerias.cmd_restaurar_backup(message, args[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi restaurar-backup [nome do arquivo]*", 0x6B0000))
        return

    elif cmd in ("logs-protecao", "logsprotecao", "protection-logs"):
        filtro = args[0] if args else None
        await protecao_parcerias.cmd_logs_protecao(message, filtro)
        return

    elif cmd in ("estatisticas-protecao", "estatisticasprotecao", "protection-stats", "stats-protecao"):
        await protecao_parcerias.cmd_estatisticas_protecao(message)
        return

    elif cmd in ("config-canal-alertas", "configcanalalertas", "config-alert-channel"):
        if message.channel_mentions:
            await protecao_parcerias.cmd_config_canal_alertas(message, message.channel_mentions[0])
        else:
            await protecao_parcerias.cmd_config_canal_alertas(message, None)
        return

    elif cmd in ("limpar-logs", "limparlogs", "clear-logs"):
        if args:
            try:
                dias = int(args[0])
                await protecao_parcerias.cmd_limpar_logs(message, dias)
            except ValueError:
                await message.channel.send(embed=embed_imperial("❌ Valor Inválido", "*Use: tenshi limpar-logs [dias]*", 0x6B0000))
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi limpar-logs [dias]*", 0x6B0000))
        return

    elif cmd in ("relatorio-protecao", "relatorioprotecao", "protection-report"):
        await protecao_parcerias.cmd_relatorio_protecao(message)
        return

    elif cmd in ("resetar-estatisticas", "resetarestatisticas", "reset-stats"):
        await protecao_parcerias.cmd_resetar_estatisticas(message)
        return

    elif cmd in ("modo-teste", "modoteste", "test-mode"):
        await protecao_parcerias.cmd_modo_teste(message)
        return

    elif cmd in ("bloquear-servidor", "bloquearservidor", "block-server"):
        if args:
            try:
                guild_id = int(args[0])
                await protecao_parcerias.cmd_bloquear_servidor(message, guild_id)
            except ValueError:
                await message.channel.send(embed=embed_imperial("❌ ID Inválido", "*Use: tenshi bloquear-servidor [id do servidor]*", 0x6B0000))
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi bloquear-servidor [id do servidor]*", 0x6B0000))
        return

    elif cmd in ("desbloquear-servidor", "desbloquearservidor", "unblock-server"):
        if args:
            try:
                guild_id = int(args[0])
                await protecao_parcerias.cmd_desbloquear_servidor(message, guild_id)
            except ValueError:
                await message.channel.send(embed=embed_imperial("❌ ID Inválido", "*Use: tenshi desbloquear-servidor [id do servidor]*", 0x6B0000))
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi desbloquear-servidor [id do servidor]*", 0x6B0000))
        return

    elif cmd in ("atividade-suspeita", "atividadesuspeita", "suspicious-activity"):
        if args and message.mentions:
            await protecao_parcerias.cmd_atividade_suspeita(message, message.mentions[0])
        else:
            await protecao_parcerias.cmd_atividade_suspeita(message, None)
        return

    elif cmd in ("teste-protecao", "testeprotecao", "test-protection"):
        if args and message.mentions:
            await protecao_parcerias.cmd_teste_protecao(message, message.mentions[0])
        else:
            await protecao_parcerias.cmd_teste_protecao(message, None)
        return

    # ── SISTEMA DE PARCERIAS ────────────────────────────────
    elif cmd in ("parceria", "partnership", "create-partnership"):
        if args:
            await protecao_parcerias.cmd_parceria(message, args[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi parceria [link de convite]*", 0x6B0000))
        return

    elif cmd in ("historico-parcerias", "historicoparcerias", "partnership-history"):
        await protecao_parcerias.cmd_historico_parcerias(message)
        return

    # ── MODERAÇÃO DE CONTEÚDO ───────────────────────────────
    elif cmd in ("config-moderacao", "configmoderacao", "moderation-config"):
        await moderacao_conteudo.cmd_config_moderacao(message)
        return

    elif cmd in ("bloquear-link", "bloquearlink", "block-link"):
        if args:
            await moderacao_conteudo.cmd_bloquear_link(message, args[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi bloquear-link [url]*", 0x6B0000))
        return

    elif cmd in ("desbloquear-link", "desbloquearlink", "unblock-link"):
        if args:
            await moderacao_conteudo.cmd_desbloquear_link(message, args[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi desbloquear-link [url]*", 0x6B0000))
        return

    elif cmd in ("adicionar-dominio-confianca", "adicionardominioconfianca", "add-trusted-domain"):
        if args:
            await moderacao_conteudo.cmd_adicionar_dominio_confianca(message, args[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi adicionar-dominio-confianca [dominio]*", 0x6B0000))
        return

    elif cmd in ("remover-dominio-confianca", "removerdominioconfianca", "remove-trusted-domain"):
        if args:
            await moderacao_conteudo.cmd_remover_dominio_confianca(message, args[0])
        else:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi remover-dominio-confianca [dominio]*", 0x6B0000))
        return

    elif cmd in ("add-reward-item", "adicionar-item-recompensa"):
        await level_rewards.handle_add_reward_item(message, args)
        return

    elif cmd in ("reset-rewards", "resetar-recompensas"):
        await level_rewards.handle_reset_rewards(message, args)
        return

    # ── SISTEMA DE EVENTOS ─────────────────────────────────────────────────
    elif cmd in ("create-event", "criar-evento", "novo-evento"):
        await event_system.handle_create_event(message, args)
        return

    elif cmd in ("schedule-event", "agendar-evento"):
        await event_system.handle_schedule_event(message, args)
        return

    elif cmd in ("list-events", "listar-eventos", "eventos"):
        await event_system.handle_list_events(message, args)
        return

    elif cmd in ("join-event", "entrar-evento", "participar"):
        await event_system.handle_join_event(message, args)
        return

    elif cmd in ("event-info", "info-evento"):
        await event_system.handle_event_info(message, args)
        return

    elif cmd in ("end-event", "finalizar-evento"):
        await event_system.handle_end_event(message, args)
        return

    elif cmd in ("delete-event", "deletar-evento"):
        await event_system.handle_delete_event(message, args)
        return

    # ── FACÇÕES ───────────────────────────────────────────────────────────────
    elif cmd in ("entrar", "faccao", "facção"):
        await faccoes.handle_entrar_faccao(message, args)
        return

    elif cmd in ("ranking", "top-faccoes"):
        await faccoes.handle_ranking_faccoes(message)
        return

    # ── MODERAÇÃO ─────────────────────────────────────────────────────────────
    elif cmd in ("decreto",):
        await moderacao.handle_decreto(message, args)
        return

    elif cmd in ("promover",):
        await moderacao.handle_promover_cargo(message, args)
        return

    elif cmd in ("criar-cargo", "cargo-imperial", "novo-cargo"):
        await moderacao.handle_criar_cargo_imperial(message, args)
        return

    elif cmd in ("criar-secoes-cargos", "criar-seções-cargos", "separar-cargos"):
        await cargos_admin.handle_criar_secoes_cargos(message, args)
        return

    elif cmd in ("cargos-servidor", "listar-cargos", "roles"):
        await cargos_admin.handle_cargos_servidor(message, args)
        return

    elif cmd in ("mapear-cargos", "sincronizar-cargos"):
        await cargos_admin.handle_mapear_cargos(message, args)
        return

    elif cmd in ("auditoria-cargos", "auditoria-cargos-ia", "organizar-cargos-ia", "organizar-servidor-ia"):
        await cargos_admin.handle_auditoria_cargos_ia(message, args)
        return

    elif cmd in ("cargo-info", "info-cargo"):
        await cargos_admin.handle_cargo_info(message, args)
        return

    elif cmd in ("funcao-cargo", "função-cargo", "definir-funcao-cargo"):
        await cargos_admin.handle_funcao_cargo(message, args)
        return

    elif cmd in ("publicar-mapa-cargos", "manual-cargos"):
        await cargos_admin.handle_publicar_mapa(message, args)
        return

    elif cmd in ("auditoria-permissoes", "auditoria-permissões", "checar-permissoes", "checar-permissões"):
        await permissoes_canais.handle_auditoria_permissoes(message, args)
        return

    elif cmd in ("corrigir-permissoes-bot", "corrigir-permissões-bot", "arrumar-permissoes-bot"):
        await permissoes_canais.handle_corrigir_permissoes_bot(message, args)
        return

    elif cmd in ("mapa-canais", "mapa-chats", "estrutura-chats"):
        await permissoes_canais.handle_mapa_canais(message, args)
        return

    elif cmd in ("aplicar-perfil-canal", "perfil-canal", "organizar-chat"):
        await permissoes_canais.handle_aplicar_perfil_canal(message, args)
        return

    elif cmd in ("punir-audacia", "punir"):
        await moderacao.handle_punir_audacia(message, args)
        return

    elif cmd in ("julgamento", "julgar", "trial"):
        await moderacao.handle_julgamento(message, args)
        return

    elif cmd in ("masmorra-prender", "prender", "masmorrar"):
        await moderacao.handle_prender(message, args)
        return

    elif cmd in ("exilar",):
        await moderacao.handle_exilar(message, args)
        return

    elif cmd in ("anistia-real", "anistia"):
        await moderacao.handle_anistia(message)
        return

    elif cmd in ("trancar-portoes", "lockdown"):
        await moderacao.handle_lockdown(message)
        return

    elif cmd in ("tesouro",):
        await moderacao.handle_tesouro(message, args)
        return

    elif cmd in ("veto",):
        await moderacao.handle_veto(message, args)
        return

    elif cmd == "ban":
        await moderacao.handle_ban(message, args)
        return

    elif cmd == "kick":
        await moderacao.handle_kick(message, args)
        return

    elif cmd == "mute":
        await moderacao.handle_mute(message, args)
        return

    elif cmd in ("unmute", "desmutar", "dessilenciar"):
        await moderacao.handle_unmute(message, args)
        return

    elif cmd in ("unban", "desbanir"):
        await moderacao.handle_unban(message, args)
        return

    elif cmd in ("slowmode", "modo-lento"):
        await moderacao.handle_slowmode(message, args)
        return

    elif cmd in ("clear", "limpar", "purge"):
        await moderacao.handle_clear(message, args)
        return

    elif cmd in ("nota",):
        await infractions.handle_nota(message, args)
        return

    elif cmd in ("aviso",):
        await infractions.handle_aviso(message, args)
        return

    elif cmd in ("notas", "infracoes", "infrações"):
        await infractions.handle_notas(message, args)
        return

    elif cmd in ("info", "informacoes", "informações", "perfil-completo"):
        await infractions.handle_info(message, args)
        return

    # ── CONDOMÍNIO AVANÇADO ───────────────────────────────────────────────────
    elif cmd in ("trancar-casa", "trancar_casa", "lock-casa"):
        await avancado.handle_trancar_casa(message)
        return

    elif cmd in ("destrancar-casa", "destrancar_casa", "unlock-casa"):
        await avancado.handle_destrancar_casa(message)
        return

    # ── GARAGEM & VEÍCULOS ────────────────────────────────────────────────────
    elif cmd in ("garagem", "veiculos", "veículos", "meu-veiculo"):
        await avancado.handle_garagem(message)
        return

    elif cmd in ("vender-veiculo", "vender-veículo", "vender_veiculo"):
        await avancado.handle_vender_veiculo(message)
        return

    # ── ESPORTES ──────────────────────────────────────────────────────────────
    elif cmd in ("basquete", "basketball"):
        await avancado.handle_esporte(message, args, "basquete")
        return

    elif cmd in ("futebol", "football", "soccer"):
        await avancado.handle_esporte(message, args, "futebol")
        return

    # ── POOL PARTY ────────────────────────────────────────────────────────────
    elif cmd in ("pool-party", "poolparty", "festa-piscina"):
        await avancado.handle_pool_party(message)
        return

    # ── PETS ──────────────────────────────────────────────────────────────────
    elif cmd in ("pet-shop", "petshop", "loja-pets"):
        await avancado.handle_petshop(message)
        return

    elif cmd in ("meu-pet", "meupet", "pet"):
        await avancado.handle_meu_pet(message)
        return

    elif cmd in ("vender-pet", "venderpet"):
        await avancado.handle_vender_pet(message)
        return

    # ── CASAMENTO & DIVÓRCIO ──────────────────────────────────────────────────
    elif cmd in ("casar", "pedido", "noivado", "marry"):
        await matrimonio.handle_pedido_comum(message, args)
        return

    elif cmd in ("pedido-real", "pedido_rei", "pedido-rei", "noivado-real"):
        await matrimonio.handle_pedido_real(message, args)
        return

    elif cmd in ("cerimonia", "cerimônia", "configurar-casamento", "agendar-casamento"):
        await matrimonio.handle_configurar_cerimonia(message, args)
        return

    elif cmd in ("iniciar-cerimonia", "iniciar-cerimônia", "celebrar-casamento"):
        await matrimonio.handle_iniciar_cerimonia(message, args)
        return

    elif cmd in ("rito-real", "casamento-real", "matrimonio-real", "matrimônio-real"):
        await matrimonio.handle_rito_real(message, args)
        return

    elif cmd in ("registro-casamento", "certidao-casamento", "certidão-casamento"):
        await matrimonio.handle_registro_casamento(message, args)
        return

    elif cmd in ("abandonar-preparacao", "abandonar-cerimonia", "abandonar-pedido"):
        await matrimonio.handle_abandonar_preparacao(message, args)
        return

    elif cmd in ("cancelar-casamento", "cancelar-pedido", "anular-pedido"):
        await matrimonio.handle_cancelar_casamento_usuario(message, args)
        return

    elif cmd in ("anular-casamento", "anular-uniao", "anular-união", "dissolver-casamento"):
        await matrimonio.handle_cancelar_casamento_admin(message, args)
        return

    elif cmd in ("divorcio", "divórcio", "separar", "divorce"):
        await social_cog.handle_divorcio(message)
        return

    # ── LAVANDERIA ────────────────────────────────────────────────────────────
    elif cmd in ("lavanderia", "lavar-itens", "limpeza"):
        await social_cog.handle_lavanderia(message)
        return

    # ── LABORATÓRIO ───────────────────────────────────────────────────────────
    elif cmd in ("sintetizar", "craftar", "fabricar", "sintetisar"):
        await social_cog.handle_sintetizar(message, args)
        return

    # ── CINEMA ────────────────────────────────────────────────────────────────
    elif cmd in ("cartaz", "cinema", "sessao", "sessão", "agendar-filme"):
        await social_cog.handle_cartaz(message, args)
        return

    # ── CRIME & BECO ──────────────────────────────────────────────────────────
    elif cmd in ("assaltar", "roubar", "furtar"):
        await crime_cog.handle_assaltar(message, args)
        return

    elif cmd in ("mercado-negro-beco", "beco-mercado"):
        await crime_cog.handle_mercado_beco(message)
        return

    elif cmd in ("jornal-policial", "noticias-policiais", "boletim-policial"):
        await crime_cog.handle_jornal_policial(message, args)
        return

    elif cmd in ("interagir-local", "interacao-local", "interação-local"):
        await locais.handle_interagir_local(message, args)
        return

    elif cmd in ("cassino", "jogos-cassino", "apostar"):
        await locais.handle_cassino(message, args)
        return

    elif cmd in ("zoologico", "zoológico", "visitar-zoologico"):
        await locais.handle_zoologico(message, args)
        return

    elif cmd in ("terminar-interacao", "terminar-interação", "encerrar-interacao"):
        await locais.handle_terminar_interacao(message, args)
        return

    elif cmd in ("concurso-publico", "concurso-público", "concurso-policial", "concurso-juridico"):
        await locais.handle_concurso(message, args)
        return

    # ── COTIDIANO ─────────────────────────────────────────────────────────────
    elif cmd in ("jornal-cotidiano", "jornal-dia", "cronica-dia", "crônica-dia"):
        await cotidiano.handle_cronica_diaria(message)
        return

    elif cmd in ("psicologo", "psicólogo", "terapia", "desabafar"):
        await cotidiano.handle_psicologo(message, args)
        return

    elif cmd in ("beber", "bar", "bebida"):
        await cotidiano.handle_beber(message, args)
        return

    elif cmd in ("clima-atual", "meteorologia", "tempo-atual"):
        await cotidiano.handle_clima(message)
        return

    # ── CORREIO ANÔNIMO ───────────────────────────────────────────────────────
    elif cmd in ("criar-correio", "painel-correio", "correio"):
        await correio_cog.handle_criar_correio(message)
        return

    # ── ESTAÇÕES ──────────────────────────────────────────────────────────────
    elif cmd in ("estacoes", "estações", "estacao", "estação", "temporada"):
        await temporadas.handle_estacoes(message)
        return

    # ── ENTREVISTA DE EMPREGO ─────────────────────────────────────────────────
    elif cmd in ("entrevista", "entrevista-emprego", "candidatar"):
        await temporadas.handle_entrevista(message, args)
        return

    # ── EMERGÊNCIAS MÉDICAS ───────────────────────────────────────────────────
    elif cmd in ("socorrer", "atender", "salvar"):
        await temporadas.handle_socorrer(message, args)
        return

    # ── CLERO ─────────────────────────────────────────────────────────────────
    elif cmd in ("padre", "clero", "liturgia", "rito"):
        await clero_cog.handle_padre(message, args)
        return

    elif cmd in ("sindicancia", "sindicância", "investigar-usuario"):
        await clero_cog.handle_sindicancia(message, args)
        return

    elif cmd in ("consultar-lei", "codigo-imperial", "código-imperial", "lei"):
        await governanca_ia.handle_consultar_lei(message, args)
        return

    elif cmd in ("parecer-ia", "ia-admin", "oraculo-admin", "oráculo-admin"):
        await governanca_ia.handle_parecer_ia(message, args)
        return

    elif cmd in ("plano-admin", "governar-ia", "administrar-ia"):
        await governanca_ia.handle_plano_admin(message, args)
        return

    # ── JURÍDICO ──────────────────────────────────────────────────────────────
    elif cmd in ("ficha-criminal", "ficha_criminal", "historico-criminal"):
        await juridico.handle_ficha_criminal(message, args)
        return

    elif cmd in ("perdoar-aviso", "perdoar_aviso", "remover-warn"):
        await juridico.handle_perdoar_aviso(message, args)
        return

    elif cmd in ("warn", "advertir", "advertencia", "advertência"):
        await juridico.handle_warn(message, args)
        return

    # ── INTELIGÊNCIA ──────────────────────────────────────────────────────────
    elif cmd in ("subornar-porteiro", "suborno-porteiro", "espionar-casa"):
        await intel.handle_subornar_porteiro(message, args)
        return

    elif cmd in ("grampear-call", "grampo", "monitorar-call"):
        await intel.handle_grampear_call(message)
        return

    elif cmd in ("iniciar-festa", "festa", "comecar-festa", "começar-festa"):
        await intel.handle_iniciar_festa(message, args)
        return

    elif cmd in ("registrar-perola", "perola", "pérola", "salvar-rp"):
        await intel.handle_registrar_perola(message, args)
        return

    elif cmd in ("vdd", "verdade-ou-desafio", "verdade-desafio"):
        await intel.handle_vdd(message)
        return

    elif cmd in ("chat", "perguntar", "assistente", "tenshi-ia"):
        await assistente_ia.handle_chat(message, args)
        return

    # ── UTILITÁRIOS ───────────────────────────────────────────────────────────
    elif cmd in ("ajuda", "help", "comandos", "menu"):
        await enviar_ajuda(message)
        return

    elif cmd in ("ping", "latencia"):
        lat = round(bot.latency * 1000)
        cor = 0x006400 if lat < 100 else 0xFF8C00 if lat < 200 else 0x8B0000
        await message.channel.send(embed=embed_imperial(
            "🏓 Latência Imperial",
            f"*As ondas etéreas de Tenshi respondem...*\n{SEP}\n\n**`{lat}ms`**",
            cor
        ))
        return

    elif cmd in ("top", "leaderboard", "podio"):
        await _handle_top(message)
        return

    elif cmd in ("servidor", "server", "guild"):
        await _handle_servidor(message)
        return

    elif cmd in ("backup",):
        await _handle_backup(message)
        return

    elif cmd in ("bandeira", "brasao", "brasão", "simbolo", "símbolo", "estandarte"):
        await _handle_bandeira(message)
        return

    elif cmd in ("historia-tenshi", "história-tenshi", "base-historica", "base-histórica", "origem-tenshi"):
        await _handle_historia_tenshi(message)
        return

    elif cmd in ("biblioteca-imperial", "biblioteca", "documentos-imperiais"):
        await biblioteca_imperial.handle_biblioteca(message, args)
        return

    elif cmd in ("documento", "pdf", "pergaminho"):
        await biblioteca_imperial.handle_documento(message, args)
        return

    elif cmd in ("memoria-imperial", "memória-imperial", "consultar-memoria", "consultar-memória"):
        await biblioteca_imperial.handle_memoria(message, args)
        return

    elif cmd in ("aula-imperial", "aula", "ensinar"):
        await biblioteca_imperial.handle_aula_imperial(message, args)
        return

    elif cmd in ("missao-historica", "missão-histórica", "missao-histórica", "missão-historica"):
        await biblioteca_imperial.handle_missao_historica(message, args)
        return

    elif cmd in ("juramento-tenshi", "juramento", "voto-tenshi"):
        await biblioteca_imperial.handle_juramento_tenshi(message, args)
        return

    elif cmd in ("protocolo-imperial", "protocolo"):
        await biblioteca_imperial.handle_protocolo_imperial(message, args)
        return

    elif cmd in ("quiz-imperial", "quiz-tenshi", "quiz"):
        await biblioteca_imperial.handle_quiz_imperial(message, args)
        return

    elif cmd in ("aniversario", "aniversário", "birthday"):
        anos = _utcnow().year - FUNDACAO_TENSHI.year
        await _anunciar_aniversario(anos)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 15 — PRERROGATIVAS SOBERANAS (todos exigem IMPERADOR_ID ou co_soberano)
    # ══════════════════════════════════════════════════════════════════════════

    # ── A) Controle Monetário ─────────────────────────────────────────────────
    elif cmd in ("emitir-moeda", "emitir_moeda", "emitir-moedas"):
        await soberano.cmd_emitir_moeda(message, args)
        return

    elif cmd in ("confiscar-fortuna", "confiscar_fortuna"):
        await soberano.cmd_confiscar_fortuna(message, args)
        return

    elif cmd in ("congelar-banco", "congelar_banco"):
        await soberano.cmd_congelar_banco(message, args)
        return

    elif cmd in ("perdoar-divida", "perdoar_divida", "perdoar-dívida"):
        await soberano.cmd_perdoar_divida(message, args)
        return

    elif cmd in ("isencao-fiscal", "isenção-fiscal", "isencao_fiscal"):
        await soberano.cmd_isencao_fiscal(message, args)
        return

    # ── B) Manipulação do RPG ─────────────────────────────────────────────────
    elif cmd in ("set-status", "set_status", "setstatus"):
        await soberano.cmd_set_status(message, args)
        return

    elif cmd in ("apagar-ficha", "apagar_ficha", "deletar-ficha"):
        await soberano.cmd_apagar_ficha(message, args)
        return

    elif cmd in ("conceder-item", "conceder_item", "dar-item"):
        await soberano.cmd_conceder_item(message, args)
        return

    elif cmd in ("purificar-status", "purificar_status", "cure"):
        await soberano.cmd_purificar_status(message, args)
        return

    elif cmd in ("imortalidade",):
        await soberano.cmd_imortalidade(message, args)
        return

    # ── C) Decretos de Estado ─────────────────────────────────────────────────
    elif cmd in ("estado-de-sitio", "estado_de_sitio", "sitio"):
        await soberano.cmd_estado_de_sitio(message, args)
        return

    elif cmd in ("dissolver-mafia", "dissolver_mafia"):
        await soberano.cmd_dissolver_mafia(message, args)
        return

    elif cmd in ("estatizar-casa", "estatizar_casa"):
        await soberano.cmd_estatizar_casa(message, args)
        return

    elif cmd in ("silenciar-geral", "silenciar_geral"):
        await soberano.cmd_silenciar_geral(message, args)
        return

    elif cmd in ("anistia-geral", "anistia_geral"):
        await soberano.cmd_anistia_geral(message, args)
        return

    # ── D) Alta Justiça ───────────────────────────────────────────────────────
    elif cmd in ("exilio-supremo", "exilio_supremo", "banir-imperial"):
        await soberano.cmd_exilio_supremo(message, args)
        return

    elif cmd in ("perdao-judicial", "perdão-judicial", "perdao_judicial"):
        await soberano.cmd_perdao_judicial(message, args)
        return

    elif cmd in ("revogar-diploma", "revogar_diploma"):
        await soberano.cmd_revogar_diploma(message, args)
        return

    elif cmd in ("cassar-conjuge", "cassar-cônjuge", "cassar_conjuge"):
        await soberano.cmd_cassar_conjuge(message, args)
        return

    # ── E) IA e Conteúdo ──────────────────────────────────────────────────────
    elif cmd in ("atualizar-diretriz", "atualizar_diretriz"):
        await soberano.cmd_atualizar_diretriz(message, args)
        return

    elif cmd in ("apagar-memoria-ia", "apagar_memoria_ia", "limpar-ia"):
        await soberano.cmd_apagar_memoria_ia(message, args)
        return

    elif cmd in ("interceptar-correio", "interceptar_correio"):
        await soberano.cmd_interceptar_correio(message, args)
        return

    elif cmd in ("forçar-cronica", "forcar-cronica", "forcar_cronica"):
        await soberano.cmd_forcar_cronica(message, args)
        return

    # ── F) Engenharia e Manutenção ────────────────────────────────────────────
    elif cmd in ("desligar", "shutdown", "fechar"):
        await soberano.cmd_desligar(message, args)
        return

    elif cmd in ("forçar-pagamento", "forcar-pagamento", "forcar_pagamento"):
        await soberano.cmd_forcar_pagamento(message, args)
        return

    elif cmd in ("exportar-banco", "exportar_banco", "backup-db"):
        await soberano.cmd_exportar_banco(message, args)
        return

    elif cmd in ("bypass-cooldown", "bypass_cooldown"):
        await soberano.cmd_bypass_cooldown(message, args)
        return

    elif cmd in ("congelar-economia", "congelar_economia"):
        await soberano.cmd_congelar_economia(message, args)
        return

    elif cmd in ("censo-imperial", "censo_imperial"):
        await soberano.cmd_censo_imperial(message, args)
        return

    elif cmd in ("reset-era", "reset_era", "nova-era"):
        await soberano.cmd_reset_era(message, args)
        return

    elif cmd in ("irradiar", "transmissao-nacional", "transmissão-nacional"):
        await soberano.cmd_irradiar(message, args)
        return

    elif cmd in ("interdicao", "interdição", "interdicao-canal", "interditar"):
        await soberano.cmd_interdicao(message, args)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 13 A-B — GEOPOLÍTICA E IMIGRAÇÃO
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("dominar", "dominar-canal", "conquistar-territorio"):
        await geopolitica.handle_dominar(message, args)
        return

    elif cmd in ("territorio", "território", "status-territorio"):
        await geopolitica.handle_status_territorio(message, args)
        return

    elif cmd in ("rebeliao", "rebelião", "rebelar"):
        await geopolitica.handle_rebeliao(message, args)
        return

    elif cmd in ("visto", "painel-visto", "imigração", "imigracao"):
        await geopolitica.handle_painel_visto(message)
        return

    elif cmd in ("cidadania", "certidao", "certidão", "registro-civil"):
        await geopolitica.handle_cidadania(message, args)
        return

    elif cmd in ("exilio", "exílio", "exilio-temporario"):
        await geopolitica.handle_exilio_temporario(message, args)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 13 C-H + 14 — ESTADO, ECONOMIA, TRANSPORTE, SAÚDE
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("pedir-emprestimo", "pedir_emprestimo"):
        await estado.handle_emprestimo_banco(message, args)
        return

    elif cmd in ("quitar-divida",):
        await estado.handle_quitar(message, args)
        return

    elif cmd in ("lavar", "lavagem", "lavar-dinheiro"):
        await estado.handle_lavagem(message, args)
        return

    elif cmd in ("titulo-divida", "título-dívida", "titulo_divida"):
        await estado.handle_titulo_divida(message, args)
        return

    elif cmd in ("abastecer", "combustivel", "combustível", "recarregar-veiculo"):
        await estado.handle_abastecer(message, args)
        return

    elif cmd in ("mandado", "mandado-busca", "busca-e-apreensao"):
        await estado.handle_mandado(message, args)
        return

    elif cmd in ("auditoria-bancaria", "auditoria_bancaria", "auditoria-banco"):
        await estado.handle_auditoria_bancaria(message, args)
        return

    elif cmd in ("seguro-vida", "contratar-seguro", "seguro"):
        await estado.handle_contratar_seguro(message, args)
        return

    elif cmd in ("necrolo", "necrológio", "mural-mortos"):
        await estado.handle_necrolo(message, args)
        return

    elif cmd in ("aposentar", "aposentadoria", "fundo-pensao"):
        await estado.handle_aposentar(message, args)
        return

    elif cmd in ("diagnostico-ia", "diagnóstico-ia", "diagnostico_ia"):
        await estado.handle_diagnostico_ia(message, args)
        return

    elif cmd in ("buscar-protocolo", "buscar_protocolo"):
        await estado.handle_buscar_protocolo(message, args)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # PROTOCOLO 23 — SISTEMA DE ERAS DO TRONO
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("set-era", "set_era", "era-atual", "nova-era-trono"):
        await eras_cog.handle_set_era(message, args)
        return

    elif cmd in ("era", "era-status", "qual-era", "status-era"):
        await eras_cog.handle_era_atual(message)
        return

    elif cmd in ("decreto-marcial", "decreto_marcial"):
        await eras_cog.handle_decreto_marcial(message, args)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # PROTOCOLO 25 — METEOROLOGIA LOCALIZADA POR IA
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("clima", "checar-clima", "tempo"):
        await clima_cog.handle_clima(message, args)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 22 — TENSHI ACADEMY
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("matricular", "matricula", "matrícula", "inscrever-materia"):
        await academia.handle_matricular(message, args)
        return

    elif cmd in ("grade-academia", "grade_academia", "faculdades", "curriculo-academia", "curriculo"):
        await academia.handle_grade_academia(message, args)
        return

    elif cmd in ("certificado", "certificado-info", "diploma-info", "ver-certificado"):
        await academia.handle_certificado_info(message, args)
        return

    elif cmd in ("aptidao-academica", "aptidão-acadêmica", "avaliar-aptidao", "avaliar-aptidão"):
        await academia.handle_aptidao_academica(message, args)
        return

    elif cmd in ("trancar-matricula", "trancar_matricula", "cancelar-materia"):
        await academia.handle_trancar_matricula(message, args)
        return

    elif cmd in ("presença", "presenca", "registrar-presenca"):
        await academia.handle_presenca(message, args)
        return

    elif cmd in ("professor", "gerenciar-professor", "definir-professor"):
        await academia.handle_gerenciar_professor(message, args)
        return

    elif cmd in ("professores", "corpo-docente", "docentes"):
        await academia.handle_professores(message, args)
        return

    elif cmd in ("ministrar-aula", "dar-aula", "aula-professor"):
        await academia.handle_ministrar_aula(message, args)
        return

    elif cmd in ("iniciar-aula", "iniciar_aula"):
        await academia.handle_iniciar_aula(message, args)
        return

    elif cmd in ("ler-apostila", "apostila", "material-didatico"):
        await academia.handle_ler_apostila(message, args)
        return

    elif cmd in ("prestar-exame", "prestar_exame", "exame", "fazer-prova"):
        await academia.handle_prestar_exame(message, args)
        return

    elif cmd in ("historico-escolar", "histórico-escolar"):
        await academia.handle_historico_escolar(message, args)
        return

    elif cmd in ("segunda-via-diploma", "segunda_via_diploma", "revalidar-diploma"):
        await academia.handle_segunda_via_diploma(message, args)
        return

    elif cmd in ("entrar-clube", "entrar_clube", "filiacao-clube", "clube"):
        await academia.handle_entrar_clube(message, args)
        return

    elif cmd in ("cofre-clube", "cofres-clubes", "financas-clube"):
        await academia.handle_cofre_clube(message, args)
        return

    # ── Comandos Soberanos da Academia ────────────────────────────────────────
    elif cmd in ("interditar-escola", "interditar_escola"):
        await academia.cmd_interditar_escola(message, args)
        return

    elif cmd in ("aprovação-forçada", "aprovacao-forcada", "aprovacao_forcada"):
        await academia.cmd_aprovacao_forcada(message, args)
        return

    elif cmd in ("estatizar-cofre-clube", "estatizar_cofre_clube"):
        await academia.cmd_estatizar_cofre_clube(message, args)
        return

    elif cmd in ("zerar-historico-academico", "zerar_historico_academico"):
        await academia.cmd_zerar_historico_academico(message, args)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULOS 19-21 — INFRAESTRUTURA CRÍTICA, MACROECONOMIA, VIGILÂNCIA
    # ══════════════════════════════════════════════════════════════════════════

    # ── Energética e Inflação ─────────────────────────────────────────────────
    elif cmd in ("status-energia", "status_energia", "rede-eletrica"):
        await infra.handle_status_energia(message, args)
        return

    elif cmd in ("inflacao", "inflação", "status-inflacao", "indice-inflacao"):
        await infra.handle_status_inflacao(message, args)
        return

    # ── Mercado de Ações e Poupança ────────────────────────────────────────────
    elif cmd in ("comprar-acoes", "comprar_acoes", "acoes", "ações"):
        await infra.handle_comprar_acoes(message, args)
        return

    elif cmd in ("poupanca", "poupança", "investimento", "conta-poupanca"):
        await infra.handle_poupanca(message, args)
        return

    # ── Vigilância e OSINT ────────────────────────────────────────────────────
    elif cmd in ("checar-cameras", "checar_cameras", "dvr", "cameras"):
        await infra.handle_checar_cameras(message, args)
        return

    elif cmd in ("biometria", "dna", "registro-biometrico"):
        await infra.handle_biometria(message, args)
        return

    elif cmd in ("rastrear-perfil", "rastrear_perfil", "osint"):
        await infra.handle_rastrear_perfil(message, args)
        return

    # ── Logística e Cargas ────────────────────────────────────────────────────
    elif cmd in ("enviar-carga", "enviar_carga", "despachar-carga"):
        await infra.handle_enviar_carga(message, args)
        return

    # ── Saúde ─────────────────────────────────────────────────────────────────
    elif cmd in ("laudo-medico", "laudo_medico", "laudo"):
        await infra.handle_laudo_medico(message, args)
        return

    elif cmd in ("desintoxicacao", "desintoxicação", "detox"):
        await infra.handle_desintoxicacao(message, args)
        return

    elif cmd in ("doacao-sangue", "doação-sangue", "doar-sangue"):
        await infra.handle_doacao_sangue(message, args)
        return

    # ── Imóveis ───────────────────────────────────────────────────────────────
    elif cmd in ("titulo-propriedade", "título-propriedade", "escritura"):
        await infra.handle_titulo_propriedade(message, args)
        return

    elif cmd in ("historico-imovel", "histórico-imóvel", "historico_imovel"):
        await infra.handle_historico_imovel(message, args)
        return

    # ── Aluguel Comercial ─────────────────────────────────────────────────────
    elif cmd in ("alugar-comercio", "alugar_comercio", "alugar-comercial"):
        await infra.handle_alugar_comercio(message, args)
        return

    # ── Fiança ────────────────────────────────────────────────────────────────
    elif cmd in ("pagar-fianca", "pagar_fianca", "pagar-fiança"):
        await infra.handle_pagar_fianca(message, args)
        return

    # ── Diplomacia ────────────────────────────────────────────────────────────
    elif cmd in ("imunidade-diplomatica", "imunidade_diplomatica", "imunidade-consular"):
        await infra.handle_imunidade_diplomatica(message, args)
        return

    # ── Soberania Suprema (Módulos 19-21) ─────────────────────────────────────
    elif cmd in ("auditoria-geral-banco", "auditoria_geral_banco", "auditoria-absoluta"):
        await infra.cmd_auditoria_geral_banco(message, args)
        return

    elif cmd in ("expurgar-fichas-inativas", "expurgar_fichas_inativas", "limpar-fichas"):
        await infra.cmd_expurgar_fichas_inativas(message, args)
        return

    elif cmd in ("reset-parcial-economia", "reset_parcial_economia"):
        await infra.cmd_reset_parcial_economia(message, args)
        return

    elif cmd in ("bans-lista", "lista-exilados", "exilados"):
        await infra.cmd_bans_lista(message, args)
        return

    elif cmd in ("confiscar-veiculo", "confiscar_veiculo", "apreender-veiculo"):
        await infra.cmd_confiscar_veiculo(message, args)
        return

    elif cmd in ("decreto-climatico", "decreto_climatico", "forçar-clima"):
        await infra.cmd_decreto_climatico(message, args)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 30 — PSICOLOGIA ESTRATÉGICA & CONSELHEIRO IMPERIAL
    # ══════════════════════════════════════════════════════════════════════════
    elif cmd in ("aconselhar-estrategia", "aconselhar_estrategia",
                 "aconselhar-estratégia", "conselheiro", "conselho-estrategico"):
        await psicologia.handle_aconselhar(message, args)
        return

    # ── STATUS DOS MOTORES DE IA ───────────────────────────────────────────────
    elif cmd in ("status-ia", "status_ia", "motores-ia", "ia-status"):
        from ia_router import status_motores
        motores = status_motores()
        linhas = []
        for key, info in motores.items():
            icone = "🟢" if info["ativo"] else "🔴"
            linhas.append(f"{icone} **{key}** — `{info['modelo']}`")
        embed = discord.Embed(
            title="🧠 ⚙️ MOTORES DE IA — PAINEL IMPERIAL",
            description=(
                f"*Status em tempo real dos 8 motores de inteligência artificial.*\n{SEP}\n\n"
                + "\n".join(linhas) +
                f"\n\n{SEP}\n**🟢 Ativo** = chave configurada  •  **🔴 Inativo** = sem chave\n"
                f"Use `OPENROUTER_API_KEY` para manter a IA ativa."
            ),
            color=0x1A1A2E
        )
        embed.set_footer(text=f"⚙️ OpenRouter  •  {RODAPE_IMPERIAL}")
        await message.channel.send(embed=embed)
        return

    else:
        await message.channel.send(embed=embed_imperial(
            "❓ Não Reconhecido",
            f"*Os guardas imperiais não encontraram o pergaminho `{cmd}`...*\n\n"
            f"Use `Tenshi, ajuda` para ver todos os comandos disponíveis.",
            0x1a1a2e
        ))


# ─────────────────────────────────────────────────────────────────────────────
# Saudação automática ao Imperador
# ─────────────────────────────────────────────────────────────────────────────
async def _saudar_imperador_se_necessario(message):
    hoje = datetime.now().date().isoformat()
    chave = f"imperador-presenca:{hoje}"
    if chave in _imperador_saudado:
        return
    saudacoes = _carregar_saudacoes()
    if saudacoes.get("ultima_presenca_imperador") == hoje:
        _imperador_saudado.add(chave)
        return
    _imperador_saudado.add(chave)
    saudacoes["ultima_presenca_imperador"] = hoje
    saudacoes["ultimo_canal"] = str(message.channel.id)
    _salvar_saudacoes(saudacoes)
    embed = discord.Embed(
        title="⚜️ 👑 O IMPERADOR RETORNA 👑 ⚜️",
        description=(
            f"*Uma aura dourada envolve o salão... o cosmos se curva...*\n{SEP}\n\n"
            f"**Imperador Alloy** ilumina novamente os domínios de Tenshi.\n"
            f"*Que sua presença divina abençoe todos os súditos desta corte.*\n\n{SEP}"
        ),
        color=0xFFD700
    )
    embed.set_footer(text="👑 Alloy Tenshi — Soberano Supremo e Eterno")
    await message.channel.send(embed=embed)


# ─────────────────────────────────────────────────────────────────────────────
# Auxiliares
# ─────────────────────────────────────────────────────────────────────────────
async def _handle_top(message):
    from database import get_all_users
    todos = get_all_users()
    if not todos:
        await message.channel.send(embed=embed_imperial("📊 Pódio", "Nenhum guerreiro registrado.", 0x1a1a2e))
        return
    ordenados = sorted(todos.items(), key=lambda x: x[1].get("poder", 0), reverse=True)[:10]
    embed = discord.Embed(
        title="🏆 PÓDIO IMPERIAL — GUERREIROS DE TENSHI",
        description=f"*Os nomes gravados nos Pergaminhos Imortais...*\n{SEP}",
        color=0xFFD700
    )
    medalhas = ["🥇", "🥈", "🥉"]
    from cogs.especies import ESPECIES
    for i, (uid, u) in enumerate(ordenados):
        medalha = medalhas[i] if i < 3 else f"`#{i+1}`"
        try:
            membro = await bot.fetch_user(int(uid))
            nome = membro.display_name
        except Exception:
            nome = u.get("nome") or f"Súdito #{uid[-4:]}"
        especie_key = u.get("especie")
        esp_emoji = ESPECIES[especie_key]["emoji"] if especie_key and especie_key in ESPECIES else "🏛️"
        embed.add_field(
            name=f"{medalha} {esp_emoji} {nome}",
            value=(
                f"💥 **{u.get('poder',0)}** poder  •  "
                f"📊 Nv **{u.get('nivel',1)}**  •  "
                f"⚔️ **{u.get('vitorias_duelo',0)}** vitórias"
            ),
            inline=False
        )
    embed.set_footer(text=RODAPE_IMPERIAL)
    await message.channel.send(embed=embed)


async def _handle_servidor(message):
    guild = message.guild
    if not guild:
        return
    embed = discord.Embed(
        title=f"🏛️ {guild.name.upper()}",
        description=f"*Território sagrado do Império de Tenshi*\n{SEP}",
        color=0x2B0A3D
    )
    embed.add_field(name="👥 Membros", value=f"**{guild.member_count}**", inline=True)
    embed.add_field(name="📺 Canais",  value=f"**{len(guild.channels)}**", inline=True)
    embed.add_field(name="🎭 Cargos",  value=f"**{len(guild.roles)}**",   inline=True)
    embed.add_field(name="📅 Idade",   value=f"**{(discord.utils.utcnow() - guild.created_at).days}** dias", inline=True)
    if guild.owner:
        embed.add_field(name="👑 Governante", value=guild.owner.display_name, inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text=RODAPE_IMPERIAL)
    await message.channel.send(embed=embed)


async def _handle_backup(message):
    from database import CASAS_FILE, DB_FILE, EMPRESAS_FILE, FAMILIAS_FILE, _load
    stats = {
        "usuarios":        len(_load(DB_FILE)),
        "casas_ocupadas":  sum(1 for c in _load(CASAS_FILE).values() if c.get("dono")),
        "empresas":        len(_load(EMPRESAS_FILE)),
        "familias":        len(_load(FAMILIAS_FILE)),
    }
    embed = embed_imperial(
        "💾 BACKUP IMPERIAL",
        f"*Os Escribas preservaram os Pergaminhos Imortais...*\n{SEP}\n\n"
        f"👤 Usuários: **{stats['usuarios']}**\n"
        f"🏠 Casas ocupadas: **{stats['casas_ocupadas']}**\n"
        f"🏢 Empresas: **{stats['empresas']}**\n"
        f"👨‍👩‍👧 Organizações: **{stats['familias']}**\n\n"
        f"*Dados seguros nos servidores eternos de Tenshi.*",
        0x006400
    )
    await message.channel.send(embed=embed)


async def _handle_bandeira(message):
    embed = discord.Embed(
        title="⚜️ Bandeira Oficial da Família Tenshi",
        description=(
            f"*O estandarte da Casa Imperial Tenshi é erguido.*\n{SEP}\n\n"
            f"**Símbolo:** Elmo imperial, louros de vitória e o nome Tenshi.\n"
            f"**Uso:** identidade oficial da família, do Império e do bot.\n\n"
            f"*Onde esta bandeira aparece, a Casa Tenshi está presente.*"
        ),
        color=0x0D0D0D,
    )
    embed.set_footer(text=RODAPE_IMPERIAL)
    if os.path.exists(BANDEIRA_FILE):
        file = discord.File(BANDEIRA_FILE, filename="tenshi-bandeira.png")
        embed.set_image(url="attachment://tenshi-bandeira.png")
        await message.channel.send(file=file, embed=embed)
        return
    await message.channel.send(embed=embed)


async def _handle_historia_tenshi(message):
    from historia_tenshi import (
        FONTE_HISTORICA,
        HISTORIA_TOPICOS,
        PAGINAS_FONTE_HISTORICA,
    )

    embed = discord.Embed(
        title="📜 Bases Históricas do Império Tenshi",
        description=(
            f"*Resumo oficial contabilizado pelo bot.*\n{SEP}\n\n"
            f"**Fonte:** `{FONTE_HISTORICA}`\n"
            f"**Extensão:** {PAGINAS_FONTE_HISTORICA} páginas\n\n"
            f"*A IA usa esta base para manter a memória histórica do Império; em cerimônias, "
            f"usa apenas a versão essencial.*"
        ),
        color=0x9E7815,
    )
    for item in HISTORIA_TOPICOS[:6]:
        embed.add_field(name=item["tema"], value=item["texto"][:900], inline=False)
    embed.set_footer(text=RODAPE_IMPERIAL)
    if os.path.exists(BANDEIRA_FILE):
        file = discord.File(BANDEIRA_FILE, filename="tenshi-bandeira.png")
        embed.set_thumbnail(url="attachment://tenshi-bandeira.png")
        await message.channel.send(file=file, embed=embed)
        return
    await message.channel.send(embed=embed)


@bot.event
async def on_member_join(member):
    try:
        await aplicar_membro_inicial(member)
    except discord.Forbidden:
        print(f"[AVISO] Não foi possível aplicar o cargo Membro a {member}.")
    except discord.HTTPException as exc:
        print(f"[AVISO] Falha ao preparar parentesco de {member}: {exc}")

    canal = member.guild.system_channel
    if not canal:
        for ch in member.guild.text_channels:
            if ch.permissions_for(member.guild.me).send_messages:
                canal = ch
                break
    if not canal:
        return
    if member.id == IMPERADOR_ID:
        embed = discord.Embed(
            title="⚜️ 👑 O IMPERADOR RETORNA AO TRONO 👑 ⚜️",
            description=(
                f"*Os sinos dourados de Tenshi ecoam por todo o Império...*\n{SEP}\n\n"
                f"**Alloy Tenshi**, o Soberano Supremo e Eterno, pisa novamente nestas terras sagradas!\n\n"
                f"*Que todos os súditos se curvem diante de sua presença divina.*\n\n{SEP}"
            ),
            color=0xFFD700
        )
    else:
        embed = discord.Embed(
            title="🏛️ UM NOVO SÚDITO CHEGA A TENSHI",
            description=(
                f"*As trombetas imperiais anunciam {member.mention}...*\n{SEP}\n\n"
                f"Bem-vindo(a) aos domínios eternos do Império de Tenshi.\n\n"
                f"**Comece sua jornada:**\n"
                f"• `Tenshi, criar-ficha` — Crie seu personagem com espécie\n"
                f"• `Tenshi, status` — Ver seu perfil imperial\n"
                f"• `Tenshi, especies` — Ver todas as espécies\n"
                f"• Você recebeu o vínculo inicial **Membro**; a administração pode definir seu parentesco\n"
                f"• `Tenshi, ajuda` — Todos os pergaminhos\n\n{SEP}"
            ),
            color=0x2B0A3D
        )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=RODAPE_IMPERIAL)
    await canal.send(embed=embed)


@bot.event
async def on_member_remove(member):
    canal = member.guild.system_channel
    if canal:
        await canal.send(embed=embed_imperial(
            "💨 Um Súdito Parte",
            f"*{member.display_name} dissolve-se na névoa imperial...*\n\nSeus feitos permanecem nos Pergaminhos Eternos.",
            0x1a1a2e
        ))


@bot.event
async def on_disconnect():
    _salvar_status_bot(False)


@bot.event
async def on_error(event, *args, **kwargs):
    import traceback
    print(f"[ERRO] Evento: {event}")
    traceback.print_exc()


if __name__ == "__main__":
    _site_thread = start_site_server_thread(bot)
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("[ERRO] DISCORD_TOKEN nao encontrado no ambiente.")
        print("[ERRO] Configure DISCORD_TOKEN em Railway -> Variables e faca um redeploy.")
        sys.exit(1)
    else:
        try:
            bot.run(token)
        except discord.LoginFailure:
            print("[ERRO] Token do Discord invalido. Gere um novo token no Discord Developer Portal e atualize o .env.")
            raise
        except Exception as exc:
            if "Cannot connect to host discord.com:443" in str(exc) or "Acesso negado" in str(exc):
                print("[ERRO] O Windows bloqueou a conexao do Python com discord.com:443.")
                print("[ERRO] Libere o python.exe no Firewall/antivirus/proxy e tente iniciar novamente.")
            raise
        finally:
            _salvar_status_bot(False)
