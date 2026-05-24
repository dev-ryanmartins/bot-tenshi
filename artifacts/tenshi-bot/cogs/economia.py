import discord
from database import get_user, save_user, LOJA_ITEMS, calcular_nivel
from utils import embed_imperial, embed_pegada, IMPERADOR_ID


class Economia:
    def __init__(self, bot):
        self.bot = bot

    async def handle_carteira(self, message):
        user = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")
        eh_imperador = message.author.id == IMPERADOR_ID
        moedas = user.get("moedas", 0)
        banco = user.get("conta_banco", 0)
        emprestimos = user.get("emprestimos", [])
        divida = sum(e["valor_restante"] for e in emprestimos)

        embed = discord.Embed(
            title="💰 CÂMARA DO TESOURO IMPERIAL",
            description=f"*Os cofres do Império registram a fortuna de {message.author.display_name}...*",
            color=0xFFD700 if eh_imperador else 0x8B6914
        )
        embed.add_field(name="🪙 Em Mãos", value=f"**{moedas}** moedas", inline=True)
        embed.add_field(name="🏦 No Banco", value=f"**{banco}** moedas", inline=True)
        embed.add_field(name="💸 Dívidas", value=f"**{divida}** moedas", inline=True)
        embed.add_field(name="💎 Patrimônio Líquido", value=f"**{moedas + banco - divida}** moedas", inline=False)
        embed.add_field(name="📊 Nível Econômico", value=self._nivel_economico(moedas + banco), inline=True)
        embed.add_field(name="🎒 Itens", value=str(len(user.get("inventario", []))), inline=True)
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text="Use 'Tenshi, banco' para ver detalhes financeiros completos")
        await message.channel.send(embed=embed)

    def _nivel_economico(self, total: int) -> str:
        if total < 100:   return "🪨 Súdito Humilde"
        if total < 300:   return "🥉 Comerciante"
        if total < 700:   return "🥈 Mercador Imperial"
        if total < 1500:  return "🥇 Nobre Comerciante"
        if total < 5000:  return "💎 Magnata do Império"
        return "🏆 Tycoon Imperial"

    async def handle_loja(self, message):
        embed = discord.Embed(
            title="🏪 MERCADO IMPERIAL DE TENSHI",
            description="*Bem-vindo ao Mercado Imperial...*\n\nUse: `Tenshi, comprar [id do item]`",
            color=0x8B6914
        )
        tipo_emoji = {"arma": "⚔️", "pocao": "🧪", "armadura": "🛡️", "titulo": "👑", "amuleto": "📿", "runa": "🔮", "acessorio": "💼"}
        for item in LOJA_ITEMS:
            emoji = tipo_emoji.get(item["tipo"], "📦")
            embed.add_field(
                name=f"{emoji} {item['nome']} — `{item['preco']}` moedas",
                value=f"*{item['descricao']}*\n+{item['bonus_poder']} Poder | ID: `{item['id']}`",
                inline=False
            )
        embed.set_footer(text="💰 Preços fixados por decreto imperial")
        await message.channel.send(embed=embed)

    async def handle_comprar(self, message, args):
        if not args:
            await message.channel.send(embed=embed_imperial("❓", "Informe o ID: `Tenshi, comprar [id]`\nVeja a loja: `Tenshi, loja`", 0x8B0000))
            return
        item_id = args[0].lower()
        item = next((i for i in LOJA_ITEMS if i["id"] == item_id), None)
        if not item:
            await message.channel.send(embed=embed_imperial("❌ Não encontrado", f"Item `{item_id}` não existe. Use `Tenshi, loja`.", 0x8B0000))
            return
        user = get_user(message.author.id)
        if item["nome"] in user.get("inventario", []):
            await message.channel.send(embed=embed_imperial("⚠️ Já Adquirido", f"Você já possui **{item['nome']}**.", 0xFF8C00))
            return
        if user["moedas"] < item["preco"]:
            falta = item["preco"] - user["moedas"]
            await message.channel.send(embed=embed_imperial("💸 Insuficiente", f"Você precisa de **{falta}** moedas a mais para **{item['nome']}**.", 0x8B0000))
            return
        user["moedas"] -= item["preco"]
        user["poder"] += item["bonus_poder"]
        user.setdefault("inventario", []).append(item["nome"])
        if item["tipo"] == "titulo":
            user["titulo"] = item["nome"].replace("Título: ", "")
        save_user(message.author.id, user)
        tipo_emoji = {"arma": "⚔️", "pocao": "🧪", "armadura": "🛡️", "titulo": "👑", "amuleto": "📿", "runa": "🔮", "acessorio": "💼"}
        emoji = tipo_emoji.get(item["tipo"], "📦")
        embed = discord.Embed(
            title=f"{emoji} AQUISIÇÃO IMPERIAL",
            description=f"*{item['nome']}* agora pertence a {message.author.display_name}.",
            color=0xFFD700
        )
        embed.add_field(name="💸 Custo", value=f"`{item['preco']}` moedas", inline=True)
        embed.add_field(name="⚡ Bônus", value=f"+{item['bonus_poder']} Poder", inline=True)
        embed.add_field(name="💰 Saldo", value=f"`{user['moedas']}` moedas", inline=True)
        embed.set_footer(text="🏪 Que este artefato sirva bem ao Império")
        await message.channel.send(embed=embed)
