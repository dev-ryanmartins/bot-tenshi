import discord
from discord.ext import commands
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

# Intents necessários para o bot funcionar
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = discord.Client(intents=intents)

# Instâncias dos módulos
rpg = RPG(bot)
economia = Economia(bot)
faccoes = Faccoes(bot)
mistico = Mistico(bot)
duelo = Duelo(bot)
eventos = Eventos(bot)
moderacao = Moderacao(bot)
loremaster = LoreMaster(bot)


@bot.event
async def on_ready():
    print(f"⚜️ O Império de Tenshi está online! Bot: {bot.user.name}")
    print(f"🏛️ Servindo {len(bot.guilds)} servidor(es)")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="o Império de Tenshi | Tenshi, ajuda"
        )
    )
    # Iniciar tarefa de eventos em background
    eventos.cog_load()


@bot.event
async def on_message(message):
    # Ignorar mensagens do próprio bot
    if message.author.bot:
        return

    conteudo = message.content.strip()
    conteudo_lower = conteudo.lower()

    # Verificar se é um ataque de invasão (qualquer mensagem num canal de invasão ativa)
    if await eventos.processar_ataque_invasao(message):
        return

    # Detectar prefixo "Tenshi," (case insensitive)
    if not conteudo_lower.startswith(PREFIXO):
        # Tentar interação de lore natural
        await loremaster.handle_lore_natural(message, conteudo)
        return

    # Extrair o comando após o prefixo
    resto = conteudo[len(PREFIXO):].strip()
    partes = resto.split()

    if not partes:
        return

    comando = partes[0].lower()
    args = partes[1:]

    # ============================
    # ROTEAMENTO DE COMANDOS
    # ============================

    # --- RPG & Perfil ---
    if comando in ("status", "perfil"):
        await rpg.handle_perfil(message)

    elif comando in ("treinar", "treino"):
        await rpg.handle_treinar(message)

    elif comando in ("missao", "missão"):
        await rpg.handle_missao(message, args)

    elif comando in ("interagir", "interação", "interacao"):
        await rpg.handle_interagir(message, args)

    # --- Economia ---
    elif comando in ("carteira", "saldo", "moedas"):
        await economia.handle_carteira(message)

    elif comando == "loja":
        await economia.handle_loja(message)

    elif comando in ("comprar", "compra"):
        await economia.handle_comprar(message, args)

    # --- Facções ---
    elif comando in ("entrar", "faccao", "facção", "divisao", "divisão"):
        await faccoes.handle_entrar_faccao(message, args)

    elif comando in ("ranking", "ranking-faccoes", "ranking-facções"):
        await faccoes.handle_ranking_faccoes(message)

    # --- Místico ---
    elif comando == "tarot":
        await mistico.handle_tarot(message)

    elif comando in ("runa", "runas"):
        await mistico.handle_runa(message)

    # --- Duelos PvP ---
    elif comando == "duelo":
        await duelo.handle_duelo(message, args)

    elif comando in ("aceitar-duelo", "aceitar_duelo", "aceitar"):
        await duelo.handle_aceitar_duelo(message)

    # --- LoreMaster (IA) ---
    elif comando in ("cronica", "crônica"):
        await loremaster.handle_cronica(message, args)

    elif comando in ("evento-lore", "eventolore", "profecia"):
        await loremaster.handle_evento_lore(message)

    # --- Eventos manuais (ADM) ---
    elif comando == "invasao" or comando == "invasão":
        if message.author.guild_permissions.administrator or message.author.id == IMPERADOR_ID:
            await eventos.iniciar_invasao(message.channel)
        else:
            await message.channel.send(embed=embed_imperial("🚫 Sem Permissão", "Apenas administradores podem invocar invasões manualmente.", 0x8B0000))

    # --- Moderação ---
    elif comando == "ban":
        await moderacao.handle_ban(message, args)

    elif comando == "kick":
        await moderacao.handle_kick(message, args)

    elif comando == "mute":
        await moderacao.handle_mute(message, args)

    elif comando in ("clear", "limpar", "purge"):
        await moderacao.handle_clear(message, args)

    elif comando == "decreto":
        await moderacao.handle_decreto(message, args)

    # --- Utilitários ---
    elif comando in ("ajuda", "help", "comandos"):
        embed = discord.Embed(
            title="📜 PERGAMINHOS IMPERIAIS DE TENSHI",
            description=AJUDA_TEXTO,
            color=0x4B0082
        )
        embed.set_footer(text="🏛️ Que o conhecimento imperial guie seus passos")
        await message.channel.send(embed=embed)

    elif comando == "ping":
        latencia = round(bot.latency * 1000)
        await message.channel.send(embed=embed_imperial(
            "🏓 Latência Imperial",
            f"*As ondas etéreas de Tenshi respondem...*\n\n**{latencia}ms**",
            0x006400
        ))

    elif comando in ("servidor", "server", "info"):
        guild = message.guild
        if guild:
            embed = discord.Embed(
                title=f"🏛️ {guild.name} — Domínios de Tenshi",
                description=f"*As muralhas deste reino se erguem há {(discord.utils.utcnow() - guild.created_at).days} dias...*",
                color=0x4B0082
            )
            embed.add_field(name="👥 Membros", value=str(guild.member_count), inline=True)
            embed.add_field(name="📺 Canais", value=str(len(guild.channels)), inline=True)
            embed.add_field(name="👑 Imperador", value=guild.owner.display_name if guild.owner else "Desconhecido", inline=True)
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            await message.channel.send(embed=embed)

    else:
        # Comando desconhecido — sugestão imperial
        await message.channel.send(embed=embed_imperial(
            "❓ Comando Desconhecido",
            f"*Os guardas imperiais não reconhecem o comando `{comando}`...*\n\nUse `Tenshi, ajuda` para ver todos os comandos disponíveis.",
            0x2C2F33
        ))


@bot.event
async def on_member_join(member):
    """Mensagem de boas-vindas quando um novo membro entra"""
    canal = member.guild.system_channel
    if not canal:
        for ch in member.guild.text_channels:
            if ch.permissions_for(member.guild.me).send_messages:
                canal = ch
                break

    if canal:
        embed = discord.Embed(
            title="🏛️ UM NOVO SÚDITO CHEGA A TENSHI",
            description=f"*As trombetas imperiais anunciam a chegada de {member.mention} aos domínios do Império de Tenshi...*\n\n"
                       f"Que sua jornada seja gloriosa, guerreiro. O trono de **Alloy** observa seus primeiros passos.\n\n"
                       f"Digite `Tenshi, ajuda` para descobrir seus poderes imperiais.",
            color=0xFFD700
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="⚜️ Bem-vindo ao Império de Tenshi — que a glória seja sua")
        await canal.send(embed=embed)


@bot.event
async def on_member_remove(member):
    """Mensagem quando um membro sai"""
    canal = member.guild.system_channel
    if not canal:
        return

    embed = embed_imperial(
        "💨 Um Guerreiro Parte",
        f"*O nome de {member.display_name} desfaz-se na névoa imperial...*\n\nSeus feitos permanecerão nos Pergaminhos Eternos de Tenshi.",
        0x2C2F33
    )
    await canal.send(embed=embed)


@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Erro no evento {event}: {args}")


# Iniciar o servidor Keep Alive e o bot
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN não encontrado nas variáveis de ambiente!")
    else:
        bot.run(token)
