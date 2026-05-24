import discord
import os
import sys
import asyncio
from datetime import datetime

# Garante que o diretório do main.py está no path, independente de onde
# o processo é iniciado (Render, Railway, Replit, etc.)
_base_dir = os.path.dirname(os.path.abspath(__file__))
if _base_dir not in sys.path:
    sys.path.insert(0, _base_dir)
os.chdir(_base_dir)

_cogs_dir = os.path.join(_base_dir, "cogs")
if not os.path.exists(_cogs_dir):
    print(f"Erro Crítico: A pasta cogs não foi encontrada em: {_cogs_dir}")
    sys.exit(1)

from keep_alive import keep_alive, set_bot
from utils import PREFIXO, embed_imperial, AJUDA_TEXTO, IMPERADOR_ID, SEP, RODAPE_IMPERIAL
from database import get_user, save_user

from cogs.rpg           import RPG
from cogs.economia      import Economia
from cogs.faccoes       import Faccoes
from cogs.mistico       import Mistico
from cogs.duelo         import Duelo
from cogs.eventos       import Eventos
from cogs.moderacao     import Moderacao
from cogs.loremaster    import LoreMaster
from cogs.casas         import Casas
from cogs.empresa       import Empresa
from cogs.financeiro    import Financeiro
from cogs.familia       import Familia
from cogs.perfil_config import PerfilConfig
from cogs.especies      import Especies
from cogs.poderes       import Poderes
from cogs.empregos      import Empregos
from cogs.vizinhanca    import Vizinhanca
from cogs.avancado     import Avancado
from cogs.social       import Social
from cogs.crime        import Crime
from cogs.cotidiano    import CotidianoCog
from cogs.correio      import Correio
from cogs.temporadas   import Temporadas
from cogs.clero        import Clero
from cogs.juridico     import Juridico
from cogs.inteligencia import Inteligencia
from cogs.soberano             import Soberano
from cogs.geopolitica          import Geopolitica
from cogs.estado               import Estado
from cogs.eras                 import Eras
from cogs.clima_ia             import ClimaIA
from cogs.academia             import Academia
from cogs.infraestrutura_critica import InfraestruturaCritica
from cogs.npcs                   import NPCs
from cogs.psicologia             import Psicologia
from cogs.ia                     import IA

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds   = True

bot = discord.Client(intents=intents)
set_bot(bot)

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
geopolitica = Geopolitica(bot)
estado      = Estado(bot)
eras_cog    = Eras(bot)
clima_cog   = ClimaIA(bot)
academia    = Academia(bot)
infra       = InfraestruturaCritica(bot)
npcs_cog    = NPCs(bot)
psicologia  = Psicologia(bot)
ia_cog      = IA(bot)

# ── Fundação de Tenshi ────────────────────────────────────────────────────────
FUNDACAO_TENSHI = datetime(2016, 6, 6)

_imperador_saudado: set = set()
_aniversario_anunciado: set = set()

# ── Guard 1: dedup por ID de mensagem (mesma msg processada 2x) ───────────────
from collections import deque as _deque
import time as _time

_seen_msg_ids: set = set()
_seen_msg_deque: _deque = _deque(maxlen=500)

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


@bot.event
async def on_ready():
    global _bg_tasks_initialized, _task_aniversario

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
        eventos.cog_load()
        vizinhanca.cog_load()
        cotidiano.cog_load()
        temporadas.cog_load()
        intel.cog_load()
        estado.cog_load()
        eras_cog.cog_load()
        clima_cog.cog_load()
        infra.cog_load()
        _task_aniversario = bot.loop.create_task(_loop_aniversario())
        print("✅ Tarefas de background inicializadas.")


