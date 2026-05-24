import discord
import os
import asyncio
from datetime import datetime

from keep_alive import keep_alive
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

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds   = True

bot = discord.Client(intents=intents)

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

# ── Fundação de Tenshi ────────────────────────────────────────────────────────
FUNDACAO_TENSHI = datetime(2016, 6, 6)

_imperador_saudado: set = set()
_aniversario_anunciado: set = set()


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
    bot.loop.create_task(_loop_aniversario())


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

    conteudo       = message.content.strip()
    conteudo_lower = conteudo.lower()

    # Saudação automática ao Imperador
    if message.author.id == IMPERADOR_ID:
        await _saudar_imperador_se_necessario(message)

    # Invasão ativa
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

    elif cmd in ("clima", "weather", "tempo"):
        await rpg.handle_clima(message)

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

    # ── CASAS ─────────────────────────────────────────────────────────────────
    elif cmd in ("casas", "imoveis", "propriedades"):
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
