import discord
import random
from datetime import datetime, timedelta
from database import get_user, save_user
from utils import embed_imperial, embed_pegada

CARTAS_TAROT = [
    {"nome": "O Mago", "simbolo": "🧙", "interpretacao": "A vontade manifesta realidade. Hoje, seus atos têm peso dobrado no tecido de Tenshi.", "bonus": {"poder": 15}},
    {"nome": "A Sacerdotisa", "simbolo": "🌙", "interpretacao": "Segredos aguardam nas sombras. O silêncio é mais poderoso que mil espadas hoje.", "bonus": {"xp": 30}},
    {"nome": "A Imperatriz", "simbolo": "👸", "interpretacao": "A abundância flui como o Rio Eterno. O Império sorri para você hoje.", "bonus": {"moedas": 50}},
    {"nome": "O Imperador", "simbolo": "👑", "interpretacao": "A autoridade suprema ressoa em seu ser. Como o grande Alloy, você projeta poder e domínio.", "bonus": {"poder": 25}},
    {"nome": "A Torre", "simbolo": "⚡", "interpretacao": "Transformação violenta, mas necessária. O que cai hoje abre espaço para algo maior.", "bonus": {"xp": 50}},
    {"nome": "A Estrela", "simbolo": "⭐", "interpretacao": "Esperança e renovação banham sua aura. Os astros de Tenshi conspiraram em seu favor.", "bonus": {"poder": 10, "moedas": 30}},
    {"nome": "A Lua", "simbolo": "🌕", "interpretacao": "O véu entre os mundos está fino. Ilusões e verdades se entrelaçam.", "bonus": {"xp": 40}},
    {"nome": "O Sol", "simbolo": "☀️", "interpretacao": "Vitória e clareza absolutas. Tudo que tocar hoje florescerá sob a bênção solar.", "bonus": {"poder": 20, "moedas": 20}},
    {"nome": "O Mundo", "simbolo": "🌍", "interpretacao": "Completude e triunfo absoluto. Você está em perfeita harmonia com o destino imperial.", "bonus": {"poder": 15, "xp": 25, "moedas": 25}},
    {"nome": "O Ermitão", "simbolo": "🕯️", "interpretacao": "A sabedoria interior ilumina mais que qualquer tocha. Retire-se do ruído.", "bonus": {"xp": 60}},
    {"nome": "A Morte", "simbolo": "💀", "interpretacao": "Transformação profunda. Uma fase termina para que algo extraordinário nasça nas cinzas.", "bonus": {"poder": 30}},
    {"nome": "O Louco", "simbolo": "🃏", "interpretacao": "O início de uma jornada épica. A coragem de dar o salto sem garantias define os grandes.", "bonus": {"moedas": 75}},
    {"nome": "A Força", "simbolo": "🦁", "interpretacao": "Não a força bruta, mas a coragem interior. Você doma as feras do seu próprio espírito.", "bonus": {"poder": 20, "xp": 20}},
    {"nome": "A Roda da Fortuna", "simbolo": "🎡", "interpretacao": "Os ciclos giram em seu favor hoje. O destino de Tenshi sorri para você.", "bonus": {"moedas": 60, "xp": 30}},
]

RUNAS = [
    {"nome": "Fehu — A Riqueza", "simbolo": "ᚠ", "interpretacao": "A runa da abundância material flui através de você. Os cofres de Tenshi se abrem.", "bonus": {"moedas": 60}},
    {"nome": "Uruz — A Força", "simbolo": "ᚢ", "interpretacao": "O poder selvagem do auroque corre em suas veias. Ninguém pode te deter hoje.", "bonus": {"poder": 35}},
    {"nome": "Thurisaz — O Trovão", "simbolo": "ᚦ", "interpretacao": "A força destruidora trabalha a seu favor. O que resiste a você quebra.", "bonus": {"poder": 20, "xp": 20}},
    {"nome": "Ansuz — A Sabedoria", "simbolo": "ᚨ", "interpretacao": "Odin sussurra em seu ouvido. Segredos ancestrais de Tenshi são revelados.", "bonus": {"xp": 70}},
    {"nome": "Sowilo — O Sol", "simbolo": "ᛋ", "interpretacao": "A vitória é inevitável. A runa solar brilha — hoje você não pode perder.", "bonus": {"poder": 25, "moedas": 25}},
    {"nome": "Tiwaz — A Justiça", "simbolo": "ᛏ", "interpretacao": "A runa do guerreiro justo. Sua causa é honrada pelos deuses de Tenshi.", "bonus": {"poder": 40}},
    {"nome": "Hagalaz — A Tempestade", "simbolo": "ᚺ", "interpretacao": "Caos purificador. O que sobrevive à tempestade é aço puro.", "bonus": {"xp": 55}},
    {"nome": "Raidho — A Jornada", "simbolo": "ᚱ", "interpretacao": "O caminho se abre. Uma missão épica te aguarda — os passos certos aparecem.", "bonus": {"xp": 40, "moedas": 20}},
]


