import discord
from discord.ext import commands
from database import get_user, save_user, LOJA_ITEMS
from utils import embed_imperial, IMPERADOR_ID


class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_carteira(self, message):
        user = get_user(message.author.id)
        eh_imperador = message.author.id == IMPERADOR_ID

        embed = discord.Embed(
            title="💰 CÂMARA DO TESOURO IMPERIAL",
            description=f"*Os cofres do Império registram a fortuna de {message.author.display_name}...*",
            color=0xFFD700 if eh_imperador else 0x4B0082
        )
        embed.add_field(name="🪙 Moedas Imperiais", value=f"**{user['moedas']}** moedas", inline=True)
        embed.add_field(name="📊 Nível Econômico", value=self._nivel_economico(user['moedas']), inline=True)
        embed.add_field(name="🎒 Itens no Inventário", value=str(len(user.get('inventario', []))), inline=True)
        embed.set_footer(text="🏦 Tesouro Imperial de Tenshi • Que a prosperidade seja eterna")
        await message.channel.send(embed=embed)

    def _nivel_economico(self, moedas: int) -> str:
        if moedas < 100:
            return "🪨 Súdito Humilde"
        elif moedas < 300:
            return "🥉 Comerciante"
        elif moedas < 700:
            return "🥈 Mercador Imperial"
        elif moedas < 1500:
            return "🥇 Nobre Comerciante"
        else:
            return "💎 Magnata do Império"

    async def handle_loja(self, message):
        embed = discord.Embed(
            title="🏪 MERCADO IMPERIAL DE TENSHI",
            description="*Bem-vindo ao Mercado Imperial, onde os melhores artefatos do Império aguardam por um dono digno...*\n\n**Use:** `Tenshi, comprar [id do item]`",
            color=0x8B6914
        )
        for item in LOJA_ITEMS:
            tipo_emoji = {"arma": "⚔️", "pocao": "🧪", "armadura": "🛡️", "titulo": "👑", "amuleto": "📿", "runa": "🔮"}.get(item["tipo"], "📦")
            embed.add_field(
                name=f"{tipo_emoji} {item['nome']} — `{item['preco']}` moedas",
                value=f"*{item['descricao']}*\n+{item['bonus_poder']} Poder | ID: `{item['id']}`",
                inline=False
            )
        embed.set_footer(text="💰 Os preços são fixados pelo decreto imperial")
        await message.channel.send(embed=embed)

    async def handle_comprar(self, message, args):
        if not args:
            await message.channel.send(embed=embed_imperial("❓ Erro", "Informe o ID do item: `Tenshi, comprar [id]`\nUse `Tenshi, loja` para ver os itens.", 0x8B0000))
            return

        item_id = args[0].lower()
        item = next((i for i in LOJA_ITEMS if i["id"] == item_id), None)

        if not item:
            await message.channel.send(embed=embed_imperial("❌ Item não encontrado", f"O artefato `{item_id}` não existe no Mercado Imperial. Use `Tenshi, loja` para ver os disponíveis.", 0x8B0000))
            return

        user = get_user(message.author.id)

        if item["nome"] in user.get("inventario", []):
            await message.channel.send(embed=embed_imperial("⚠️ Já Adquirido", f"Você já possui **{item['nome']}** em seu inventário.", 0xFF8C00))
            return

        if user["moedas"] < item["preco"]:
            falta = item["preco"] - user["moedas"]
            await message.channel.send(embed=embed_imperial(
                "💸 Moedas Insuficientes",
                f"*Os guardas do tesouro bloqueiam sua passagem...*\n\nVocê precisa de **{falta}** moedas a mais para adquirir **{item['nome']}**.",
                0x8B0000
            ))
            return

        user["moedas"] -= item["preco"]
        user["poder"] += item["bonus_poder"]
        if user.get("inventario") is None:
            user["inventario"] = []
        user["inventario"].append(item["nome"])

        if item["tipo"] == "titulo":
            user["titulo"] = item["nome"].replace("Título: ", "")

        save_user(message.author.id, user)

        tipo_emoji = {"arma": "⚔️", "pocao": "🧪", "armadura": "🛡️", "titulo": "👑", "amuleto": "📿", "runa": "🔮"}.get(item["tipo"], "📦")

        embed = discord.Embed(
            title=f"{tipo_emoji} AQUISIÇÃO IMPERIAL",
            description=f"*Os selos do Mercado Imperial foram apostos...*\n\n**{item['nome']}** agora pertence a {message.author.display_name}.",
            color=0xFFD700
        )
        embed.add_field(name="💸 Custo", value=f"`{item['preco']}` moedas", inline=True)
        embed.add_field(name="⚡ Bônus Recebido", value=f"+{item['bonus_poder']} Poder de Luta", inline=True)
        embed.add_field(name="💰 Saldo Restante", value=f"`{user['moedas']}` moedas", inline=True)
        embed.set_footer(text="🏪 Que este artefato sirva bem ao Império")
        await message.channel.send(embed=embed)
