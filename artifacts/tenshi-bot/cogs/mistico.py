import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from database import get_user, save_user
from utils import embed_imperial

CARTAS_TAROT = [
    {
        "nome": "O Mago",
        "simbolo": "🧙",
        "interpretacao": "A vontade manifesta realidade. Hoje, seus atos têm peso dobrado no tecido de Tenshi. As forças invisíveis alinham-se ao seu comando.",
        "bonus": {"poder": 15},
    },
    {
        "nome": "A Sacerdotisa",
        "simbolo": "🌙",
        "interpretacao": "Segredos aguardam nas sombras. O silêncio é mais poderoso que mil espadas hoje. Ouça os sussurros das runas antigas.",
        "bonus": {"xp": 30},
    },
    {
        "nome": "A Imperatriz",
        "simbolo": "👸",
        "interpretacao": "A abundância flui como o Rio Eterno. O Império sorri para você hoje — a prosperidade é seu direito divino.",
        "bonus": {"moedas": 50},
    },
    {
        "nome": "O Imperador",
        "simbolo": "👑",
        "interpretacao": "A autoridade suprema ressoa em seu ser. Como o grande Alloy, você projeta poder e domínio. Ninguém questiona sua presença hoje.",
        "bonus": {"poder": 25},
    },
    {
        "nome": "A Torre",
        "simbolo": "⚡",
        "interpretacao": "Transformação violenta, mas necessária. O que cai hoje abre espaço para algo maior. Não resista — flua com a tempestade imperial.",
        "bonus": {"xp": 50},
    },
    {
        "nome": "A Estrela",
        "simbolo": "⭐",
        "interpretacao": "Esperança e renovação banham sua aura. Os astros de Tenshi conspiraram em seu favor — hoje é dia de novas conquistas.",
        "bonus": {"poder": 10, "moedas": 30},
    },
    {
        "nome": "A Lua",
        "simbolo": "🌕",
        "interpretacao": "O véu entre os mundos está fino. Ilusões e verdades se entrelaçam. Confie no instinto, não nos olhos hoje em Tenshi.",
        "bonus": {"xp": 40},
    },
    {
        "nome": "O Sol",
        "simbolo": "☀️",
        "interpretacao": "Vitória e clareza absolutas iluminam seu caminho. Tudo que tocar hoje florescerá sob a bênção solar do Império.",
        "bonus": {"poder": 20, "moedas": 20},
    },
    {
        "nome": "O Mundo",
        "simbolo": "🌍",
        "interpretacao": "Completude e triunfo absoluto. Você está em perfeita harmonia com o destino imperial. Este é um dia de culminação gloriosa.",
        "bonus": {"poder": 15, "xp": 25, "moedas": 25},
    },
    {
        "nome": "O Ermitão",
        "simbolo": "🕯️",
        "interpretacao": "A sabedoria interior ilumina mais que qualquer tocha. Retire-se do ruído — a resposta que busca está em você.",
        "bonus": {"xp": 60},
    },
    {
        "nome": "A Morte",
        "simbolo": "💀",
        "interpretacao": "Não temais — esta carta anuncia transformação profunda. Uma fase termina para que algo extraordinário possa nascer nas cinzas.",
        "bonus": {"poder": 30},
    },
    {
        "nome": "O Louco",
        "simbolo": "🃏",
        "interpretacao": "O início de uma jornada épica. A coragem de dar o salto sem garantias define os grandes do Império. Ouse hoje.",
        "bonus": {"moedas": 75},
    },
]