async def _loop_aniversario():
    """Verifica diariamente se é aniversário de Tenshi (06/06)"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        agora = datetime.utcnow()
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
            f"**Aniversariante:** {datetime.utcnow().year}\n"
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
    if _ja_processou(message.id):
        return

    conteudo       = message.content.strip()
    conteudo_lower = conteudo.lower()

    # Saudação automática ao Imperador (apenas em mensagens sem prefixo de comando)
    if message.author.id == IMPERADOR_ID and not conteudo_lower.startswith(PREFIXO):
        await _saudar_imperador_se_necessario(message)

    # Invasão ativa
    if await eventos.processar_ataque_invasao(message):
        return

    # Verificar bloqueio (nocaute/prisão)
    if not conteudo_lower.startswith(PREFIXO):
        u_data = get_user(message.author.id)
        bloq   = u_data.get("bloqueado_ate")
        if bloq:
            try:
                from datetime import datetime as _dt
                if _dt.utcnow() < _dt.fromisoformat(bloq):
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
        await loremaster.handle_lore_natural(message, conteudo)
        return

    resto  = conteudo[len(PREFIXO):].strip()
    partes = resto.split()
    if not partes:
        return

    cmd  = partes[0].lower()
    args = partes[1:]

    # Guard 2 — cooldown 2s por usuário por comando
    if _em_cooldown(message.author.id, cmd):
        return

    # ══════════════════════════════════════════════════════════════════════════
    # ROTEADOR CENTRAL
    # ══════════════════════════════════════════════════════════════════════════

    # ── PERFIL & FICHA ────────────────────────────────────────────────────────
    if cmd in ("status", "perfil", "eu", "me"):
        await perfil_cfg.handle_status(message)

    elif cmd in ("ficha",):
        await perfil_cfg.handle_ficha(message, args)

    elif cmd in ("criar-ficha", "criarficha", "new-char", "novo-personagem", "registrar"):
        await especies.handle_criar_ficha(message)

    elif cmd in ("pegada", "vibe", "estilo", "tema"):
        await perfil_cfg.handle_pegada(message, args)

    elif cmd in ("inventario", "inventário", "inv"):
        await perfil_cfg.handle_inventario(message)

    elif cmd in ("conquistas", "achievements"):
        await perfil_cfg.handle_conquistas(message)

    # ── ESPÉCIES & LOCALIZAÇÃO ───────────────────────────────────────────────
    elif cmd in ("especies", "espécies", "racas", "raças"):
        await especies.handle_especies(message)

    elif cmd in ("viajar", "travel", "mover", "ir"):
        await especies.handle_viajar(message)

    elif cmd in ("local", "localizacao", "localização", "onde-estou", "mapa"):
        await especies.handle_meu_local(message)

    # ── PODERES DE RP ─────────────────────────────────────────────────────────
    elif cmd in ("poderes", "poder", "habilidades", "skills", "arvore"):
        await poderes_cog.handle_poderes(message)

    elif cmd in ("meus-poderes", "meuspoderes", "meus_poderes"):
        await poderes_cog.handle_meus_poderes(message)

    # ── RPG NARRATIVO ─────────────────────────────────────────────────────────
    elif cmd in ("treinar", "treino", "train"):
        await rpg.handle_treinar(message, args)

    elif cmd in ("missao", "missão", "mission"):
        await rpg.handle_missao(message, args)

    elif cmd in ("meditar", "meditate"):
        await rpg.handle_meditar(message)

    elif cmd in ("descansar", "rest"):
        await rpg.handle_descansar(message)

    elif cmd in ("trabalhar", "trabalho", "work"):
        # Atalho rápido para emprego
        await empregos.handle_emprego(message, args)

    elif cmd in ("emprego", "empregos", "jobs", "job"):
        if not args:
            await empregos.handle_trabalhos(message)
        else:
            await empregos.handle_emprego(message, args)

    elif cmd in ("profissao", "profissão", "classe"):
        await rpg.handle_profissao(message, args)

    elif cmd in ("interagir", "rp", "emote"):
        await rpg.handle_interagir(message, args)

    elif cmd in ("dado", "dice", "rolar"):
        await rpg.handle_dado(message, args)

    # ── LOREMASTER IA ─────────────────────────────────────────────────────────
    elif cmd in ("cronica", "crônica", "lore"):
        await loremaster.handle_cronica(message, args)

    elif cmd in ("evento-lore", "profecia"):
        await loremaster.handle_evento_lore(message)

    elif cmd in ("oraculo", "oráculo"):
        await loremaster.handle_oraculo(message, args)

    elif cmd in ("falar", "npc"):
        await loremaster.handle_falar(message, args)

    elif cmd in ("lore-historico", "cronicas-antigas"):
        await loremaster.handle_lore_historico(message)

    elif cmd in ("quadro-avisos", "avisos", "missoes-diarias"):
        await loremaster.handle_quadro_avisos(message)

    # ── MÍSTICO ───────────────────────────────────────────────────────────────
    elif cmd in ("tarot", "carta"):
        await mistico.handle_tarot(message)

    elif cmd in ("runa", "rune"):
        await mistico.handle_runa(message)

    elif cmd in ("astros", "constelacao", "horoscopo"):
        await mistico.handle_astros(message)

    elif cmd in ("destino",):
        await mistico.handle_destino(message, args)

    elif cmd in ("sacrificio", "sacrifício", "purificar"):
        await mistico.handle_sacrificio(message, args)

    elif cmd in ("ritual-protecao", "ritual"):
        await mistico.handle_ritual(message)

    # ── COMBATE ───────────────────────────────────────────────────────────────
    elif cmd in ("duelo", "duelar", "duel"):
        await duelo.handle_duelo(message, args)

    elif cmd in ("aceitar-duelo", "aceitar"):
        await duelo.handle_aceitar_duelo(message)

    elif cmd in ("invocar-chefe", "boss", "monstro"):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.administrator
        except: pass
        if tem_perm or message.author.id == IMPERADOR_ID:
            await eventos.iniciar_invasao(message.channel, args)
        else:
            await message.channel.send(embed=embed_imperial("🚫", "*Apenas administradores podem invocar criaturas.*", 0x6B0000))

    elif cmd in ("invasao", "invasão"):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.administrator
        except: pass
        if tem_perm or message.author.id == IMPERADOR_ID:
            await eventos.iniciar_invasao(message.channel)
        else:
            await message.channel.send(embed=embed_imperial("🚫", "*Apenas administradores podem iniciar invasões.*", 0x6B0000))

    # ── ECONOMIA ──────────────────────────────────────────────────────────────
    elif cmd in ("carteira", "saldo", "wallet", "moedas"):
        await economia.handle_carteira(message)

    elif cmd in ("mercado", "loja", "shop"):
        await economia.handle_loja(message)

    elif cmd in ("mercado-negro", "mercadonegro"):
        await economia.handle_mercado_negro(message)

    elif cmd in ("comprar", "compra", "buy"):
        await economia.handle_comprar(message, args)

    elif cmd in ("leilao", "leilão"):
        await economia.handle_leilao(message, args)

    elif cmd in ("sorteio-real", "sorteio", "giveaway"):
        await economia.handle_sorteio(message)

    # ── BANCO / FINANCEIRO ────────────────────────────────────────────────────
    elif cmd in ("banco", "bank", "extrato"):
        await financeiro.handle_banco(message)

    elif cmd in ("depositar", "deposit"):
        await financeiro.handle_depositar(message, args)

    elif cmd in ("sacar", "saque", "withdraw"):
        await financeiro.handle_sacar(message, args)

    elif cmd in ("transferir", "pagar", "pix"):
        await financeiro.handle_transferir(message, args)

    elif cmd in ("emprestimo", "empréstimo", "loan"):
        await financeiro.handle_emprestimo(message, args)

    elif cmd in ("pagar-divida", "pagardivida", "quitar"):
        await financeiro.handle_pagar_divida(message, args)

    elif cmd in ("historico", "histórico", "history"):
        await financeiro.handle_historico(message)

    # ── CASAS (mercado imobiliário geral) ─────────────────────────────────────
    elif cmd in ("casas", "imoveis", "propriedades"):
        await casas.handle_casas(message)

    elif cmd in ("minha-casa", "minhacasa", "meu-lar"):
        await casas.handle_minha_casa(message)

    elif cmd in ("vender-casa", "vendercasa"):
        await casas.handle_vender_casa(message)

    # ── VIZINHANÇA / CONDOMÍNIO ────────────────────────────────────────────────
    elif cmd in ("portaria", "condominio", "condomínio", "residencias"):
        await vizinhanca.handle_portaria(message)

    elif cmd in ("meu-lar-cond", "meuların", "residencia", "residência"):
        await vizinhanca.handle_meu_lar(message)

    elif cmd in ("convidar",):
        await vizinhanca.handle_convidar(message, args)

    elif cmd in ("expulsar",):
        await vizinhanca.handle_expulsar(message, args)

    elif cmd in ("devolver-casa", "devolvercasa", "sair-casa"):
        await vizinhanca.handle_devolver_casa(message)

    elif cmd in ("moradores", "vizinhos"):
        await vizinhanca.handle_moradores(message)

    elif cmd in ("cronica-cond", "fofoca", "crônica-cond"):
        await vizinhanca.handle_cronica_condominio(message)

    elif cmd in ("descansar-lazer", "descanso-lazer", "relaxar"):
        await vizinhanca.handle_descanso_lazer(message)

    # ── EMPRESA ───────────────────────────────────────────────────────────────
    elif cmd in ("empresa", "company", "corp", "enterprise", "negocio"):
        await empresa.handle_empresa(message, args)

    # ── FAMÍLIA / MÁFIA ───────────────────────────────────────────────────────
    elif cmd in ("familia", "família", "mafia", "máfia", "cla", "org"):
        await familia.handle_familia(message, args)

    # ── FACÇÕES ───────────────────────────────────────────────────────────────
    elif cmd in ("entrar", "faccao", "facção"):
        await faccoes.handle_entrar_faccao(message, args)

    elif cmd in ("ranking", "top-faccoes"):
        await faccoes.handle_ranking_faccoes(message)

    # ── MODERAÇÃO ─────────────────────────────────────────────────────────────
    elif cmd in ("decreto",):
        await moderacao.handle_decreto(message, args)

    elif cmd in ("promover",):
        await moderacao.handle_promover_cargo(message, args)

    elif cmd in ("punir-audacia", "punir"):
        await moderacao.handle_punir_audacia(message, args)

    elif cmd in ("julgamento", "julgar", "trial"):
        await moderacao.handle_julgamento(message, args)

    elif cmd in ("masmorra-prender", "prender", "masmorrar"):
        await moderacao.handle_prender(message, args)

    elif cmd in ("exilar",):
        await moderacao.handle_exilar(message, args)

    elif cmd in ("anistia-real", "anistia"):
        await moderacao.handle_anistia(message)

    elif cmd in ("trancar-portoes", "lockdown"):
        await moderacao.handle_lockdown(message)

    elif cmd in ("tesouro",):
        await moderacao.handle_tesouro(message, args)

    elif cmd in ("veto",):
        await moderacao.handle_veto(message, args)

    elif cmd == "ban":
        await moderacao.handle_ban(message, args)

    elif cmd == "kick":
        await moderacao.handle_kick(message, args)

    elif cmd == "mute":
        await moderacao.handle_mute(message, args)

    elif cmd in ("clear", "limpar", "purge"):
        await moderacao.handle_clear(message, args)

    # ── CONDOMÍNIO AVANÇADO ───────────────────────────────────────────────────
    elif cmd in ("trancar-casa", "trancar_casa", "lock-casa"):
        await avancado.handle_trancar_casa(message)

    elif cmd in ("destrancar-casa", "destrancar_casa", "unlock-casa"):
        await avancado.handle_destrancar_casa(message)

    # ── GARAGEM & VEÍCULOS ────────────────────────────────────────────────────
    elif cmd in ("garagem", "veiculos", "veículos", "meu-veiculo"):
        await avancado.handle_garagem(message)

    elif cmd in ("vender-veiculo", "vender-veículo", "vender_veiculo"):
        await avancado.handle_vender_veiculo(message)

    # ── ESPORTES ──────────────────────────────────────────────────────────────
    elif cmd in ("basquete", "basketball"):
        await avancado.handle_esporte(message, args, "basquete")

    elif cmd in ("futebol", "football", "soccer"):
        await avancado.handle_esporte(message, args, "futebol")

    # ── POOL PARTY ────────────────────────────────────────────────────────────
    elif cmd in ("pool-party", "poolparty", "festa-piscina"):
        await avancado.handle_pool_party(message)

    # ── PETS ──────────────────────────────────────────────────────────────────
    elif cmd in ("pet-shop", "petshop", "loja-pets"):
        await avancado.handle_petshop(message)

    elif cmd in ("meu-pet", "meupet", "pet"):
        await avancado.handle_meu_pet(message)

    elif cmd in ("vender-pet", "venderpet"):
        await avancado.handle_vender_pet(message)

    # ── CASAMENTO & DIVÓRCIO ──────────────────────────────────────────────────
    elif cmd in ("casar", "noivado", "marry"):
        await social_cog.handle_casar(message, args)

    elif cmd in ("divorcio", "divórcio", "separar", "divorce"):
        await social_cog.handle_divorcio(message)

    # ── LAVANDERIA ────────────────────────────────────────────────────────────
    elif cmd in ("lavanderia", "lavar-itens", "limpeza"):
        await social_cog.handle_lavanderia(message)

    # ── LABORATÓRIO ───────────────────────────────────────────────────────────
    elif cmd in ("sintetizar", "craftar", "fabricar", "sintetisar"):
        await social_cog.handle_sintetizar(message, args)

    # ── CINEMA ────────────────────────────────────────────────────────────────
    elif cmd in ("cartaz", "cinema", "sessao", "sessão", "agendar-filme"):
        await social_cog.handle_cartaz(message, args)

    # ── CRIME & BECO ──────────────────────────────────────────────────────────
    elif cmd in ("assaltar", "roubar", "furtar"):
        await crime_cog.handle_assaltar(message, args)

    elif cmd in ("mercado-negro-beco", "beco-mercado"):
        await crime_cog.handle_mercado_beco(message)

    # ── COTIDIANO ─────────────────────────────────────────────────────────────
    elif cmd in ("jornal-cotidiano", "jornal-dia", "cronica-dia", "crônica-dia"):
        await cotidiano.handle_cronica_diaria(message)

    elif cmd in ("psicologo", "psicólogo", "terapia", "desabafar"):
        await cotidiano.handle_psicologo(message, args)

    elif cmd in ("beber", "bar", "bebida"):
        await cotidiano.handle_beber(message, args)

    elif cmd in ("clima-atual", "meteorologia", "tempo-atual"):
        await cotidiano.handle_clima(message)

    # ── CORREIO ANÔNIMO ───────────────────────────────────────────────────────
    elif cmd in ("criar-correio", "painel-correio", "correio"):
        await correio_cog.handle_criar_correio(message)

    # ── ESTAÇÕES ──────────────────────────────────────────────────────────────
    elif cmd in ("estacoes", "estações", "estacao", "estação", "temporada"):
        await temporadas.handle_estacoes(message)

    # ── ENTREVISTA DE EMPREGO ─────────────────────────────────────────────────
    elif cmd in ("entrevista", "entrevista-emprego", "candidatar"):
        await temporadas.handle_entrevista(message, args)

    # ── EMERGÊNCIAS MÉDICAS ───────────────────────────────────────────────────
    elif cmd in ("socorrer", "atender", "salvar"):
        await temporadas.handle_socorrer(message, args)

    # ── CLERO ─────────────────────────────────────────────────────────────────
    elif cmd in ("padre", "clero", "liturgia", "rito"):
        await clero_cog.handle_padre(message, args)

    elif cmd in ("sindicancia", "sindicância", "investigar-usuario"):
        await clero_cog.handle_sindicancia(message, args)

    # ── JURÍDICO ──────────────────────────────────────────────────────────────
    elif cmd in ("ficha-criminal", "ficha_criminal", "historico-criminal"):
        await juridico.handle_ficha_criminal(message, args)

    elif cmd in ("perdoar-aviso", "perdoar_aviso", "remover-warn"):
        await juridico.handle_perdoar_aviso(message, args)

    elif cmd in ("warn", "advertir", "advertencia", "advertência"):
        await juridico.handle_warn(message, args)

    # ── INTELIGÊNCIA ──────────────────────────────────────────────────────────
    elif cmd in ("subornar-porteiro", "suborno-porteiro", "espionar-casa"):
        await intel.handle_subornar_porteiro(message, args)

    elif cmd in ("grampear-call", "grampo", "monitorar-call"):
        await intel.handle_grampear_call(message)

    elif cmd in ("iniciar-festa", "festa", "comecar-festa", "começar-festa"):
        await intel.handle_iniciar_festa(message, args)

    elif cmd in ("registrar-perola", "perola", "pérola", "salvar-rp"):
        await intel.handle_registrar_perola(message, args)

    elif cmd in ("vdd", "verdade-ou-desafio", "verdade-desafio"):
        await intel.handle_vdd(message)

    # ── IA CONVERSACIONAL ────────────────────────────────────────────────────
    elif cmd in ("ia", "ai", "chat", "gpt"):
        await ia_cog.handle_ia(message, args)

    # ── UTILITÁRIOS ───────────────────────────────────────────────────────────
    elif cmd in ("ajuda", "help", "comandos", "menu"):
        embed = discord.Embed(
            title="📜 PERGAMINHOS IMPERIAIS DE TENSHI",
            description=AJUDA_TEXTO,
            color=0x2B0A3D
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    elif cmd in ("ping", "latencia"):
        lat = round(bot.latency * 1000)
        cor = 0x006400 if lat < 100 else 0xFF8C00 if lat < 200 else 0x8B0000
        await message.channel.send(embed=embed_imperial(
            "🏓 Latência Imperial",
            f"*As ondas etéreas de Tenshi respondem...*\n{SEP}\n\n**`{lat}ms`**",
            cor
        ))

    elif cmd in ("top", "leaderboard", "podio"):
        await _handle_top(message)

    elif cmd in ("servidor", "server", "guild"):
        await _handle_servidor(message)

    elif cmd in ("backup",):
        await _handle_backup(message)

    elif cmd in ("aniversario", "aniversário", "birthday"):
        anos = datetime.utcnow().year - FUNDACAO_TENSHI.year
        await _anunciar_aniversario(anos)

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 15 — PRERROGATIVAS SOBERANAS (todos exigem IMPERADOR_ID ou co_soberano)
    # ══════════════════════════════════════════════════════════════════════════

    # ── A) Controle Monetário ─────────────────────────────────────────────────
    elif cmd in ("emitir-moeda", "emitir_moeda", "emitir-moedas"):
        await soberano.cmd_emitir_moeda(message, args)

    elif cmd in ("confiscar-fortuna", "confiscar_fortuna"):
        await soberano.cmd_confiscar_fortuna(message, args)

    elif cmd in ("congelar-banco", "congelar_banco"):
        await soberano.cmd_congelar_banco(message, args)

    elif cmd in ("perdoar-divida", "perdoar_divida", "perdoar-dívida"):
        await soberano.cmd_perdoar_divida(message, args)

    elif cmd in ("isencao-fiscal", "isenção-fiscal", "isencao_fiscal"):
        await soberano.cmd_isencao_fiscal(message, args)

    # ── B) Manipulação do RPG ─────────────────────────────────────────────────
    elif cmd in ("set-status", "set_status", "setstatus"):
        await soberano.cmd_set_status(message, args)

    elif cmd in ("apagar-ficha", "apagar_ficha", "deletar-ficha"):
        await soberano.cmd_apagar_ficha(message, args)

    elif cmd in ("conceder-item", "conceder_item", "dar-item"):
        await soberano.cmd_conceder_item(message, args)

    elif cmd in ("purificar-status", "purificar_status", "cure"):
        await soberano.cmd_purificar_status(message, args)

    elif cmd in ("imortalidade",):
        await soberano.cmd_imortalidade(message, args)

    # ── C) Decretos de Estado ─────────────────────────────────────────────────
    elif cmd in ("estado-de-sitio", "estado_de_sitio", "sitio"):
        await soberano.cmd_estado_de_sitio(message, args)

    elif cmd in ("dissolver-mafia", "dissolver_mafia"):
        await soberano.cmd_dissolver_mafia(message, args)

    elif cmd in ("estatizar-casa", "estatizar_casa"):
        await soberano.cmd_estatizar_casa(message, args)

    elif cmd in ("silenciar-geral", "silenciar_geral"):
        await soberano.cmd_silenciar_geral(message, args)

    elif cmd in ("anistia-geral", "anistia_geral"):
        await soberano.cmd_anistia_geral(message, args)

    # ── D) Alta Justiça ───────────────────────────────────────────────────────
    elif cmd in ("exilio-supremo", "exilio_supremo", "banir-imperial"):
        await soberano.cmd_exilio_supremo(message, args)

    elif cmd in ("perdao-judicial", "perdão-judicial", "perdao_judicial"):
        await soberano.cmd_perdao_judicial(message, args)

    elif cmd in ("revogar-diploma", "revogar_diploma"):
        await soberano.cmd_revogar_diploma(message, args)

    elif cmd in ("cassar-conjuge", "cassar-cônjuge", "cassar_conjuge"):
        await soberano.cmd_cassar_conjuge(message, args)

    # ── E) IA e Conteúdo ──────────────────────────────────────────────────────
    elif cmd in ("atualizar-diretriz", "atualizar_diretriz"):
        await soberano.cmd_atualizar_diretriz(message, args)

    elif cmd in ("apagar-memoria-ia", "apagar_memoria_ia", "limpar-ia"):
        await soberano.cmd_apagar_memoria_ia(message, args)

    elif cmd in ("interceptar-correio", "interceptar_correio"):
        await soberano.cmd_interceptar_correio(message, args)

    elif cmd in ("forçar-cronica", "forcar-cronica", "forcar_cronica"):
        await soberano.cmd_forcar_cronica(message, args)

    elif cmd in ("censurar-termo", "censurar_termo"):
        await soberano.cmd_censurar_termo(message, args)

    # ── F) Engenharia e Manutenção ────────────────────────────────────────────
    elif cmd in ("desligar", "shutdown", "fechar"):
        await soberano.cmd_desligar(message, args)

    elif cmd in ("forçar-pagamento", "forcar-pagamento", "forcar_pagamento"):
        await soberano.cmd_forcar_pagamento(message, args)

    elif cmd in ("exportar-banco", "exportar_banco", "backup-db"):
        await soberano.cmd_exportar_banco(message, args)

    elif cmd in ("bypass-cooldown", "bypass_cooldown"):
        await soberano.cmd_bypass_cooldown(message, args)

    elif cmd in ("congelar-economia", "congelar_economia"):
        await soberano.cmd_congelar_economia(message, args)

    elif cmd in ("censo-imperial", "censo_imperial"):
        await soberano.cmd_censo_imperial(message, args)

    elif cmd in ("reset-era", "reset_era", "nova-era"):
        await soberano.cmd_reset_era(message, args)

    elif cmd in ("irradiar", "transmissao-nacional", "transmissão-nacional"):
        await soberano.cmd_irradiar(message, args)

    elif cmd in ("interdicao", "interdição", "interdicao-canal", "interditar"):
        await soberano.cmd_interdicao(message, args)

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 13 A-B — GEOPOLÍTICA E IMIGRAÇÃO
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("dominar", "dominar-canal", "conquistar-territorio"):
        await geopolitica.handle_dominar(message, args)

    elif cmd in ("territorio", "território", "status-territorio"):
        await geopolitica.handle_status_territorio(message, args)

    elif cmd in ("rebeliao", "rebelião", "rebelar"):
        await geopolitica.handle_rebeliao(message, args)

    elif cmd in ("visto", "painel-visto", "imigração", "imigracao"):
        await geopolitica.handle_painel_visto(message)

    elif cmd in ("cidadania", "certidao", "certidão", "registro-civil"):
        await geopolitica.handle_cidadania(message, args)

    elif cmd in ("exilio", "exílio", "exilio-temporario", "exilar"):
        await geopolitica.handle_exilio_temporario(message, args)

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 13 C-H + 14 — ESTADO, ECONOMIA, TRANSPORTE, SAÚDE
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("pedir-emprestimo", "pedir_emprestimo", "emprestimo", "empréstimo"):
        await estado.handle_emprestimo_banco(message, args)

    elif cmd in ("quitar", "quitar-divida", "pagar-divida"):
        await estado.handle_quitar(message, args)

    elif cmd in ("lavar", "lavagem", "lavar-dinheiro"):
        await estado.handle_lavagem(message, args)

    elif cmd in ("titulo-divida", "título-dívida", "titulo_divida"):
        await estado.handle_titulo_divida(message, args)

    elif cmd in ("abastecer", "combustivel", "combustível", "recarregar-veiculo"):
        await estado.handle_abastecer(message, args)

    elif cmd in ("mandado", "mandado-busca", "busca-e-apreensao"):
        await estado.handle_mandado(message, args)

    elif cmd in ("auditoria-bancaria", "auditoria_bancaria", "auditoria-banco"):
        await estado.handle_auditoria_bancaria(message, args)

    elif cmd in ("seguro-vida", "contratar-seguro", "seguro"):
        await estado.handle_contratar_seguro(message, args)

    elif cmd in ("necrolo", "necrológio", "mural-mortos"):
        await estado.handle_necrolo(message, args)

    elif cmd in ("aposentar", "aposentadoria", "fundo-pensao"):
        await estado.handle_aposentar(message, args)

    elif cmd in ("diagnostico-ia", "diagnóstico-ia", "diagnostico_ia"):
        await estado.handle_diagnostico_ia(message, args)

    elif cmd in ("buscar-protocolo", "buscar_protocolo"):
        await estado.handle_buscar_protocolo(message, args)

    # ══════════════════════════════════════════════════════════════════════════
    # PROTOCOLO 23 — SISTEMA DE ERAS DO TRONO
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("set-era", "set_era", "era-atual", "nova-era-trono"):
        await eras_cog.handle_set_era(message, args)

    elif cmd in ("era", "era-status", "qual-era", "status-era"):
        await eras_cog.handle_era_atual(message)

    elif cmd in ("decreto-marcial", "decreto_marcial"):
        await eras_cog.handle_decreto_marcial(message, args)

    # ══════════════════════════════════════════════════════════════════════════
    # PROTOCOLO 25 — METEOROLOGIA LOCALIZADA POR IA
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("clima", "checar-clima", "tempo", "meteorologia"):
        await clima_cog.handle_clima(message, args)

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 22 — TENSHI ACADEMY
    # ══════════════════════════════════════════════════════════════════════════

    elif cmd in ("matricular", "matricula", "matrícula", "inscrever-materia"):
        await academia.handle_matricular(message, args)

    elif cmd in ("trancar-matricula", "trancar_matricula", "cancelar-materia"):
        await academia.handle_trancar_matricula(message, args)

    elif cmd in ("presença", "presenca", "registrar-presenca"):
        await academia.handle_presenca(message, args)

    elif cmd in ("iniciar-aula", "iniciar_aula", "aula"):
        await academia.handle_iniciar_aula(message, args)

    elif cmd in ("ler-apostila", "apostila", "material-didatico"):
        await academia.handle_ler_apostila(message, args)

    elif cmd in ("prestar-exame", "prestar_exame", "exame", "fazer-prova"):
        await academia.handle_prestar_exame(message, args)

    elif cmd in ("historico-escolar", "histórico-escolar", "notas"):
        await academia.handle_historico_escolar(message, args)

    elif cmd in ("segunda-via-diploma", "segunda_via_diploma", "revalidar-diploma"):
        await academia.handle_segunda_via_diploma(message, args)

    elif cmd in ("entrar-clube", "entrar_clube", "filiacao-clube", "clube"):
        await academia.handle_entrar_clube(message, args)

    elif cmd in ("cofre-clube", "cofres-clubes", "financas-clube"):
        await academia.handle_cofre_clube(message, args)

    # ── Comandos Soberanos da Academia ────────────────────────────────────────
    elif cmd in ("interditar-escola", "interditar_escola"):
        await academia.cmd_interditar_escola(message, args)

    elif cmd in ("aprovação-forçada", "aprovacao-forcada", "aprovacao_forcada"):
        await academia.cmd_aprovacao_forcada(message, args)

    elif cmd in ("estatizar-cofre-clube", "estatizar_cofre_clube"):
        await academia.cmd_estatizar_cofre_clube(message, args)

    elif cmd in ("zerar-historico-academico", "zerar_historico_academico"):
        await academia.cmd_zerar_historico_academico(message, args)

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULOS 19-21 — INFRAESTRUTURA CRÍTICA, MACROECONOMIA, VIGILÂNCIA
    # ══════════════════════════════════════════════════════════════════════════

    # ── Energética e Inflação ─────────────────────────────────────────────────
    elif cmd in ("status-energia", "status_energia", "rede-eletrica"):
        await infra.handle_status_energia(message, args)

    elif cmd in ("inflacao", "inflação", "status-inflacao", "indice-inflacao"):
        await infra.handle_status_inflacao(message, args)

    # ── Mercado de Ações e Poupança ────────────────────────────────────────────
    elif cmd in ("comprar-acoes", "comprar_acoes", "acoes", "ações"):
        await infra.handle_comprar_acoes(message, args)

    elif cmd in ("poupanca", "poupança", "investimento", "conta-poupanca"):
        await infra.handle_poupanca(message, args)

    # ── Vigilância e OSINT ────────────────────────────────────────────────────
    elif cmd in ("checar-cameras", "checar_cameras", "dvr", "cameras"):
        await infra.handle_checar_cameras(message, args)

    elif cmd in ("biometria", "dna", "registro-biometrico"):
        await infra.handle_biometria(message, args)

    elif cmd in ("rastrear-perfil", "rastrear_perfil", "osint"):
        await infra.handle_rastrear_perfil(message, args)

    # ── Logística e Cargas ────────────────────────────────────────────────────
    elif cmd in ("enviar-carga", "enviar_carga", "despachar-carga"):
        await infra.handle_enviar_carga(message, args)

    # ── Saúde ─────────────────────────────────────────────────────────────────
    elif cmd in ("laudo-medico", "laudo_medico", "laudo"):
        await infra.handle_laudo_medico(message, args)

    elif cmd in ("desintoxicacao", "desintoxicação", "detox"):
        await infra.handle_desintoxicacao(message, args)

    elif cmd in ("doacao-sangue", "doação-sangue", "doar-sangue"):
        await infra.handle_doacao_sangue(message, args)

    # ── Imóveis ───────────────────────────────────────────────────────────────
    elif cmd in ("titulo-propriedade", "título-propriedade", "escritura"):
        await infra.handle_titulo_propriedade(message, args)

    elif cmd in ("historico-imovel", "histórico-imóvel", "historico_imovel"):
        await infra.handle_historico_imovel(message, args)

    # ── Aluguel Comercial ─────────────────────────────────────────────────────
    elif cmd in ("alugar-comercio", "alugar_comercio", "alugar-comercial"):
        await infra.handle_alugar_comercio(message, args)

    # ── Fiança ────────────────────────────────────────────────────────────────
    elif cmd in ("pagar-fianca", "pagar_fianca", "pagar-fiança"):
        await infra.handle_pagar_fianca(message, args)

    # ── Diplomacia ────────────────────────────────────────────────────────────
    elif cmd in ("imunidade-diplomatica", "imunidade_diplomatica", "imunidade-consular"):
        await infra.handle_imunidade_diplomatica(message, args)

    # ── Soberania Suprema (Módulos 19-21) ─────────────────────────────────────
    elif cmd in ("auditoria-geral-banco", "auditoria_geral_banco", "auditoria-absoluta"):
        await infra.cmd_auditoria_geral_banco(message, args)

    elif cmd in ("expurgar-fichas-inativas", "expurgar_fichas_inativas", "limpar-fichas"):
        await infra.cmd_expurgar_fichas_inativas(message, args)

    elif cmd in ("reset-parcial-economia", "reset_parcial_economia"):
        await infra.cmd_reset_parcial_economia(message, args)

    elif cmd in ("bans-lista", "lista-exilados", "exilados"):
        await infra.cmd_bans_lista(message, args)

    elif cmd in ("confiscar-veiculo", "confiscar_veiculo", "apreender-veiculo"):
        await infra.cmd_confiscar_veiculo(message, args)

    elif cmd in ("decreto-climatico", "decreto_climatico", "forçar-clima"):
        await infra.cmd_decreto_climatico(message, args)

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO 30 — PSICOLOGIA ESTRATÉGICA & CONSELHEIRO IMPERIAL
    # ══════════════════════════════════════════════════════════════════════════
    elif cmd in ("aconselhar-estrategia", "aconselhar_estrategia",
                 "aconselhar-estratégia", "conselheiro", "conselho-estrategico"):
        await psicologia.handle_aconselhar(message, args)

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
                f"Use o fallback `GROQ_API_KEY` garante que o bot nunca fique sem IA."
            ),
            color=0x1A1A2E
        )
        embed.set_footer(text=f"⚙️ 8 Modelos Groq  •  {RODAPE_IMPERIAL}")
        await message.channel.send(embed=embed)

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
    chave = f"{message.channel.id}-{message.created_at.date()}"
    if chave in _imperador_saudado:
        return
    _imperador_saudado.add(chave)
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
    from database import _load, DB_FILE, CASAS_FILE, EMPRESAS_FILE, FAMILIAS_FILE
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


@bot.event
async def on_member_join(member):
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
async def on_error(event, *args, **kwargs):
    import traceback
    print(f"[ERRO] Evento: {event}")
    traceback.print_exc()


if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN não encontrado nos secrets!")
    else:
        bot.run(token)
