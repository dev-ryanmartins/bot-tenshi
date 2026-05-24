import discord
import os
import asyncio

from keep_alive import keep_alive
from utils import PREFIXO, embed_imperial, AJUDA_TEXTO, IMPERADOR_ID
from database import get_user, save_user

from cogs.rpg import RPG
from cogs.economia import Economia
from cogs.faccoes import Faccoes
from cogs.mistico import Mistico
from cogs.duelo import Duelo
from cogs.eventos import Eventos
from cogs.moderacao import Moderacao
from cogs.loremaster import LoreMaster
from cogs.casas import Casas
from cogs.empresa import Empresa
from cogs.financeiro import Financeiro
from cogs.familia import Familia
from cogs.perfil_config import PerfilConfig

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = discord.Client(intents=intents)

# Instâncias dos módulos
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


@bot.event
async def on_ready():
    print(f"⚜️  Bot Tenshi online! Usuário: {bot.user.name} ({bot.user.id})")
    print(f"🏛️  Servidores: {len(bot.guilds)}")
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

    conteudo = message.content.strip()
    conteudo_lower = conteudo.lower()

    # ── Invasão em andamento: qualquer mensagem pode ser ataque ──────────────
    if await eventos.processar_ataque_invasao(message):
        return

    # ── Detectar prefixo Tenshi, ─────────────────────────────────────────────
    if not conteudo_lower.startswith(PREFIXO):
        await loremaster.handle_lore_natural(message, conteudo)
        return

    resto  = conteudo[len(PREFIXO):].strip()
    partes = resto.split()
    if not partes:
        return

    cmd  = partes[0].lower()
    args = partes[1:]

    # ════════════════════════════════════════════════════════════════
    #  ROTEAMENTO CENTRAL
    # ════════════════════════════════════════════════════════════════

    # ── PERFIL / FICHA / PEGADA ──────────────────────────────────────
    if cmd in ("status", "perfil", "eu", "me"):
        await perfil_cfg.handle_status(message)

    elif cmd in ("ficha", "configurar", "config"):
        await perfil_cfg.handle_ficha(message, args)

    elif cmd in ("pegada", "vibe", "estilo", "tema"):
        await perfil_cfg.handle_pegada(message, args)

    # ── RPG ──────────────────────────────────────────────────────────
    elif cmd in ("treinar", "treino", "train"):
        await rpg.handle_treinar(message)

    elif cmd in ("missao", "missão", "mission"):
        await rpg.handle_missao(message, args)

    elif cmd in ("interagir", "interação", "interacao", "rp"):
        await rpg.handle_interagir(message, args)

    # ── ECONOMIA ─────────────────────────────────────────────────────
    elif cmd in ("carteira", "saldo", "wallet"):
        await economia.handle_carteira(message)

    elif cmd in ("loja", "shop", "store"):
        await economia.handle_loja(message)

    elif cmd in ("comprar", "compra", "buy"):
        await economia.handle_comprar(message, args)

    # ── BANCO / FINANCEIRO ───────────────────────────────────────────
    elif cmd in ("banco", "bank", "extrato"):
        await financeiro.handle_banco(message)

    elif cmd in ("depositar", "deposito", "deposit"):
        await financeiro.handle_depositar(message, args)

    elif cmd in ("sacar", "saque", "withdraw"):
        await financeiro.handle_sacar(message, args)

    elif cmd in ("transferir", "transferencia", "transferência", "pix", "send"):
        await financeiro.handle_transferir(message, args)

    elif cmd in ("emprestimo", "empréstimo", "credito", "crédito", "loan"):
        await financeiro.handle_emprestimo(message, args)

    elif cmd in ("pagar-divida", "pagar_divida", "pagardivida", "quitar"):
        await financeiro.handle_pagar_divida(message, args)

    elif cmd in ("historico", "histórico", "extrato-financeiro", "history"):
        await financeiro.handle_historico(message)

    # ── CASAS ────────────────────────────────────────────────────────
    elif cmd in ("casas", "imoveis", "imóveis", "propriedades", "houses"):
        await casas.handle_casas(message)

    elif cmd in ("minha-casa", "minhacasa", "meu-lar", "myhouse"):
        await casas.handle_minha_casa(message)

    elif cmd in ("vender-casa", "vendercasa", "vender_casa"):
        await casas.handle_vender_casa(message)

    # ── EMPRESA / GESTÃO ─────────────────────────────────────────────
    elif cmd in ("empresa", "company", "corp", "enterprise", "negocio", "negócio"):
        await empresa.handle_empresa(message, args)

    # ── FAMÍLIA / MÁFIA ──────────────────────────────────────────────
    elif cmd in ("familia", "família", "mafia", "máfia", "cla", "clã", "org"):
        await familia.handle_familia(message, args)

    # ── FACÇÕES ──────────────────────────────────────────────────────
    elif cmd in ("entrar", "faccao", "facção", "faction", "join"):
        await faccoes.handle_entrar_faccao(message, args)

    elif cmd in ("ranking", "top-faccoes", "faccoes-ranking"):
        await faccoes.handle_ranking_faccoes(message)

    # ── MÍSTICO ──────────────────────────────────────────────────────
    elif cmd in ("tarot", "carta"):
        await mistico.handle_tarot(message)

    elif cmd in ("runa", "runas", "rune"):
        await mistico.handle_runa(message)

    # ── DUELOS PvP ───────────────────────────────────────────────────
    elif cmd in ("duelo", "duel", "battle", "lutar"):
        await duelo.handle_duelo(message, args)

    elif cmd in ("aceitar-duelo", "aceitar_duelo", "aceitar", "accept"):
        await duelo.handle_aceitar_duelo(message)

    # ── LOREMASTER (IA) ──────────────────────────────────────────────
    elif cmd in ("cronica", "crônica", "lore", "historia-rpg"):
        await loremaster.handle_cronica(message, args)

    elif cmd in ("evento-lore", "eventolore", "profecia", "prophecy"):
        await loremaster.handle_evento_lore(message)

    # ── EVENTOS MANUAIS ──────────────────────────────────────────────
    elif cmd in ("invasao", "invasão", "invasion"):
        tem_perm = False
        try:
            tem_perm = message.author.guild_permissions.administrator
        except Exception:
            pass
        if tem_perm or message.author.id == IMPERADOR_ID:
            await eventos.iniciar_invasao(message.channel)
        else:
            await message.channel.send(embed=embed_imperial("🚫", "Apenas administradores podem invocar invasões.", 0x8B0000))

    # ── MODERAÇÃO ────────────────────────────────────────────────────
    elif cmd == "ban":
        await moderacao.handle_ban(message, args)

    elif cmd == "kick":
        await moderacao.handle_kick(message, args)

    elif cmd == "mute":
        await moderacao.handle_mute(message, args)

    elif cmd in ("clear", "limpar", "purge", "cls"):
        await moderacao.handle_clear(message, args)

    elif cmd == "decreto":
        await moderacao.handle_decreto(message, args)

    # ── UTILITÁRIOS ──────────────────────────────────────────────────
    elif cmd in ("ajuda", "help", "comandos", "menu", "?"):
        embed = discord.Embed(
            title="📜 PERGAMINHOS IMPERIAIS DE TENSHI",
            description=AJUDA_TEXTO,
            color=0x4B0082
        )
        embed.set_footer(text="🏛️ Que o conhecimento imperial guie seus passos")
        await message.channel.send(embed=embed)

    elif cmd in ("ping", "latencia", "latência"):
        lat = round(bot.latency * 1000)
        await message.channel.send(embed=embed_imperial(
            "🏓 Latência Imperial",
            f"*As ondas etéreas de Tenshi respondem...*\n\n**{lat}ms**",
            0x006400
        ))

    elif cmd in ("servidor", "server", "info", "guild"):
        guild = message.guild
        if guild:
            embed = discord.Embed(
                title=f"🏛️ {guild.name} — Domínios de Tenshi",
                description=f"*Erguida há {(discord.utils.utcnow() - guild.created_at).days} dias...*",
                color=0x4B0082
            )
            embed.add_field(name="👥 Membros", value=str(guild.member_count), inline=True)
            embed.add_field(name="📺 Canais", value=str(len(guild.channels)), inline=True)
            embed.add_field(name="🎭 Cargos", value=str(len(guild.roles)), inline=True)
            if guild.owner:
                embed.add_field(name="👑 Líder", value=guild.owner.display_name, inline=True)
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            await message.channel.send(embed=embed)

    elif cmd in ("top", "leaderboard", "podio", "pódio"):
        await _handle_top(message)

    else:
        await message.channel.send(embed=embed_imperial(
            "❓ Comando Desconhecido",
            f"*Os guardas imperiais não reconhecem `{cmd}`...*\n\nUse `Tenshi, ajuda` para ver todos os comandos.",
            0x2C2F33
        ))


