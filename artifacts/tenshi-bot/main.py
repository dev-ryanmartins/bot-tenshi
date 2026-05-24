import discord
import os
import asyncio

from keep_alive import keep_alive
from utils import PREFIXO, embed_imperial, AJUDA_TEXTO, IMPERADOR_ID, SEP, RODAPE_IMPERIAL
from database import get_user, save_user

from cogs.rpg         import RPG
from cogs.economia    import Economia
from cogs.faccoes     import Faccoes
from cogs.mistico     import Mistico
from cogs.duelo       import Duelo
from cogs.eventos     import Eventos
from cogs.moderacao   import Moderacao
from cogs.loremaster  import LoreMaster
from cogs.casas       import Casas
from cogs.empresa     import Empresa
from cogs.financeiro  import Financeiro
from cogs.familia     import Familia
from cogs.perfil_config import PerfilConfig

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds   = True

bot = discord.Client(intents=intents)

# ── Módulos ───────────────────────────────────────────────────────────────────
rpg        = RPG(bot)
economia   = Economia(bot)
faccoes    = Faccoes(bot)
mistico    = Mistico(bot)
duelo      = Duelo(bot)
eventos    = Eventos(bot)
moderacao  = Moderacao(bot)
loremaster = LoreMaster(bot)
casas      = Casas(bot)
empresa    = Empresa(bot)
financeiro = Financeiro(bot)
familia    = Familia(bot)
perfil_cfg = PerfilConfig(bot)


