import discord
from database import get_user, save_user, get_faccoes, add_membro_faccao
from utils import embed_imperial

FACCOES_EMOJIS = {"Guarda Imperial": "⚔️", "Corte de Tenshi": "👑", "Ordem Esotérica": "🔮"}
FACCOES_CORES  = {"Guarda Imperial": 0x8B0000, "Corte de Tenshi": 0xFFD700, "Ordem Esotérica": 0x4B0082}


class Faccoes:
    def __init__(self, bot):
        self.bot = bot

    async def handle_entrar_faccao(self, message, args):
        if not args:
            faccoes = get_faccoes()
            embed = discord.Embed(title="⚔️ FACÇÕES DO IMPÉRIO", description="Escolha sua facção:\n`Tenshi, entrar [nome]`", color=0x4B0082)
            for nome, dados in faccoes.items():
                emoji = FACCOES_EMOJIS.get(nome, "🏛️")
                embed.add_field(name=f"{emoji} {nome}", value=f"*{dados['descricao']}*\n👥 {len(dados['membros'])} | 🏆 {dados['pontos']} pts", inline=False)
            await message.channel.send(embed=embed)
            return

        faccao_nome = " ".join(args).title()
        faccoes = get_faccoes()
        encontrada = None
        for nome in faccoes:
            if faccao_nome.lower() in nome.lower():
                encontrada = nome
                break
        if not encontrada:
            await message.channel.send(embed=embed_imperial("❌", f"Facções: {' | '.join(faccoes.keys())}", 0x8B0000))
            return

        user = get_user(message.author.id)
        if user.get("faccao") == encontrada:
            await message.channel.send(embed=embed_imperial("⚠️", f"Você já faz parte da **{encontrada}**.", 0xFF8C00))
            return

        add_membro_faccao(message.author.id, encontrada)
        user["faccao"] = encontrada
        save_user(message.author.id, user)

        cor = FACCOES_CORES.get(encontrada, 0x4B0082)
        emoji = FACCOES_EMOJIS.get(encontrada, "🏛️")
        embed = discord.Embed(
            title=f"{emoji} JURAMENTO DE FIDELIDADE",
            description=f"**{message.author.display_name}** agora pertence à **{encontrada}**!",
            color=cor
        )
        await message.channel.send(embed=embed)

    async def handle_ranking_faccoes(self, message):
        faccoes = get_faccoes()
        ranking = sorted(faccoes.items(), key=lambda x: x[1]["pontos"], reverse=True)
        embed = discord.Embed(title="🏆 RANKING IMPERIAL DE FACÇÕES", color=0xFFD700)
        medalhas = ["🥇", "🥈", "🥉"]
        for i, (nome, dados) in enumerate(ranking):
            emoji = FACCOES_EMOJIS.get(nome, "🏛️")
            medalha = medalhas[i] if i < 3 else f"#{i+1}"
            embed.add_field(name=f"{medalha} {emoji} {nome}", value=f"🏆 **{dados['pontos']}** pts | 👥 **{len(dados['membros'])}** membros", inline=False)
        embed.set_footer(text="⚡ Pontos ganhos com treinos, missões e duelos")
        await message.channel.send(embed=embed)
