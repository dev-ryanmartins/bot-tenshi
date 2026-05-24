import discord
import random
import asyncio
from datetime import datetime, timedelta
from database import get_user, save_user, add_pontos_faccao, calcular_nivel
from utils import embed_imperial, embed_pegada, COOLDOWN_TREINO, IMPERADOR_ID

MISSOES = [
    {
        "nome": "Patrulha nas Fronteiras do Norte",
        "descricao": "Rumores de criaturas sombrias se aproximando das muralhas. O Império precisa de vigilantes.",
        "narrativa": "🌑 *As chamas das tochas tremem enquanto você avança pelas fronteiras geladas...*\n\n**Você enfrentou a escuridão. O Império está mais seguro.**",
        "recompensa_xp": 80, "recompensa_moedas": 60, "recompensa_poder": 15, "duracao_min": 2,
    },
    {
        "nome": "Missão Diplomática na Corte Rival",
        "descricao": "Uma delegação deve negociar termos com o clã rival. Eloquência e astúcia são essenciais.",
        "narrativa": "👑 *Os salões de mármore da corte rival... Cada palavra carrega o peso de mil espadas.*\n\n**Os termos foram aceitos. Tenshi expande sua influência.**",
        "recompensa_xp": 100, "recompensa_moedas": 90, "recompensa_poder": 10, "duracao_min": 3,
    },
    {
        "nome": "Investigação nas Catacumbas Místicas",
        "descricao": "Runas foram ativadas nas profundezas. Um agente deve investigar antes que o portal se abra.",
        "narrativa": "🔮 *As paredes pulsam com luz violeta... Você decifrou o símbolo proibido e selou o portal.*\n\n**O equilíbrio místico de Tenshi foi preservado.**",
        "recompensa_xp": 120, "recompensa_moedas": 70, "recompensa_poder": 25, "duracao_min": 4,
    },
    {
        "nome": "Operação no Submundo Imperial",
        "descricao": "Infiltre a rede criminosa e recupere documentos secretos roubados.",
        "narrativa": "🔫 *Luzes fracas de tavernas clandestinas... Sua identidade ficou intacta. Os documentos, recuperados.*\n\n**O Imperador recompensa sua discrição.**",
        "recompensa_xp": 110, "recompensa_moedas": 100, "recompensa_poder": 20, "duracao_min": 3,
    },
    {
        "nome": "Auditoria Corporativa da Tenshi Enterprise",
        "descricao": "Irregularidades foram detectadas em uma filial. Investigue e reporte ao CEO.",
        "narrativa": "🏢 *Planilhas, contratos, reuniões... A fraude foi exposta. A empresa está mais forte.*\n\n**Sua competência foi reconhecida pelo conselho.**",
        "recompensa_xp": 90, "recompensa_moedas": 110, "recompensa_poder": 5, "duracao_min": 2,
    },
]

TREINOS = [
    "🔥 *Horas meditando sob a cachoeira gelada, forçando mente e corpo além dos limites. As águas cantavam segredos antigos enquanto seu poder crescia...*",
    "⚔️ *Mil golpes contra a pedra sagrada. Seus punhos sangram, mas a dor é apenas um professor severo. O Imperador Alloy observaria com aprovação.*",
    "🌙 *Sob a lua cheia de Tenshi, você canalizou energia das estrelas pelo corpo. Cada respiração expandia seu poder como uma chama que se recusa a morrer.*",
    "💪 *As arenas de treino testemunharam seu esforço hoje. Os veteranos pararam para observar — raramente viam tal determinação.*",
    "🌊 *Você mergulhou nas profundezas do Rio Eterno. A pressão forja campeões ou mata os fracos. Você emergiu transformado.*",
    "🏋️ *Horas carregando pedras imperiais nas costas, cada passo um teste de vontade. Sua resistência transcendeu os limites conhecidos.*",
    "🧘 *Meditação profunda nas câmaras arcanas. Sua mente e poder se fundiram em algo mais perigoso que qualquer arma.*",
]


