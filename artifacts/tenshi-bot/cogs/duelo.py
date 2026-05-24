import discord
import random
import asyncio
from datetime import datetime
from database import get_user, save_user, add_pontos_faccao, calcular_nivel
from utils import embed_imperial, embed_pegada, IMPERADOR_ID

ACOES_COMBATE = [
    ("ataca com uma sequência relâmpago", "🌪️"),
    ("desfere um golpe de energia devastador", "⚡"),
    ("lança uma rajada de força espiritual", "💥"),
    ("executa um corte vazio com precisão cirúrgica", "⚔️"),
    ("canaliza o poder das runas em um soco sísmico", "🔮"),
    ("invoca a chama imperial em suas mãos", "🔥"),
    ("usa esquiva perfeita e contra-ataca", "💨"),
    ("rompe a guarda do adversário com brutalidade", "🛡️"),
    ("descarrega energia acumulada em golpe final", "💫"),
    ("usa técnica secreta aprendida nas catacumbas", "🌑"),
]


class Duelo:
    def __init__(self, bot):
        self.bot = bot
        self.duelos_ativos = {}

    async def handle_duelo(self, message, args):
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("⚔️ Duelo", "Mencione seu oponente: `Tenshi, duelo @usuario [aposta]`", 0x8B0000))
            return
        alvo = message.mentions[0]
        if alvo.id == message.author.id:
            await message.channel.send(embed=embed_imperial("❌", "Você não pode duelar consigo mesmo.", 0x8B0000))
            return
        if alvo.bot:
            await message.channel.send(embed=embed_imperial("❌", "Bots não entram em arenas imperiais.", 0x8B0000))
            return

        duelo_id = f"{min(message.author.id, alvo.id)}-{max(message.author.id, alvo.id)}"
        if duelo_id in self.duelos_ativos:
            await message.channel.send(embed=embed_imperial("⚠️", "Já existe um duelo ativo entre vocês.", 0xFF8C00))
            return

        aposta = 0
        for a in args:
            c = a.replace(",", "")
            if c.isdigit():
                aposta = int(c)
                break

        user_d = get_user(message.author.id)
        user_a = get_user(alvo.id)

        if aposta > 0 and user_d["moedas"] < aposta:
            await message.channel.send(embed=embed_imperial("💸 Insuficiente", f"Você não tem {aposta} moedas para apostar.", 0x8B0000))
            return

        self.duelos_ativos[duelo_id] = {"desafiante": message.author, "alvo": alvo, "aposta": aposta, "aceito": False}

        embed = discord.Embed(
            title="⚔️ DESAFIO DE DUELO IMPERIAL",
            description=f"*As arenas de Tenshi rugem com antecipação...*\n\n"
                       f"**{message.author.display_name}** desafia **{alvo.display_name}**!\n\n"
                       f"💥 Poder: **{user_d['poder']}** vs **{user_a['poder']}**\n"
                       f"💰 Aposta: **{aposta}** moedas" if aposta else
                       f"*As arenas de Tenshi rugem com antecipação...*\n\n"
                       f"**{message.author.display_name}** desafia **{alvo.display_name}**!\n\n"
                       f"💥 Poder: **{user_d['poder']}** vs **{user_a['poder']}**",
            color=0x8B0000
        )
        embed.add_field(name="✅ Aceitar", value="`Tenshi, aceitar-duelo`", inline=True)
        embed.add_field(name="⏱️ Expira em", value="60 segundos", inline=True)
        embed.set_footer(text="⚔️ Que o mais poderoso prevaleça nas arenas imperiais")
        await message.channel.send(f"{alvo.mention}", embed=embed)

        await asyncio.sleep(60)
        if duelo_id in self.duelos_ativos and not self.duelos_ativos[duelo_id]["aceito"]:
            del self.duelos_ativos[duelo_id]
            await message.channel.send(embed=embed_imperial(
                "💨 Duelo Expirado",
                f"*{alvo.display_name} não aceitou o desafio. A honra pertence a {message.author.display_name}.*",
                0x4B0082
            ))

    async def handle_aceitar_duelo(self, message):
        duelo_id = None
        for did, duelo in self.duelos_ativos.items():
            if duelo["alvo"].id == message.author.id:
                duelo_id = did
                break
        if not duelo_id:
            await message.channel.send(embed=embed_imperial("❓", "Nenhum desafio pendente para você.", 0x4B0082))
            return
        duelo = self.duelos_ativos[duelo_id]
        duelo["aceito"] = True
        await self._executar_duelo(message.channel, duelo["desafiante"], message.author, duelo["aposta"])
        del self.duelos_ativos[duelo_id]

    async def _executar_duelo(self, canal, desafiante, alvo, aposta: int):
        user_d = get_user(desafiante.id)
        user_a = get_user(alvo.id)
        poder_d = max(10, user_d["poder"] + random.randint(-15, 25))
        poder_a = max(10, user_a["poder"] + random.randint(-15, 25))

        embed_inicio = discord.Embed(
            title="⚔️ O DUELO COMEÇA!",
            description=f"*As arenas imperiais tremem! {desafiante.display_name} e {alvo.display_name} se encaram...*",
            color=0x8B0000
        )
        embed_inicio.add_field(name=desafiante.display_name, value=f"💥 **{poder_d}**", inline=True)
        embed_inicio.add_field(name="⚔️ VS ⚔️", value="\u200b", inline=True)
        embed_inicio.add_field(name=alvo.display_name, value=f"💥 **{poder_a}**", inline=True)
        await canal.send(embed=embed_inicio)
        await asyncio.sleep(1.5)

        hp_d = 100
        hp_a = 100
        log_rodadas = []

        for rodada in range(1, 5):
            if hp_d <= 0 or hp_a <= 0:
                break
            acao_d = random.choice(ACOES_COMBATE)
            acao_a = random.choice(ACOES_COMBATE)
            dano_d = max(5, int((poder_d / max(poder_a, 1)) * random.randint(12, 30)))
            dano_a = max(5, int((poder_a / max(poder_d, 1)) * random.randint(12, 30)))
            hp_a = max(0, hp_a - dano_d)
            hp_d = max(0, hp_d - dano_a)
            log_rodadas.append(
                f"**R{rodada}:** {acao_d[1]} {desafiante.display_name} {acao_d[0]} → **-{dano_d} HP**\n"
                f"        {acao_a[1]} {alvo.display_name} {acao_a[0]} → **-{dano_a} HP**\n"
                f"        ❤️ {desafiante.display_name}: **{hp_d}** | {alvo.display_name}: **{hp_a}**"
            )

        vencedor = desafiante if poder_d >= poder_a else alvo
        perdedor = alvo if vencedor == desafiante else desafiante
        user_v = user_d if vencedor == desafiante else user_a
        user_p = user_a if vencedor == desafiante else user_d

        xp_ganho = random.randint(40, 80)
        moedas_ganhas = aposta if aposta > 0 else random.randint(15, 40)

        user_v["xp"] += xp_ganho
        user_v["poder"] += 8
        user_v["vitorias_duelo"] = user_v.get("vitorias_duelo", 0) + 1
        user_p["derrotas_duelo"] = user_p.get("derrotas_duelo", 0) + 1
        if aposta > 0:
            user_v["moedas"] += aposta
            user_p["moedas"] = max(0, user_p["moedas"] - aposta)
        nivel_v, _ = calcular_nivel(user_v["xp"])
        user_v["nivel"] = nivel_v

        if user_v.get("faccao"):
            add_pontos_faccao(user_v["faccao"], 10)

        save_user(vencedor.id, user_v)
        save_user(perdedor.id, user_p)

        embed_resultado = discord.Embed(
            title="🏆 RESULTADO DO DUELO",
            description="\n\n".join(log_rodadas),
            color=0xFFD700
        )
        embed_resultado.add_field(
            name=f"👑 VENCEDOR: {vencedor.display_name}",
            value=f"+{xp_ganho} XP | +8 Poder | +{moedas_ganhas} Moedas",
            inline=False
        )
        embed_resultado.add_field(
            name=f"💀 Derrotado: {perdedor.display_name}",
            value="A derrota forja guerreiros mais fortes.",
            inline=False
        )
        embed_resultado.set_footer(text="⚔️ As arenas de Tenshi sempre revelam a verdade")
        await canal.send(embed=embed_resultado)
