import discord
from discord.ext import commands
from database import get_user, save_user, get_faccoes, add_membro_faccao
from utils import embed_imperial

FACCOES_EMOJIS = {
    "Guarda Imperial": "⚔️",
    "Corte de Tenshi": "👑",
    "Ordem Esotérica": "🔮",
}

FACCOES_CORES = {
    "Guarda Imperial": 0x8B0000,
    "Corte de Tenshi": 0xFFD700,
    "Ordem Esotérica": 0x4B0082,
}


class Faccoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_entrar_faccao(self, message, args):
        if not args:
            faccoes = get_faccoes()
            embed = discord.Embed(
                title="⚔️ FACÇÕES DO IMPÉRIO DE TENSHI",
                description="*Escolha sua facção e junte-se à causa imperial...*\n\nUse: `Tenshi, entrar [nome da facção]`",
                color=0x4B0082
            )
            for nome, dados in faccoes.items():
                emoji = FACCOES_EMOJIS.get(nome, "🏛️")
                membros = len(dados["membros"])
                embed.add_field(
                    name=f"{emoji} {nome}",
                    value=f"*{dados['descricao']}*\n👥 Membros: **{membros}** | 🏆 Pontos: **{dados['pontos']}**",
                    inline=False
                )
            embed.set_footer(text="⚔️ A lealdade à facção é eterna — escolha com sabedoria")
            await message.channel.send(embed=embed)
            return

        faccao_nome = " ".join(args).title()
        faccoes = get_faccoes()

        # Busca parcial
        encontrada = None
        for nome in faccoes:
            if faccao_nome.lower() in nome.lower():
                encontrada = nome
                break

        if not encontrada:
            opcoes = " | ".join(faccoes.keys())
            await message.channel.send(embed=embed_imperial("❌ Facção não encontrada", f"Facções disponíveis: **{opcoes}**", 0x8B0000))
            return

        user = get_user(message.author.id)
        faccao_atual = user.get("faccao")

        if faccao_atual == encontrada:
            await message.channel.send(embed=embed_imperial("⚠️ Já é Membro", f"Você já faz parte da **{encontrada}**.", 0xFF8C00))
            return

        add_membro_faccao(message.author.id, encontrada)
        user["faccao"] = encontrada
        save_user(message.author.id, user)

        emoji = FACCOES_EMOJIS.get(encontrada, "🏛️")
        cor = FACCOES_CORES.get(encontrada, 0x4B0082)

        embed = discord.Embed(
            title=f"{emoji} JURAMENTO DE FIDELIDADE",
            description=f"*As chamas do juramento acendem enquanto {message.author.display_name} se ajoelha perante os estandartes da facção...*\n\n**{message.author.display_name}** agora pertence à **{encontrada}**!\n\n*{faccoes[encontrada]['descricao']}*",
            color=cor
        )
        embed.set_footer(text="⚔️ Sua lealdade foi registrada nos Pergaminhos Imperiais")
        await message.channel.send(embed=embed)

    async def handle_ranking_faccoes(self, message):
        faccoes = get_faccoes()
        ranking = sorted(faccoes.items(), key=lambda x: x[1]["pontos"], reverse=True)

        embed = discord.Embed(
            title="🏆 RANKING IMPERIAL DE FACÇÕES",
            description="*Os olhos do Império observam... Qual facção dominará Tenshi?*",
            color=0xFFD700
        )

        medalhas = ["🥇", "🥈", "🥉"]
        for i, (nome, dados) in enumerate(ranking):
            emoji = FACCOES_EMOJIS.get(nome, "🏛️")
            medalha = medalhas[i] if i < 3 else f"#{i+1}"
            embed.add_field(
                name=f"{medalha} {emoji} {nome}",
                value=f"🏆 **{dados['pontos']}** pontos | 👥 **{len(dados['membros'])}** membros",
                inline=False
            )

        embed.set_footer(text="⚡ Pontos são ganhos com treinos, missões e vitórias em duelos")
        await message.channel.send(embed=embed)