@bot.event
async def on_ready():
    print(f"⚜️  Bot Tenshi v2 online | {bot.user.name} ({bot.user.id})")
    print(f"🏛️  Servidores: {len(bot.guilds)}")
    print(f"👑  Imperador ID: {IMPERADOR_ID}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="o Império de Tenshi | Tenshi, ajuda"
        )
    )
    eventos.cog_load()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    conteudo       = message.content.strip()
    conteudo_lower = conteudo.lower()

    # Detecção de entrada do Imperador (qualquer mensagem)
    if message.author.id == IMPERADOR_ID:
        await _saudar_imperador_se_necessario(message)

    # Invasão ativa: verifica ataque narrativo
    if await eventos.processar_ataque_invasao(message):
        return

    # Prefixo
    if not conteudo_lower.startswith(PREFIXO):
        await loremaster.handle_lore_natural(message, conteudo)
        return

    resto  = conteudo[len(PREFIXO):].strip()
    partes = resto.split()
    if not partes:
        return

    cmd  = partes[0].lower()
    args = partes[1:]

    # ══════════════════════════════════════════════════════════════════════════
    #  ROTEADOR CENTRAL
    # ══════════════════════════════════════════════════════════════════════════

    # ── PERFIL ────────────────────────────────────────────────────────────────
    if cmd in ("status", "perfil", "eu", "me", "ficha-ver"):
        await perfil_cfg.handle_status(message)

    elif cmd in ("ficha", "configurar", "config"):
        await perfil_cfg.handle_ficha(message, args)

    elif cmd in ("pegada", "vibe", "estilo", "tema"):
        await perfil_cfg.handle_pegada(message, args)

    elif cmd in ("inventario", "inventário", "inv", "mochila"):
        await perfil_cfg.handle_inventario(message)

    elif cmd in ("conquistas", "achievements", "titulos", "títulos"):
        await perfil_cfg.handle_conquistas(message)

    # ── RPG NARRATIVO ─────────────────────────────────────────────────────────
    elif cmd in ("treinar", "treino", "train"):
        await rpg.handle_treinar(message, args)

    elif cmd in ("missao", "missão", "mission"):
        await rpg.handle_missao(message, args)

    elif cmd in ("meditar", "meditate"):
        await rpg.handle_meditar(message)

    elif cmd in ("descansar", "rest", "dormir"):
        await rpg.handle_descansar(message)

    elif cmd in ("clima", "weather", "tempo-imperial"):
        await rpg.handle_clima(message)

    elif cmd in ("trabalhar", "trabalho", "work"):
        await rpg.handle_trabalhar(message)

    elif cmd in ("profissao", "profissão", "classe", "class"):
        await rpg.handle_profissao(message, args)

    elif cmd in ("interagir", "rp", "emote"):
        await rpg.handle_interagir(message, args)

    # ── LOREMASTER IA ─────────────────────────────────────────────────────────
    elif cmd in ("cronica", "crônica", "lore"):
        await loremaster.handle_cronica(message, args)

    elif cmd in ("evento-lore", "eventolore", "profecia"):
        await loremaster.handle_evento_lore(message)

    elif cmd in ("oraculo", "oráculo", "oracle"):
        await loremaster.handle_oraculo(message, args)

    elif cmd in ("falar", "npc", "speak"):
        await loremaster.handle_falar(message, args)

    elif cmd in ("lore-historico", "lorehistorico", "cronicas-antigas"):
        await loremaster.handle_lore_historico(message)

    elif cmd in ("quadro-avisos", "avisos", "missoes-diarias"):
        await loremaster.handle_quadro_avisos(message)

    # ── MÍSTICO ───────────────────────────────────────────────────────────────
    elif cmd in ("tarot", "carta"):
        await mistico.handle_tarot(message)

    elif cmd in ("runa", "runas", "rune"):
        await mistico.handle_runa(message)

    elif cmd in ("astros", "constelacao", "constelação", "horoscopo"):
        await mistico.handle_astros(message)

    elif cmd in ("destino",):
        await mistico.handle_destino(message, args)

    elif cmd in ("sacrificio", "sacrifício", "purificar"):
        await mistico.handle_sacrificio(message, args)

    elif cmd in ("ritual-protecao", "ritual"):
        await mistico.handle_ritual(message)

    # ── COMBATE ───────────────────────────────────────────────────────────────
    elif cmd in ("duelo", "duelar", "duel", "battle"):
        await duelo.handle_duelo(message, args)

    elif cmd in ("aceitar-duelo", "aceitar", "accept"):
        await duelo.handle_aceitar_duelo(message)

    elif cmd in ("apostar",):
        await duelo.handle_apostar(message, args)

    elif cmd in ("dado", "dice", "rolar"):
        await rpg.handle_dado(message, args)

    elif cmd in ("invocar-chefe", "invocar_chefe", "boss", "monstro"):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.administrator
        except: pass
        if tem_perm or message.author.id == IMPERADOR_ID:
            await eventos.iniciar_invasao(message.channel, args)
        else:
            await message.channel.send(embed=embed_imperial("🚫", "Apenas administradores podem invocar criaturas.", 0x6B0000))

    elif cmd in ("invasao", "invasão", "invasion"):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.administrator
        except: pass
        if tem_perm or message.author.id == IMPERADOR_ID:
            await eventos.iniciar_invasao(message.channel)
        else:
            await message.channel.send(embed=embed_imperial("🚫", "Apenas administradores podem iniciar invasões.", 0x6B0000))

    # ── ECONOMIA ──────────────────────────────────────────────────────────────
    elif cmd in ("carteira", "saldo", "wallet", "moedas"):
        await economia.handle_carteira(message)

    elif cmd in ("mercado", "loja", "shop", "store"):
        await economia.handle_loja(message)

    elif cmd in ("mercado-negro", "mercadonegro", "black-market"):
        await economia.handle_mercado_negro(message)

    elif cmd in ("comprar", "compra", "buy"):
        await economia.handle_comprar(message, args)

    elif cmd in ("leilao", "leilão", "auction"):
        await economia.handle_leilao(message, args)

    elif cmd in ("sorteio-real", "sorteio", "giveaway"):
        await economia.handle_sorteio(message)

    # ── BANCO / FINANCEIRO ────────────────────────────────────────────────────
    elif cmd in ("banco", "bank", "extrato"):
        await financeiro.handle_banco(message)

    elif cmd in ("depositar", "deposito", "deposit"):
        await financeiro.handle_depositar(message, args)

    elif cmd in ("sacar", "saque", "withdraw"):
        await financeiro.handle_sacar(message, args)

    elif cmd in ("transferir", "pagar", "pix", "send"):
        await financeiro.handle_transferir(message, args)

    elif cmd in ("emprestimo", "empréstimo", "credito", "loan"):
        await financeiro.handle_emprestimo(message, args)

    elif cmd in ("pagar-divida", "pagardivida", "quitar"):
        await financeiro.handle_pagar_divida(message, args)

    elif cmd in ("historico", "histórico", "history"):
        await financeiro.handle_historico(message)

    # ── CASAS ─────────────────────────────────────────────────────────────────
    elif cmd in ("casas", "imoveis", "propriedades", "houses"):
        await casas.handle_casas(message)

    elif cmd in ("minha-casa", "minhacasa", "meu-lar"):
        await casas.handle_minha_casa(message)

    elif cmd in ("vender-casa", "vendercasa"):
        await casas.handle_vender_casa(message)

    # ── EMPRESA ───────────────────────────────────────────────────────────────
    elif cmd in ("empresa", "company", "corp", "enterprise", "negocio"):
        await empresa.handle_empresa(message, args)

    # ── FAMÍLIA / MÁFIA ───────────────────────────────────────────────────────
    elif cmd in ("familia", "família", "mafia", "máfia", "cla", "org"):
        await familia.handle_familia(message, args)

    # ── FACÇÕES ───────────────────────────────────────────────────────────────
    elif cmd in ("entrar", "faccao", "facção", "faction"):
        await faccoes.handle_entrar_faccao(message, args)

    elif cmd in ("ranking", "top-faccoes"):
        await faccoes.handle_ranking_faccoes(message)

    # ── MODERAÇÃO IMPERIAL ────────────────────────────────────────────────────
    elif cmd in ("decreto",):
        await moderacao.handle_decreto(message, args)

    elif cmd in ("promover",):
        await moderacao.handle_promover_cargo(message, args)

    elif cmd in ("punir-audacia", "punirsemrespeito", "punir"):
        await moderacao.handle_punir_audacia(message, args)

    elif cmd in ("julgamento", "julgar", "trial"):
        await moderacao.handle_julgamento(message, args)

    elif cmd in ("masmorra-prender", "prender", "masmorrar"):
        await moderacao.handle_prender(message, args)

    elif cmd in ("exilar",):
        await moderacao.handle_exilar(message, args)

    elif cmd in ("anistia-real", "anistia", "perdoar-todos"):
        await moderacao.handle_anistia(message)

    elif cmd in ("trancar-portoes", "anti-raid", "lockdown"):
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

    # ── UTILITÁRIOS ───────────────────────────────────────────────────────────
    elif cmd in ("ajuda", "help", "comandos", "menu", "?"):
        embed = discord.Embed(
            title="📜 PERGAMINHOS IMPERIAIS",
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
            f"*As ondas etéreas de Tenshi respondem...*\n\n"
            f"{SEP}\n**`{lat}ms`**\n{SEP}",
            cor
        ))

    elif cmd in ("top", "leaderboard", "podio"):
        await _handle_top(message)

    elif cmd in ("servidor", "server", "guild", "info"):
        await _handle_servidor(message)

    elif cmd in ("backup",):
        await _handle_backup(message)

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
_imperador_saudado: set = set()

