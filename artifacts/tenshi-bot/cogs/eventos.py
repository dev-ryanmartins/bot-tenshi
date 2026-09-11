import discord
import asyncio
import random
from database import get_user, save_user, add_pontos_faccao, calcular_nivel
from utils import embed_imperial

INVASORES = [
    {"nome": "O Dragão Sombrio das Montanhas", "emoji": "🐉", "hp_max": 500, "descricao": "Uma criatura ancestral de escamas negras emerge das montanhas do norte!", "dano_base": 30, "recompensa_xp": 80, "recompensa_moedas": 60, "recompensa_poder": 10},
    {"nome": "O Espectro do Imperador Esquecido", "emoji": "👻", "hp_max": 350, "descricao": "Um fantasma de um antigo imperador emerge do portal das catacumbas!", "dano_base": 20, "recompensa_xp": 60, "recompensa_moedas": 40, "recompensa_poder": 8},
    {"nome": "O Leviatã das Profundezas", "emoji": "🐙", "hp_max": 600, "descricao": "Uma criatura abissal cujos tentáculos envolvem navios inteiros!", "dano_base": 40, "recompensa_xp": 100, "recompensa_moedas": 80, "recompensa_poder": 15},
    {"nome": "O Golem de Cristal Antigo", "emoji": "💎", "hp_max": 450, "descricao": "Uma construção mágica foi reativada nas ruínas do primeiro templo!", "dano_base": 25, "recompensa_xp": 70, "recompensa_moedas": 55, "recompensa_poder": 12},
    {"nome": "A Fênix Corrompida", "emoji": "🦅", "hp_max": 400, "descricao": "Uma Fênix sagrada corrompida por magia negra desce com chamas sombrias!", "dano_base": 35, "recompensa_xp": 90, "recompensa_moedas": 65, "recompensa_poder": 12},
    {"nome": "O Don das Sombras", "emoji": "🔫", "hp_max": 300, "descricao": "Um poderoso chefe do crime organizado invade os territórios imperiais!", "dano_base": 28, "recompensa_xp": 75, "recompensa_moedas": 90, "recompensa_poder": 9},
    {"nome": "O CEO Traidor", "emoji": "🏢", "hp_max": 380, "descricao": "Um executivo corrompido com exército particular ataca a Tenshi Enterprise!", "dano_base": 22, "recompensa_xp": 65, "recompensa_moedas": 100, "recompensa_poder": 7},
]

COMANDOS_ATAQUE = ["atacar", "golpear", "lutar", "combater", "defender", "resistir", "batalhar", "attack", "fight"]


class Eventos:
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
        if canal:
            await self.iniciar_invasao(canal)

    async def iniciar_invasao(self, canal):
        if self.invasao_ativa:
            await canal.send(embed=embed_imperial("⚠️", "Uma invasão já está em andamento!", 0xFF8C00))
            return

        invasor = random.choice(INVASORES)
        self.invasao_ativa = {**invasor, "hp": invasor["hp_max"]}
        self.canal_invasao = canal
        self.participantes = {}

        embed = discord.Embed(
            title=f"🚨 INVASÃO IMPERIAL! {invasor['emoji']} {invasor['nome']}",
            description=f"*Os sinos de guerra de Tenshi ecoam por todo o império...*\n\n"
                       f"**{invasor['descricao']}**\n\n"
                       f"**⚔️ Guerreiros de Tenshi! Digitem `atacar`, `lutar` ou `combater` para combater!**",
            color=0xFF0000
        )
        embed.add_field(name=f"{invasor['emoji']} HP", value=f"❤️ **{invasor['hp_max']} / {invasor['hp_max']}**", inline=True)
        embed.add_field(name="⏱️ Tempo", value="**5 minutos**", inline=True)
        embed.add_field(name="🏆 Recompensa", value=f"+{invasor['recompensa_xp']} XP | +{invasor['recompensa_moedas']} Moedas | +{invasor['recompensa_poder']} Poder", inline=False)
        embed.set_footer(text="⚔️ MVP recebe recompensas em dobro!")

        try:
            await canal.send("@everyone", embed=embed)
        except Exception:
            await canal.send(embed=embed)

        await asyncio.sleep(300)
        if self.invasao_ativa:
            hp_restante = self.invasao_ativa["hp"]
            await canal.send(embed=embed_imperial(
                f"💀 {invasor['emoji']} Invasor Escapou!",
                f"*{invasor['nome']} recuou com **{max(0, hp_restante)} HP**...*\nTreine mais para a próxima!",
                0x8B0000
            ))
            self.invasao_ativa = None
            self.canal_invasao = None
            self.participantes = {}

    async def processar_ataque_invasao(self, message) -> bool:
        if not self.invasao_ativa or message.channel != self.canal_invasao:
            return False
        palavras = message.content.lower().split()
        if not any(cmd in palavras for cmd in COMANDOS_ATAQUE):
            return False

        user = get_user(message.author.id)
        dano = max(10, user["poder"] // 5 + random.randint(5, 30))
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
                f"⚔️ **{message.author.display_name}** causou **{dano} dano**! "
                f"{self.invasao_ativa['emoji']} `{barra_str}` **{hp_atual}/{hp_max} HP**",
                delete_after=10
            )
        return True

    async def _invasao_derrotada(self, message):
        invasor = self.invasao_ativa
        participantes = self.participantes.copy()
        self.invasao_ativa = None
        self.canal_invasao = None
        self.participantes = {}

        mvp_id = max(participantes, key=participantes.get) if participantes else None

        embed = discord.Embed(
            title=f"🏆 INVASÃO DERROTADA! {invasor['emoji']}",
            description=f"*As muralhas de Tenshi resistiram! {invasor['nome']} foi destruído!*",
            color=0xFFD700
        )

        if mvp_id:
            try:
                mvp = await self.bot.fetch_user(int(mvp_id))
                embed.add_field(name="⭐ MVP", value=f"**{mvp.display_name}** — {participantes[mvp_id]} dano total", inline=False)
            except Exception:
                pass

        embed.add_field(name="👥 Participantes", value=str(len(participantes)), inline=True)
        embed.add_field(name="🎁 Recompensas", value=f"+{invasor['recompensa_xp']} XP | +{invasor['recompensa_moedas']} Moedas | +{invasor['recompensa_poder']} Poder\n⭐ MVP recebe **2x**!", inline=False)

        for uid, dano in participantes.items():
            try:
                user = get_user(int(uid))
                mult = 2.0 if uid == mvp_id else 1.0
                user["xp"] += int(invasor["recompensa_xp"] * mult)
                user["moedas"] += int(invasor["recompensa_moedas"] * mult)
                user["poder"] += int(invasor["recompensa_poder"] * mult)
                nivel, _ = calcular_nivel(user["xp"])
                user["nivel"] = nivel
                if user.get("faccao"):
                    add_pontos_faccao(user["faccao"], 15)
                save_user(int(uid), user)
            except Exception:
                pass

        embed.set_footer(text="⚔️ O Império de Tenshi é eterno — sua bravura foi registrada!")
        await message.channel.send(embed=embed)