async def _handle_top(message):
    from database import get_all_users
    todos = get_all_users()
    if not todos:
        await message.channel.send(embed=embed_imperial("📊 Top Guerreiros", "Nenhum guerreiro registrado ainda.", 0x2C2F33))
        return
    ordenados = sorted(todos.items(), key=lambda x: x[1].get("poder", 0), reverse=True)[:10]
    embed = discord.Embed(
        title="🏆 TOP GUERREIROS DO IMPÉRIO DE TENSHI",
        description="*Os mais poderosos registrados nos Pergaminhos Imortais*",
        color=0xFFD700
    )
    medalhas = ["🥇", "🥈", "🥉"]
    for i, (uid, u) in enumerate(ordenados):
        medalha = medalhas[i] if i < 3 else f"#{i+1}"
        try:
            membro = await bot.fetch_user(int(uid))
            nome = membro.display_name
        except Exception:
            nome = u.get("nome") or f"ID:{uid}"
        nivel = u.get("nivel", 1)
        poder = u.get("poder", 0)
        vitorias = u.get("vitorias_duelo", 0)
        pegada_emoji = {"imperial": "🏛️", "familia": "👨‍👩‍👧", "mafia": "🔫", "enterprise": "🏢"}.get(u.get("pegada", "imperial"), "🏛️")
        embed.add_field(
            name=f"{medalha} {pegada_emoji} {nome}",
            value=f"💥 **{poder}** poder | 📊 Nível {nivel} | ⚔️ {vitorias} vitórias",
            inline=False
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
    if canal:
        embed = discord.Embed(
            title="🏛️ UM NOVO SÚDITO CHEGA A TENSHI",
            description=(
                f"*As trombetas imperiais anunciam a chegada de {member.mention} aos domínios do Império...*\n\n"
                f"Bem-vindo(a), guerreiro(a). O trono de **Alloy** observa seus primeiros passos.\n\n"
                f"**Comece sua jornada:**\n"
                f"• `Tenshi, ficha` — Configure seu perfil\n"
                f"• `Tenshi, status` — Ver seu status\n"
                f"• `Tenshi, ajuda` — Ver todos os comandos"
            ),
            color=0xFFD700
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="⚜️ Bem-vindo ao Império de Tenshi")
        await canal.send(embed=embed)


@bot.event
async def on_member_remove(member):
    canal = member.guild.system_channel
    if canal:
        await canal.send(embed=embed_imperial(
            "💨 Um Guerreiro Parte",
            f"*{member.display_name} desfaz-se na névoa imperial...*\nSeus feitos permanecem nos Pergaminhos Eternos.",
            0x2C2F33
        ))


@bot.event
async def on_error(event, *args, **kwargs):
    import traceback
    print(f"Erro no evento {event}:")
    traceback.print_exc()


if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN não encontrado!")
    else:
        bot.run(token)