class RPG:
    def __init__(self, bot):
        self.bot = bot
        self.missoes_ativas = {}

    async def handle_treinar(self, message):
        user = get_user(message.author.id)
        agora = datetime.utcnow()

        if user.get("ultimo_treino"):
            ultimo = datetime.fromisoformat(user["ultimo_treino"])
            diferenca = agora - ultimo
            if diferenca < timedelta(seconds=COOLDOWN_TREINO):
                restante = timedelta(seconds=COOLDOWN_TREINO) - diferenca
                minutos = int(restante.total_seconds() // 60)
                segundos = int(restante.total_seconds() % 60)
                pegada = user.get("pegada", "imperial")
                await message.channel.send(embed=embed_pegada(
                    "⏳ Em Recuperação",
                    f"*Seu corpo ainda absorve os ensinamentos do último treino...*\n\n"
                    f"Próximo treino em: **{minutos}m {segundos}s**",
                    pegada
                ))
                return

        ganho_poder = random.randint(8, 25)
        ganho_xp = random.randint(25, 60)
        narrativa = random.choice(TREINOS)
        pegada = user.get("pegada", "imperial")

        user["poder"] += ganho_poder
        user["xp"] += ganho_xp
        nivel, _ = calcular_nivel(user["xp"])
        user["nivel"] = nivel
        user["ultimo_treino"] = agora.isoformat()

        if user.get("faccao"):
            add_pontos_faccao(user["faccao"], 2)

        save_user(message.author.id, user)

        embed = embed_pegada("⚡ TREINAMENTO IMPERIAL", narrativa, pegada)
        embed.add_field(name="📈 Resultado", value=f"**+{ganho_poder} Poder** | **+{ganho_xp} XP**", inline=False)
        embed.add_field(name="💥 Poder Total", value=f"`{user['poder']}`", inline=True)
        embed.add_field(name="✨ XP Total", value=f"`{user['xp']}`", inline=True)
        embed.add_field(name="📊 Nível", value=f"`{nivel}`", inline=True)
        embed.set_footer(text=f"⏳ Próximo treino em {COOLDOWN_TREINO // 60} minutos")
        await message.channel.send(embed=embed)

    async def handle_missao(self, message, args=None):
        user = get_user(message.author.id)
        uid = message.author.id
        pegada = user.get("pegada", "imperial")

        if uid in self.missoes_ativas:
            missao_ativa = self.missoes_ativas[uid]
            tempo_restante = missao_ativa["fim"] - datetime.utcnow()
            if tempo_restante.total_seconds() > 0:
                mins = int(tempo_restante.total_seconds() // 60)
                segs = int(tempo_restante.total_seconds() % 60)
                await message.channel.send(embed=embed_pegada(
                    "⚔️ Missão em Andamento",
                    f"**{missao_ativa['missao']['nome']}**\n\nRetorna em: **{mins}m {segs}s**",
                    pegada
                ))
                return

        missao = random.choice(MISSOES)
        fim = datetime.utcnow() + timedelta(minutes=missao["duracao_min"])
        self.missoes_ativas[uid] = {"missao": missao, "fim": fim}

        embed = embed_pegada(
            f"📜 MISSÃO: {missao['nome']}",
            f"*{missao['descricao']}*",
            pegada
        )
        embed.add_field(name="⏱️ Duração", value=f"`{missao['duracao_min']} min`", inline=True)
        embed.add_field(name="🏆 Recompensa", value=f"+{missao['recompensa_xp']} XP | +{missao['recompensa_moedas']} Moedas | +{missao['recompensa_poder']} Poder", inline=False)
        embed.set_footer(text="Aguarde o tempo — o bot notificará quando concluir!")
        await message.channel.send(embed=embed)

        await asyncio.sleep(missao["duracao_min"] * 60)

        if uid in self.missoes_ativas:
            del self.missoes_ativas[uid]
            user = get_user(uid)
            user["xp"] += missao["recompensa_xp"]
            user["moedas"] += missao["recompensa_moedas"]
            user["poder"] += missao["recompensa_poder"]
            nivel, _ = calcular_nivel(user["xp"])
            user["nivel"] = nivel
            user["ultima_missao"] = datetime.utcnow().isoformat()
            if user.get("faccao"):
                add_pontos_faccao(user["faccao"], 5)
            save_user(uid, user)
            embed_conc = embed_pegada("🏆 MISSÃO CONCLUÍDA!", missao["narrativa"], pegada)
            embed_conc.add_field(
                name="🎁 Recompensas",
                value=f"**+{missao['recompensa_xp']} XP** | **+{missao['recompensa_moedas']} Moedas** | **+{missao['recompensa_poder']} Poder**",
                inline=False
            )
            try:
                await message.channel.send(f"{message.author.mention}", embed=embed_conc)
            except Exception:
                pass

    async def handle_interagir(self, message, args):
        if not args:
            await message.channel.send(embed=embed_imperial("🎭 Interagir", "Ações: `saudar`, `proclamar`, `reverenciar`, `desafiar`", 0x4B0082))
            return
        acao = args[0].lower()
        alvo = message.mentions[0] if message.mentions else None
        user = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")

        if acao == "saudar":
            if alvo and alvo.id == IMPERADOR_ID:
                texto = f"*{message.author.display_name} se ajoelha profundamente diante do **Imperador Alloy**, tocando a testa no chão de mármore...*\n\n\"Que vossa divindade ilumine eternamente o Império, Ó Grande Imperador!\""
            elif alvo:
                texto = f"*{message.author.display_name} ergue a mão em saudação imperial para {alvo.display_name}.*\n\"Que Tenshi guie seus passos, guerreiro!\""
            else:
                texto = "*Um gesto imperial de boas-vindas ecoa pelo salão...*"
            await message.channel.send(embed=embed_pegada("🤝 Saudação Imperial", texto, pegada))

        elif acao == "proclamar":
            texto = f"📣 *{message.author.display_name} ergue-se sobre o pedestal e proclama lealdade absoluta ao Imperador Alloy e ao Império de Tenshi!*"
            await message.channel.send(embed=embed_pegada("📣 Proclamação", texto, pegada))

        elif acao == "reverenciar":
            if alvo and alvo.id == IMPERADOR_ID:
                texto = f"🙇 *{message.author.display_name} cai de joelhos em reverência total ao **Imperador Alloy**. Uma aura dourada envolve o momento sagrado...*"
                await message.channel.send(embed=embed_imperial("🙇 Reverência Divina", texto, 0xFFD700))
            elif alvo:
                texto = f"🙇 *{message.author.display_name} curva-se respeitosamente diante de {alvo.display_name}.*"
                await message.channel.send(embed=embed_pegada("🙇 Reverência", texto, pegada))
            else:
                await message.channel.send(embed=embed_pegada("🙇 Reverência", f"🙇 *{message.author.display_name} curva-se diante do Império.*", pegada))

        elif acao == "desafiar":
            if alvo:
                texto = f"⚔️ *{message.author.display_name} aponta para {alvo.display_name} com olhos de aço fundido...*\n\n\"Sua hora chegou, {alvo.display_name}. As arenas de Tenshi testemunharão sua queda!\"\n\nUse `Tenshi, duelo @{alvo.display_name}` para iniciar o combate!"
                await message.channel.send(embed=embed_pegada("⚔️ Desafio Lançado", texto, pegada))
            else:
                await message.channel.send(embed=embed_imperial("❓", "Mencione alguém para desafiar.", 0x8B0000))
        else:
            await message.channel.send(embed=embed_imperial("❓", "Ações: `saudar`, `proclamar`, `reverenciar`, `desafiar`", 0x8B0000))