class Mistico:
    def __init__(self, bot):
        self.bot = bot

    async def handle_tarot(self, message):
        user = get_user(message.author.id)
        agora = datetime.utcnow()
        pegada = user.get("pegada", "imperial")

        if user.get("ultimo_tarot"):
            ultimo = datetime.fromisoformat(user["ultimo_tarot"])
            if agora - ultimo < timedelta(hours=20):
                proximo = ultimo + timedelta(hours=20)
                horas = int((proximo - agora).total_seconds() // 3600)
                mins = int(((proximo - agora).total_seconds() % 3600) // 60)
                await message.channel.send(embed=embed_imperial("🌙 Os Arcanos Repousam", f"Próxima leitura em: **{horas}h {mins}m**", 0x2C2F33))
                return

        carta = random.choice(CARTAS_TAROT)
        bonus_str = []
        for stat, val in carta["bonus"].items():
            user[stat] = user.get(stat, 0) + val
            bonus_str.append(f"+{val} {stat.capitalize()}")

        user["ultimo_tarot"] = agora.isoformat()
        save_user(message.author.id, user)

        embed = discord.Embed(
            title="🃏 OS ARCANOS DE TENSHI FALAM",
            description="*As cartas tremem enquanto revelam seu destino...*",
            color=0x2C2F33
        )
        embed.add_field(name=f"{carta['simbolo']} {carta['nome']}", value=f"*\"{carta['interpretacao']}\"*", inline=False)
        embed.add_field(name="✨ Bênção do Dia", value=" | ".join(bonus_str), inline=False)
        embed.set_footer(text="🌙 Nova leitura disponível em 20 horas")
        await message.channel.send(embed=embed)

    async def handle_runa(self, message):
        user = get_user(message.author.id)
        agora = datetime.utcnow()
        pegada = user.get("pegada", "imperial")

        if user.get("ultimo_tarot"):
            ultimo = datetime.fromisoformat(user["ultimo_tarot"])
            if agora - ultimo < timedelta(hours=20):
                proximo = ultimo + timedelta(hours=20)
                horas = int((proximo - agora).total_seconds() // 3600)
                mins = int(((proximo - agora).total_seconds() % 3600) // 60)
                await message.channel.send(embed=embed_imperial("🔮 As Runas Dormem", f"Próxima runa em: **{horas}h {mins}m**", 0x1a1a2e))
                return

        runa = random.choice(RUNAS)
        bonus_str = []
        for stat, val in runa["bonus"].items():
            user[stat] = user.get(stat, 0) + val
            bonus_str.append(f"+{val} {stat.capitalize()}")

        user["ultimo_tarot"] = agora.isoformat()
        save_user(message.author.id, user)

        embed = discord.Embed(
            title="🔮 RUNA ANCESTRAL DE TENSHI",
            description="*A pedra rúnica pulsa com luz violeta...*",
            color=0x4B0082
        )
        embed.add_field(name=f"{runa['simbolo']} {runa['nome']}", value=f"*\"{runa['interpretacao']}\"*", inline=False)
        embed.add_field(name="⚡ Poder Rúnico", value=" | ".join(bonus_str), inline=False)
        embed.set_footer(text="🔮 As runas são consultadas uma vez a cada 20 horas")
        await message.channel.send(embed=embed)
