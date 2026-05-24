import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from database import get_user, save_user, add_pontos_faccao
from utils import embed_imperial, IMPERADOR_ID

ACOES_COMBATE = [
    ("ataca com uma sequência relâmpago", "🌪️"),
    ("desfere um golpe de energia devastador", "⚡"),
    ("lança uma rajada de força espiritual", "💥"),
    ("executa um corte vazio com precisão cirúrgica", "⚔️"),
    ("canaliza o poder das runas em um soco sísmico", "🔮"),
    ("invoca a chama imperial em suas mãos", "🔥"),
    ("usa uma esquiva perfeita e contra-ataca", "💨"),
    ("rompe a guarda do adversário com brutalidade", "🛡️"),
]


class Duelo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.duelos_ativos = {}
        self.apostas = {}

    async def handle_duelo(self, message, args):
        if not message.mentions:
            await message.channel.send(embed=embed_imperial(
                "⚔️ Desafio de Duelo",
                "Mencione seu oponente: `Tenshi, duelo @usuario [aposta]`",
                0x8B0000
            ))
            return

        alvo = message.mentions[0]

        if alvo.id == message.author.id:
            await message.channel.send(embed=embed_imperial("❌ Impossível", "Você não pode duelar contra si mesmo, guerreiro.", 0x8B0000))
            return

        if alvo.bot:
            await message.channel.send(embed=embed_imperial("❌ Impossível", "Os bots não duelam... ainda.", 0x8B0000))
            return

        duelo_id = f"{message.author.id}-{alvo.id}"
        if duelo_id in self.duelos_ativos:
            await message.channel.send(embed=embed_imperial("⚠️ Duelo em Andamento", "Você já tem um duelo ativo.", 0xFF8C00))
            return

        aposta = 0
        for a in args:
            if a.isdigit():
                aposta = int(a)
                break

        user_desafiante = get_user(message.author.id)
        user_alvo = get_user(alvo.id)

        if aposta > 0:
            if user_desafiante["moedas"] < aposta:
                await message.channel.send(embed=embed_imperial("💸 Moedas Insuficientes", f"Você não tem **{aposta}** moedas para apostar.", 0x8B0000))
                return

        self.duelos_ativos[duelo_id] = {
            "desafiante": message.author,
            "alvo": alvo,
            "aposta": aposta,
            "aceito": False
        }

        embed = discord.Embed(
            title="⚔️ DESAFIO DE DUELO IMPERIAL",
            description=f"*As arenas de Tenshi rugem com antecipação...*\n\n"
                       f"**{message.author.display_name}** desafia **{alvo.display_name}** para um duelo de combate!\n\n"
                       f"💥 Poder de Luta: **{user_desafiante['poder']}** vs **{user_alvo['poder']}**\n"
                       f"💰 Aposta: **{aposta} Moedas Imperiais**" if aposta > 0 else
                       f"*As arenas de Tenshi rugem com antecipação...*\n\n"
                       f"**{message.author.display_name}** desafia **{alvo.display_name}** para um duelo de combate!\n\n"
                       f"💥 Poder de Luta: **{user_desafiante['poder']}** vs **{user_alvo['poder']}**",
            color=0x8B0000
        )
        embed.add_field(name="⏱️ Tempo para Aceitar", value="60 segundos", inline=True)
        embed.add_field(name="✅ Como aceitar", value=f"`Tenshi, aceitar-duelo`", inline=True)
        embed.set_footer(text="⚔️ Que o mais poderoso prevaleça nas arenas imperiais")

        await message.channel.send(f"{alvo.mention}", embed=embed)

        await asyncio.sleep(60)
        if duelo_id in self.duelos_ativos and not self.duelos_ativos[duelo_id]["aceito"]:
            del self.duelos_ativos[duelo_id]
            await message.channel.send(embed=embed_imperial(
                "💨 Duelo Expirado",
                f"*{alvo.display_name} não aceitou o desafio dentro do tempo limite. A honra pertence a {message.author.display_name}.*",
                0x4B0082
            ))

    async def handle_aceitar_duelo(self, message):
        duelo_id = None
        for did, duelo in self.duelos_ativos.items():
            if duelo["alvo"].id == message.author.id:
                duelo_id = did
                break

        if not duelo_id:
            await message.channel.send(embed=embed_imperial("❓ Sem Desafio", "Você não tem nenhum duelo pendente.", 0x4B0082))
            return

        duelo = self.duelos_ativos[duelo_id]
        duelo["aceito"] = True

        desafiante = duelo["desafiante"]
        alvo = message.author
        aposta = duelo["aposta"]

        await self._executar_duelo(message.channel, desafiante, alvo, aposta)
        del self.duelos_ativos[duelo_id]

    async def _executar_duelo(self, canal, desafiante, alvo, aposta: int):
        user_d = get_user(desafiante.id)
        user_a = get_user(alvo.id)

        poder_d = user_d["poder"] + random.randint(-10, 20)
        poder_a = user_a["poder"] + random.randint(-10, 20)

        embed_inicio = discord.Embed(
            title="⚔️ O DUELO COMEÇA!",
            description=f"*As arenas imperiais tremem! {desafiante.display_name} e {alvo.display_name} se encaram com chamas nos olhos...*",
            color=0x8B0000
        )
        embed_inicio.add_field(name=desafiante.display_name, value=f"💥 Poder: **{poder_d}**", inline=True)
        embed_inicio.add_field(name="⚔️ VS ⚔️", value="\u200b", inline=True)
        embed_inicio.add_field(name=alvo.display_name, value=f"💥 Poder: **{poder_a}**", inline=True)
        await canal.send(embed=embed_inicio)
        await asyncio.sleep(2)

        rodadas = []
        hp_d = 100
        hp_a = 100

        for rodada in range(1, 5):
            acao_d = random.choice(ACOES_COMBATE)
            acao_a = random.choice(ACOES_COMBATE)
            dano_d = max(5, int((poder_d / poder_a) * random.randint(15, 35)))
            dano_a = max(5, int((poder_a / poder_d) * random.randint(15, 35)))
            hp_a -= dano_d
            hp_d -= dano_a

            texto = (
                f"**Rodada {rodada}:**\n"
                f"{acao_d[1]} {desafiante.display_name} {acao_d[0]} → -{dano_d} HP em {alvo.display_name}\n"
                f"{acao_a[1]} {alvo.display_name} {acao_a[0]} → -{dano_a} HP em {desafiante.display_name}\n"
                f"❤️ {desafiante.display_name}: **{max(0,hp_d)}** | {alvo.display_name}: **{max(0,hp_a)}**"
            )
            rodadas.append(texto)

            if hp_d <= 0 or hp_a <= 0:
                break

            await asyncio.sleep(1.5)

        vencedor = desafiante if poder_d >= poder_a else alvo
        perdedor = alvo if vencedor == desafiante else desafiante
        user_v = user_d if vencedor == desafiante else user_a
        user_p = user_a if vencedor == desafiante else user_d

        xp_ganho = random.randint(30, 60)
        moedas_ganhas = aposta if aposta > 0 else random.randint(10, 30)

        user_v["xp"] += xp_ganho
        user_v["poder"] += 5
        user_v["vitorias_duelo"] = user_v.get("vitorias_duelo", 0) + 1
        user_p["derrotas_duelo"] = user_p.get("derrotas_duelo", 0) + 1

        if aposta > 0:
            user_v["moedas"] += aposta
            user_p["moedas"] = max(0, user_p["moedas"] - aposta)

        if user_v.get("faccao"):
            add_pontos_faccao(user_v["faccao"], 10)

        save_user(vencedor.id, user_v)
        save_user(perdedor.id, user_p)

        embed_resultado = discord.Embed(
            title="🏆 RESULTADO DO DUELO IMPERIAL",
            description="\n\n".join(rodadas),
            color=0xFFD700
        )
        embed_resultado.add_field(
            name=f"👑 VENCEDOR: {vencedor.display_name}",
            value=f"+{xp_ganho} XP | +5 Poder | +{moedas_ganhas} Moedas Imperiais",
            inline=False
        )
        embed_resultado.add_field(
            name=f"💀 Derrotado: {perdedor.display_name}",
            value=f"A derrota forja guerreiros mais fortes. Continue treinando.",
            inline=False
        )
        embed_resultado.set_footer(text="⚔️ As arenas de Tenshi sempre revelam a verdade do poder")
        await canal.send(embed=embed_resultado)
