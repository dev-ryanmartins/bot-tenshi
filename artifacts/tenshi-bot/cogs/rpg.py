import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from database import get_user, save_user, add_pontos_faccao
from utils import embed_imperial, calcular_nivel, COOLDOWN_TREINO, COOLDOWN_MISSAO, IMPERADOR_ID

MISSOES = [
    {
        "nome": "Patrulha nas Fronteiras do Norte",
        "descricao": "Rumores de criaturas sombrias se aproximando das muralhas imperiais. O Império precisa de guardiões vigilantes.",
        "narrativa": "🌑 *As chamas das tochas tremem enquanto você avança pelas fronteiras geladas... O peso da armadura contrasta com o silêncio mortal da noite. De repente — um rugido distante ecoa nos vales.*\n\n**Você ergueu a espada e enfrentou a escuridão. O Império está mais seguro graças ao seu sacrifício.**",
        "recompensa_xp": 80,
        "recompensa_moedas": 60,
        "recompensa_poder": 15,
        "duracao_min": 2,
    },
    {
        "nome": "Missão Diplomática na Corte Rival",
        "descricao": "Uma delegação deve ser enviada para negociar termos com o clã rival. Eloquência e astúcia são essenciais.",
        "narrativa": "👑 *Você adentrou os salões de mármore da corte rival, onde cada palavra carrega o peso de mil espadas... Os olhos dos nobres te espreitam com desconfiança. Você manteve a compostura imperial.*\n\n**Após horas de negociação tensa, os termos foram aceitos. Tenshi expande sua influência.**",
        "recompensa_xp": 100,
        "recompensa_moedas": 90,
        "recompensa_poder": 10,
        "duracao_min": 3,
    },
    {
        "nome": "Investigação nas Catacumbas Místicas",
        "descricao": "Antigas runas foram ativadas nas profundezas. Um agente deve investigar antes que o portal se abra completamente.",
        "narrativa": "🔮 *As paredes das catacumbas pulsam com uma luz violeta sobrenatural... Runas antigas giram no ar ao seu redor, sussurrando segredos em línguas esquecidas. Você sentiu o véu entre os mundos se estreitar.*\n\n**Você decifrou o símbolo proibido e selou o portal. O equilíbrio místico de Tenshi foi preservado.**",
        "recompensa_xp": 120,
        "recompensa_moedas": 70,
        "recompensa_poder": 25,
        "duracao_min": 4,
    },
    {
        "nome": "Escolta do Mensageiro Imperial",
        "descricao": "Um mensageiro carrega decretos secretos do Imperador. Proteja-o a qualquer custo.",
        "narrativa": "⚔️ *A estrada está silenciosa demais... Seu instinto militar dispara. De trás das árvores, capangas mascarados saltam sobre a comitiva! O aço canta no ar enquanto você os enfrenta um a um.*\n\n**O mensageiro chegou em segurança. A palavra do Imperador Alloy foi entregue.**",
        "recompensa_xp": 90,
        "recompensa_moedas": 75,
        "recompensa_poder": 20,
        "duracao_min": 2,
    },
]

TREINOS = [
    "🔥 *Você passou horas meditando sob a cachoeira gelada, forçando sua mente e corpo além dos limites humanos. As águas cantavam segredos antigos enquanto seu poder crescia...*",
    "⚔️ *Mil golpes contra a pedra sagrada. Seus punhos sangram, mas a dor é apenas um professor severo. O Imperador Alloy observaria com aprovação.*",
    "🌙 *Sob a lua cheia de Tenshi, você canalizou a energia das estrelas pelo seu corpo. Cada respiração expandia seu poder de luta como uma chama que se recusa a morrer.*",
    "💪 *As arenas de treino da Guarda Imperial testemunharam seu esforço hoje. Os veteranos pararam para observar — raramente viam tal determinação em um único ser.*",
    "🌊 *Você mergulhou nas profundezas do Rio Eterno, onde a pressão da água forja campeões ou mata os fracos. Você emergiu transformado.*",
]


class RPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.missoes_ativas = {}

    async def handle_perfil(self, message):
        user = get_user(message.author.id)
        nome = user.get("nome") or message.author.display_name
        nivel, xp_proximo = calcular_nivel(user["xp"])
        user["nivel"] = nivel
        save_user(message.author.id, user)

        barra_xp = int((user["xp"] % 100) / 10)
        barra = "█" * barra_xp + "░" * (10 - barra_xp)

        faccao = user.get("faccao") or "Sem Facção"
        inventario = user.get("inventario") or []
        inv_str = ", ".join(inventario) if inventario else "Vazio"

        bonus = user.get("status_bonus", {})
        bonus_str = ""
        if bonus:
            bonus_str = "\n".join([f"• {k}: +{v}" for k, v in bonus.items()])
        else:
            bonus_str = "Nenhum bônus ativo"

        eh_imperador = message.author.id == IMPERADOR_ID

        titulo_exibir = "⚜️ **O IMPERADOR SUPREMO DE TENSHI** ⚜️" if eh_imperador else user.get("titulo", "Cidadão do Império")
        cor = 0xFFD700 if eh_imperador else 0x4B0082

        embed = discord.Embed(
            title=f"{'👁️ DIVINDADE IMPERIAL' if eh_imperador else '📜 REGISTRO IMPERIAL'}",
            description=f"*Os Pergaminhos de Tenshi revelam a essência de {nome}...*",
            color=cor
        )
        embed.add_field(name="👤 Nome", value=nome, inline=True)
        embed.add_field(name="🏛️ Título", value=titulo_exibir, inline=True)
        embed.add_field(name="⚡ Facção", value=faccao, inline=True)
        embed.add_field(name="📊 Nível", value=f"`{nivel}`", inline=True)
        embed.add_field(name="💥 Poder de Luta", value=f"`{user['poder']}`", inline=True)
        embed.add_field(name="💰 Moedas Imperiais", value=f"`{user['moedas']}`", inline=True)
        embed.add_field(name="✨ Experiência", value=f"`{user['xp']} XP`\n`{barra}` → Próx. nível: {xp_proximo}", inline=False)
        embed.add_field(name="🎒 Inventário", value=inv_str, inline=False)
        embed.add_field(name="🌟 Bônus Ativos", value=bonus_str, inline=False)

        if eh_imperador:
            embed.set_footer(text="⚜️ Que Tenshi trema diante de sua presença, ó Imperador Alloy ⚜️")
        else:
            embed.set_footer(text="🏛️ Registro Imperial de Tenshi • Que sua glória cresça")

        embed.set_thumbnail(url=message.author.display_avatar.url)
        await message.channel.send(embed=embed)

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
                embed = embed_imperial(
                    "⏳ Corpo em Recuperação",
                    f"*Seu corpo ainda absorve os ensinamentos do último treino...*\n\n"
                    f"Descanse, guerreiro. O próximo treino estará disponível em **{minutos}m {segundos}s**.",
                    0x8B0000
                )
                await message.channel.send(embed=embed)
                return

        ganho_poder = random.randint(5, 20)
        ganho_xp = random.randint(20, 50)
        narrativa = random.choice(TREINOS)

        user["poder"] += ganho_poder
        user["xp"] += ganho_xp
        user["nivel"] = calcular_nivel(user["xp"])[0]
        user["ultimo_treino"] = agora.isoformat()

        if user.get("faccao"):
            add_pontos_faccao(user["faccao"], 2)

        save_user(message.author.id, user)

        embed = discord.Embed(
            title="⚡ TREINAMENTO IMPERIAL",
            description=narrativa,
            color=0x4B0082
        )
        embed.add_field(name="📈 Resultado", value=f"**+{ganho_poder} Poder de Luta**\n**+{ganho_xp} XP**", inline=False)
        embed.add_field(name="💥 Poder Atual", value=f"`{user['poder']}`", inline=True)
        embed.add_field(name="✨ XP Total", value=f"`{user['xp']}`", inline=True)
        embed.set_footer(text=f"⏳ Próximo treino disponível em {COOLDOWN_TREINO // 60} minutos")
        await message.channel.send(embed=embed)

    async def handle_missao(self, message, args=None):
        user = get_user(message.author.id)
        uid = message.author.id

        if uid in self.missoes_ativas:
            missao_ativa = self.missoes_ativas[uid]
            tempo_restante = missao_ativa["fim"] - datetime.utcnow()
            if tempo_restante.total_seconds() > 0:
                mins = int(tempo_restante.total_seconds() // 60)
                segs = int(tempo_restante.total_seconds() % 60)
                embed = embed_imperial(
                    "⚔️ Missão em Andamento",
                    f"*Você já está em campo, guerreiro...*\n\n"
                    f"**{missao_ativa['missao']['nome']}**\n\n"
                    f"Retorna em: **{mins}m {segs}s**",
                    0x8B4513
                )
                await message.channel.send(embed=embed)
                return

        missao = random.choice(MISSOES)
        fim = datetime.utcnow() + timedelta(minutes=missao["duracao_min"])
        self.missoes_ativas[uid] = {"missao": missao, "fim": fim}

        embed = discord.Embed(
            title=f"📜 MISSÃO ACEITA: {missao['nome']}",
            description=f"*Os selos imperiais foram apostos no pergaminho...*\n\n{missao['descricao']}",
            color=0x006400
        )
        embed.add_field(name="⏱️ Duração", value=f"`{missao['duracao_min']} minutos`", inline=True)
        embed.add_field(name="🏆 Recompensa Prevista", value=f"+{missao['recompensa_xp']} XP | +{missao['recompensa_moedas']} Moedas | +{missao['recompensa_poder']} Poder", inline=False)
        embed.set_footer(text="Use 'Tenshi, completar-missao' após o tempo para receber suas recompensas")
        await message.channel.send(embed=embed)

        await asyncio.sleep(missao["duracao_min"] * 60)

        if uid in self.missoes_ativas:
            del self.missoes_ativas[uid]
            user = get_user(uid)
            user["xp"] += missao["recompensa_xp"]
            user["moedas"] += missao["recompensa_moedas"]
            user["poder"] += missao["recompensa_poder"]
            user["nivel"] = calcular_nivel(user["xp"])[0]
            user["ultima_missao"] = datetime.utcnow().isoformat()

            if user.get("faccao"):
                add_pontos_faccao(user["faccao"], 5)

            save_user(uid, user)

            embed = discord.Embed(
                title="🏆 MISSÃO CONCLUÍDA!",
                description=missao["narrativa"],
                color=0xFFD700
            )
            embed.add_field(name="🎁 Recompensas Recebidas", value=f"**+{missao['recompensa_xp']} XP** | **+{missao['recompensa_moedas']} Moedas Imperiais** | **+{missao['recompensa_poder']} Poder**", inline=False)
            embed.set_footer(text="O Império reconhece seu serviço, guerreiro.")
            try:
                await message.channel.send(f"{message.author.mention}", embed=embed)
            except Exception:
                pass

    async def handle_interagir(self, message, args):
        if not args:
            await message.channel.send(embed=embed_imperial("🎭 Interagir", "Especifique uma interação: `saudar`, `proclamar`, `reverenciar`", 0x4B0082))
            return

        acao = args[0].lower()
        alvo = message.mentions[0] if message.mentions else None

        if acao == "saudar":
            if alvo:
                if alvo.id == IMPERADOR_ID:
                    texto = f"*{message.author.display_name} se ajoelha profundamente diante do **Imperador Alloy**, tocando a testa no chão frio de mármore...*\n\n\"Que vossa divindade ilumine eternamente o Império de Tenshi, Ó Grande Imperador!\""
                else:
                    texto = f"*{message.author.display_name} ergue a mão direita em saudação imperial para {alvo.display_name}...*\n\n\"Que Tenshi guie seus passos, guerreiro!\""
            else:
                texto = "*Um gesto imperial de boas-vindas ecoa pelo salão...*"
            await message.channel.send(embed=embed_imperial("🤝 Saudação Imperial", texto, 0x4B0082))

        elif acao == "proclamar":
            texto = f"📣 *{message.author.display_name} ergue-se sobre o pedestal imperial e proclama sua lealdade absoluta ao Imperador Alloy e ao Império de Tenshi, fazendo sua voz ecoar pelos corredores eternos do poder!*"
            await message.channel.send(embed=embed_imperial("📣 Proclamação de Lealdade", texto, 0x8B0000))

        elif acao == "reverenciar":
            if alvo and alvo.id == IMPERADOR_ID:
                texto = f"🙇 *{message.author.display_name} cai de joelhos, inclinando-se em reverência total diante da divindade viva que é o **Imperador Alloy**. Uma aura dourada envolve o momento sagrado...*"
                cor = 0xFFD700
            elif alvo:
                texto = f"🙇 *{message.author.display_name} curva-se respeitosamente diante de {alvo.display_name}, reconhecendo sua posição no Império.*"
                cor = 0x4B0082
            else:
                texto = f"🙇 *{message.author.display_name} curva-se diante do Império de Tenshi, reconhecendo a grandeza do trono.*"
                cor = 0x4B0082
            await message.channel.send(embed=embed_imperial("🙇 Reverência", texto, cor))

        else:
            await message.channel.send(embed=embed_imperial("❓ Ação Desconhecida", "Ações disponíveis: `saudar`, `proclamar`, `reverenciar`", 0x8B0000))