async def _saudar_imperador_se_necessario(message):
    chave = f"{message.channel.id}-{message.created_at.date()}"
    if chave in _imperador_saudado:
        return
    _imperador_saudado.add(chave)
    embed = discord.Embed(
        title="⚜️ 👑 O IMPERADOR RETORNA 👑 ⚜️",
        description=(
            f"*Uma aura dourada envolve o salão... o cosmos se curva...*\n\n"
            f"{SEP}\n\n"
            f"**Imperador Alloy** ilumina novamente os domínios de Tenshi.\n"
            f"*Que sua presença divina abençoe todos os súditos desta corte.*\n\n"
            f"{SEP}"
        ),
        color=0xFFD700
    )
    embed.set_footer(text="👑 Alloy Tenshi — Soberano Supremo e Eterno")
    await message.channel.send(embed=embed)


# ─────────────────────────────────────────────────────────────────────────────
# Auxiliares globais
# ─────────────────────────────────────────────────────────────────────────────
async def _handle_top(message):
    from database import get_all_users
    todos = get_all_users()
    if not todos:
        await message.channel.send(embed=embed_imperial("📊 Pódio Imperial", "Nenhum guerreiro registrado ainda.", 0x1a1a2e))
        return
    ordenados = sorted(todos.items(), key=lambda x: x[1].get("poder", 0), reverse=True)[:10]
    embed = discord.Embed(
        title="🏆 PÓDIO IMPERIAL — GUERREIROS DE TENSHI",
        description=f"*Os nomes gravados nos Pergaminhos Imortais...*\n{SEP}",
        color=0xFFD700
    )
    medalhas = ["🥇", "🥈", "🥉"]
    emoji_pegada = {"imperial": "🏛️", "familia": "👨‍👩‍👧", "mafia": "🖤", "enterprise": "🏢"}
    for i, (uid, u) in enumerate(ordenados):
        medalha = medalhas[i] if i < 3 else f"`#{i+1}`"
        try:
            membro = await bot.fetch_user(int(uid))
            nome = membro.display_name
        except Exception:
            nome = u.get("nome") or f"Súdito #{uid[-4:]}"
        ep = emoji_pegada.get(u.get("pegada", "imperial"), "🏛️")
        embed.add_field(
            name=f"{medalha} {ep} {nome}",
            value=(
                f"💥 **{u.get('poder',0)}** poder  •  "
                f"📊 Nível **{u.get('nivel',1)}**  •  "
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
    embed.add_field(name="📺 Canais", value=f"**{len(guild.channels)}**", inline=True)
    embed.add_field(name="🎭 Cargos", value=f"**{len(guild.roles)}**", inline=True)
    embed.add_field(name="📅 Fundado há", value=f"**{(discord.utils.utcnow() - guild.created_at).days}** dias", inline=True)
    if guild.owner:
        embed.add_field(name="👑 Governante", value=guild.owner.display_name, inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text=RODAPE_IMPERIAL)
    await message.channel.send(embed=embed)


async def _handle_backup(message):
    import json
    from database import _load, DB_FILE, CASAS_FILE, EMPRESAS_FILE, FAMILIAS_FILE
    stats = {
        "usuarios": len(_load(DB_FILE)),
        "casas_ocupadas": sum(1 for c in _load(CASAS_FILE).values() if c.get("dono")),
        "empresas": len(_load(EMPRESAS_FILE)),
        "familias": len(_load(FAMILIAS_FILE)),
    }
    embed = embed_imperial(
        "💾 BACKUP IMPERIAL",
        f"*Os Escribas salvaram os Pergaminhos Imortais...*\n{SEP}\n\n"
        f"👤 Usuários: **{stats['usuarios']}**\n"
        f"🏠 Casas ocupadas: **{stats['casas_ocupadas']}**\n"
        f"🏢 Empresas: **{stats['empresas']}**\n"
        f"👨‍👩‍👧 Organizações: **{stats['familias']}**\n\n"
        f"*Dados preservados nos servidores eternos de Tenshi.*",
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
    eh_imp = member.id == IMPERADOR_ID
    if eh_imp:
        embed = discord.Embed(
            title="⚜️ 👑 O IMPERADOR RETORNA AO TRONO 👑 ⚜️",
            description=(
                f"*Os sinos dourados de Tenshi ecoam por todo o império...*\n\n{SEP}\n\n"
                f"**Alloy Tenshi**, o Soberano Supremo e Eterno, pisou novamente "
                f"nas terras do Império!\n\n"
                f"*Que todos os súditos se curvem diante de sua presença divina.*\n\n{SEP}"
            ),
            color=0xFFD700
        )
    else:
        embed = discord.Embed(
            title="🏛️ UM NOVO SÚDITO CHEGA A TENSHI",
            description=(
                f"*As trombetas imperiais anunciam {member.mention}...*\n\n{SEP}\n\n"
                f"Bem-vindo(a) aos domínios eternos do Império de Tenshi.\n"
                f"*O trono de Alloy observa seus primeiros passos.*\n\n"
                f"**Comece sua jornada:**\n"
                f"• `Tenshi, ficha` — Configure seu personagem\n"
                f"• `Tenshi, status` — Ver seu perfil imperial\n"
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
        embed = embed_imperial(
            "💨 Um Súdito Parte",
            f"*{member.display_name} dissolve-se na névoa imperial...*\n\n"
            f"Seus feitos permanecem gravados nos Pergaminhos Eternos de Tenshi.",
            0x1a1a2e
        )
        await canal.send(embed=embed)


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