RUNAS = [
    {
        "nome": "Fehu — A Riqueza",
        "simbolo": "ᚠ",
        "interpretacao": "A runa da abundância material e prosperidade flui através de você. O gado sagrado de Tenshi abençoa seus cofres hoje.",
        "bonus": {"moedas": 60},
    },
    {
        "nome": "Uruz — A Força Bruta",
        "simbolo": "ᚢ",
        "interpretacao": "O poder selvagem do auroque corre em suas veias. Sua força de luta alcança novos picos — ninguém pode te deter.",
        "bonus": {"poder": 35},
    },
    {
        "nome": "Thurisaz — O Trovão",
        "simbolo": "ᚦ",
        "interpretacao": "A runa do caos e da ruptura. Uma força destruidora trabalha a seu favor hoje — o que resiste a você quebra.",
        "bonus": {"poder": 20, "xp": 20},
    },
    {
        "nome": "Ansuz — A Sabedoria Divina",
        "simbolo": "ᚨ",
        "interpretacao": "Odin sussurra em seu ouvido. Mensagens ocultas chegam até você. A compreensão de mistérios antigos de Tenshi é sua hoje.",
        "bonus": {"xp": 70},
    },
    {
        "nome": "Raidho — A Jornada",
        "simbolo": "ᚱ",
        "interpretacao": "O caminho se abre diante de você. Uma missão épica te aguarda — os passos certos aparecem naturalmente em seu trajeto imperial.",
        "bonus": {"xp": 40, "moedas": 20},
    },
    {
        "nome": "Sowilo — O Sol Vitorioso",
        "simbolo": "ᛋ",
        "interpretacao": "A vitória é inevitável. A runa solar de Tenshi brilha sobre você — hoje, você não pode perder o que é seu por direito.",
        "bonus": {"poder": 25, "moedas": 25},
    },
    {
        "nome": "Tiwaz — A Justiça",
        "simbolo": "ᛏ",
        "interpretacao": "A runa do guerreiro justo. Sua causa é honrada pelos deuses de Tenshi. Lute com honra — a vitória justa é garantida.",
        "bonus": {"poder": 40},
    },
    {
        "nome": "Hagalaz — A Tempestade",
        "simbolo": "ᚺ",
        "interpretacao": "Caos inevitável precede transformação radical. As granizadas de Tenshi purificam o que é fraco — o que sobra é aço puro.",
        "bonus": {"xp": 55},
    },
]


class Mistico(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_tarot(self, message):
        user = get_user(message.author.id)
        agora = datetime.utcnow()

        if user.get("ultimo_tarot"):
            ultimo = datetime.fromisoformat(user["ultimo_tarot"])
            if agora - ultimo < timedelta(hours=20):
                proximo = ultimo + timedelta(hours=20)
                horas = int((proximo - agora).total_seconds() // 3600)
                mins = int(((proximo - agora).total_seconds() % 3600) // 60)
                await message.channel.send(embed=embed_imperial(
                    "🌙 Os Arcanos Repousam",
                    f"*As cartas precisam de tempo para se recarregar com a energia de Tenshi...*\n\nPróxima leitura disponível em: **{horas}h {mins}m**",
                    0x2C2F33
                ))
                return

        carta = random.choice(CARTAS_TAROT)
        bonus_str = []
        for stat, val in carta["bonus"].items():
            current = user.get(stat, 0)
            user[stat] = current + val
            bonus_str.append(f"+{val} {stat.capitalize()}")

        user["ultimo_tarot"] = agora.isoformat()
        save_user(message.author.id, user)

        embed = discord.Embed(
            title=f"🃏 OS ARCANOS DE TENSHI FALAM",
            description=f"*As cartas tremem enquanto revelam seu destino...*",
            color=0x2C2F33
        )
        embed.add_field(name=f"{carta['simbolo']} {carta['nome']}", value=f"*\"{carta['interpretacao']}\"*", inline=False)
        embed.add_field(name="✨ Bênção do Dia", value=" | ".join(bonus_str), inline=False)
        embed.set_footer(text="🌙 Uma nova leitura estará disponível em 20 horas")
        await message.channel.send(embed=embed)

    async def handle_runa(self, message):
        user = get_user(message.author.id)
        agora = datetime.utcnow()

        if user.get("ultimo_tarot"):
            ultimo = datetime.fromisoformat(user["ultimo_tarot"])
            if agora - ultimo < timedelta(hours=20):
                proximo = ultimo + timedelta(hours=20)
                horas = int((proximo - agora).total_seconds() // 3600)
                mins = int(((proximo - agora).total_seconds() % 3600) // 60)
                await message.channel.send(embed=embed_imperial(
                    "🔮 As Runas Dormem",
                    f"*As runas precisam de energia cósmica para se manifestar novamente...*\n\nPróxima runa em: **{horas}h {mins}m**",
                    0x1a1a2e
                ))
                return

        runa = random.choice(RUNAS)
        bonus_str = []
        for stat, val in runa["bonus"].items():
            current = user.get(stat, 0)
            user[stat] = current + val
            bonus_str.append(f"+{val} {stat.capitalize()}")

        user["ultimo_tarot"] = agora.isoformat()
        save_user(message.author.id, user)

        embed = discord.Embed(
            title="🔮 RUNA ANCESTRAL DE TENSHI",
            description="*A pedra rúnica pulsa com luz violeta enquanto revela seus segredos...*",
            color=0x4B0082
        )
        embed.add_field(name=f"{runa['simbolo']} {runa['nome']}", value=f"*\"{runa['interpretacao']}\"*", inline=False)
        embed.add_field(name="⚡ Poder Rúnico", value=" | ".join(bonus_str), inline=False)
        embed.set_footer(text="🔮 As runas são consultadas uma vez a cada 20 horas")
        await message.channel.send(embed=embed)
