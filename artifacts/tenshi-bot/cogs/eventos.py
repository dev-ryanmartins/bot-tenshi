import discord
from discord.ext import commands
import asyncio
import random
from datetime import datetime
from database import get_user, save_user, add_pontos_faccao
from utils import embed_imperial, IMPERADOR_ID

INVASORES = [
    {
        "nome": "O Dragão Sombrio das Montanhas Proibidas",
        "emoji": "🐉",
        "hp_max": 500,
        "descricao": "Uma criatura ancestral de escamas negras como o vazio emerge das montanhas do norte. Seu rugido faz as muralhas imperiais tremerem!",
        "dano_base": 30,
        "recompensa_xp": 80,
        "recompensa_moedas": 60,
        "recompensa_poder": 10,
    },
    {
        "nome": "O Espectro do Imperador Esquecido",
        "emoji": "👻",
        "hp_max": 350,
        "descricao": "Um fantasma de um antigo imperador que recusa a descansar emerge do portal dimensional das catacumbas imperiais. Sua raiva corrói a realidade!",
        "dano_base": 20,
        "recompensa_xp": 60,
        "recompensa_moedas": 40,
        "recompensa_poder": 8,
    },
    {
        "nome": "O Leviatã de Sangue das Profundezas",
        "emoji": "🐙",
        "hp_max": 600,
        "descricao": "Das profundezas do Mar de Tenshi emerge uma criatura abissal cujos tentáculos envolvem navios inteiros. O Império clama por heróis!",
        "dano_base": 40,
        "recompensa_xp": 100,
        "recompensa_moedas": 80,
        "recompensa_poder": 15,
    },
    {
        "nome": "O Golem de Cristal das Ruínas Antigas",
        "emoji": "💎",
        "hp_max": 450,
        "descricao": "Uma antiga construção mágica foi reativada nas ruínas do primeiro templo. Seus punhos de cristal destroem pedra como papel!",
        "dano_base": 25,
        "recompensa_xp": 70,
        "recompensa_moedas": 55,
        "recompensa_poder": 12,
    },
    {
        "nome": "A Fênix Corrompida da Ordem Proibida",
        "emoji": "🦅",
        "hp_max": 400,
        "descricao": "Uma Fênix sagrada foi corrompida por magia negra e agora desce sobre o Império com chamas sombrias. Suas cinzas trazem maldição!",
        "dano_base": 35,
        "recompensa_xp": 90,
        "recompensa_moedas": 65,
        "recompensa_poder": 12,
    },
]

COMANDOS_ATAQUE = ["atacar", "golpear", "lutar", "combater", "defender", "resistir", "batalhar"]


class Eventos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invasao_ativa = None
        self.canal_invasao = None
        self.participantes = {}
        self.bg_task = None

    def cog_load(self):
        self.bg_task = self.bot.loop.create_task(self._loop_invasoes())

    def cog_unload(self):
        if self.bg_task:
            self.bg_task.cancel()

    async def _loop_invasoes(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            intervalo = random.randint(3600, 7200)
            await asyncio.sleep(intervalo)
            await self._tentar_invasao()

    async def _tentar_invasao(self):
        if self.invasao_ativa:
            return

        canal = None
        for guild in self.bot.guilds:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    canal = ch
                    break
            if canal:
                break

        if not canal:
            return

        await self.iniciar_invasao(canal)

    async def iniciar_invasao(self, canal):
        if self.invasao_ativa:
            await canal.send(embed=embed_imperial("⚠️ Invasão em Andamento", "Uma invasão já está acontecendo!", 0xFF8C00))
            return

        invasor = random.choice(INVASORES)
        self.invasao_ativa = {
            **invasor,
            "hp": invasor["hp_max"],
        }
        self.canal_invasao = canal
        self.participantes = {}

        embed = discord.Embed(
            title=f"🚨 INVASÃO IMPERIAL! {invasor['emoji']} {invasor['nome']}",
            description=f"*Os sinos de guerra de Tenshi ecoam por todo o império...*\n\n**{invasor['descricao']}**\n\n"
                       f"**Guerreiros de Tenshi! Unam-se para derrotar esta ameaça!**\n\n"
                       f"Digite `atacar`, `golpear` ou `lutar` para combater o inimigo!",
            color=0xFF0000
        )
        embed.add_field(name=f"{invasor['emoji']} HP do Invasor", value=f"❤️ **{invasor['hp_max']} / {invasor['hp_max']}**", inline=True)
        embed.add_field(name="⏱️ Tempo Limite", value="**5 minutos**", inline=True)
        embed.add_field(name="🏆 Recompensa", value=f"+{invasor['recompensa_xp']} XP | +{invasor['recompensa_moedas']} Moedas | +{invasor['recompensa_poder']} Poder", inline=False)
        embed.set_footer(text="⚔️ O Império chama todos os guerreiros — a glória aguarda os corajosos!")
        await canal.send("@everyone", embed=embed)

        await asyncio.sleep(300)
        if self.invasao_ativa:
            hp_restante = self.invasao_ativa["hp"]
            await canal.send(embed=embed_imperial(
                f"💀 {invasor['emoji']} O Invasor Escapou!",
                f"*O {invasor['nome']} recuou para as sombras com **{hp_restante} HP** restantes...*\n\n"
                f"Tenshi foi varrida por sua fúria. Guerreiros, trinem mais para a próxima invasão!",
                0x8B0000
            ))
            self.invasao_ativa = None
            self.canal_invasao = None
            self.participantes = {}

    async def processar_ataque_invasao(self, message):
        if not self.invasao_ativa or message.channel != self.canal_invasao:
            return False

        palavras = message.content.lower().split()
        if not any(cmd in palavras for cmd in COMANDOS_ATAQUE):
            return False

        user = get_user(message.author.id)
        dano = max(10, user["poder"] // 5 + random.randint(5, 25))

        self.invasao_ativa["hp"] -= dano

        uid = str(message.author.id)
        self.participantes[uid] = self.participantes.get(uid, 0) + dano

        if self.invasao_ativa["hp"] <= 0:
            await self._invasao_derrotada(message)
        else:
            hp_atual = max(0, self.invasao_ativa["hp"])
            hp_max = self.invasao_ativa["hp_max"]
            barra = int((hp_atual / hp_max) * 10)
            barra_str = "❤️" * barra + "🖤" * (10 - barra)

            await message.channel.send(
                f"⚔️ **{message.author.display_name}** causou **{dano} de dano**! "
                f"{self.invasao_ativa['emoji']} HP: `{barra_str}` **{hp_atual}/{hp_max}**",
                delete_after=8
            )

        return True

    async def _invasao_derrotada(self, message):
        invasor = self.invasao_ativa
        participantes = self.participantes.copy()
        self.invasao_ativa = None
        self.canal_invasao = None
        self.participantes = {}

        mvp_id = max(participantes, key=participantes.get) if participantes else None
        mvp = await self.bot.fetch_user(int(mvp_id)) if mvp_id else None

        embed = discord.Embed(
            title=f"🏆 INVASÃO DERROTADA! {invasor['emoji']}",
            description=f"*As muralhas de Tenshi resistiram! O {invasor['nome']} foi destruído pela bravura dos guerreiros imperiais!*",
            color=0xFFD700
        )

        if mvp:
            embed.add_field(name="⭐ MVP da Batalha", value=f"**{mvp.display_name}** — {participantes[mvp_id]} de dano total", inline=False)

        embed.add_field(name="👥 Participantes", value=str(len(participantes)), inline=True)
        embed.add_field(name="🎁 Recompensas Distribuídas", value=f"+{invasor['recompensa_xp']} XP | +{invasor['recompensa_moedas']} Moedas | +{invasor['recompensa_poder']} Poder", inline=False)

        for uid, dano in participantes.items():
            try:
                user = get_user(int(uid))
                bonus_mult = 1.5 if uid == mvp_id else 1.0
                user["xp"] += int(invasor["recompensa_xp"] * bonus_mult)
                user["moedas"] += int(invasor["recompensa_moedas"] * bonus_mult)
                user["poder"] += int(invasor["recompensa_poder"] * bonus_mult)
                if user.get("faccao"):
                    add_pontos_faccao(user["faccao"], 15)
                save_user(int(uid), user)
            except Exception:
                pass

        embed.set_footer(text="⚔️ O Império de Tenshi é eterno — sua bravura foi registrada nos Pergaminhos Imortais")
        await message.channel.send(embed=embed)
