import discord
from database import get_casas, comprar_casa, vender_casa, get_user
from utils import embed_imperial, CORES_PEGADA

TIPO_COR = {
    "Modesta":    0x8B6914,
    "Nobre":      0xFFD700,
    "Mística":    0x4B0082,
    "Militar":    0x8B0000,
    "Luxuosa":    0xC0C0C0,
    "Lendária":   0xFF8C00,
    "Rústica":    0x556B2F,
    "Clandestina":0x1C1C1C,
}


class BotaoCasa(discord.ui.Button):
    def __init__(self, casa_id: str, casa: dict):
        disponivel = casa["dono"] is None
        label = casa["nome"][:20]
        emoji = casa["emoji"]
        style = discord.ButtonStyle.green if disponivel else discord.ButtonStyle.red
        super().__init__(label=label, emoji=emoji, style=style, custom_id=f"casa_{casa_id}", disabled=not disponivel)
        self.casa_id = casa_id
        self.casa = casa

    async def callback(self, interaction: discord.Interaction):
        casa = self.casa
        casas_atuais = get_casas()
        casa_atual = casas_atuais.get(self.casa_id, casa)
        if casa_atual["dono"] is not None:
            await interaction.response.send_message(
                embed=embed_imperial("🔒 Propriedade Ocupada", f"**{casa['nome']}** já pertence a outro habitante.", 0x8B0000),
                ephemeral=True
            )
            return
        user = get_user(interaction.user.id)
        embed = discord.Embed(
            title=f"{casa['emoji']} CONFIRMAR COMPRA",
            description=f"**{casa['nome']}**\n*{casa['descricao']}*",
            color=TIPO_COR.get(casa["tipo"], 0x4B0082)
        )
        embed.add_field(name="💰 Preço", value=f"**{casa['preco']}** moedas", inline=True)
        embed.add_field(name="🏠 Tipo", value=casa["tipo"], inline=True)
        embed.add_field(name="🛏️ Cômodos", value=str(casa["comodos"]), inline=True)
        embed.add_field(name="💼 Sua carteira", value=f"**{user['moedas']}** moedas + **{user.get('conta_banco',0)}** no banco", inline=False)
        view = ConfirmarCompraCasa(self.casa_id, casa, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ConfirmarCompraCasa(discord.ui.View):
    def __init__(self, casa_id: str, casa: dict, user_id: int):
        super().__init__(timeout=60)
        self.casa_id = casa_id
        self.casa = casa
        self.user_id = user_id

    @discord.ui.button(label="✅ Confirmar Compra", style=discord.ButtonStyle.green)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Esta confirmação não é sua!", ephemeral=True)
            return
        ok, msg = comprar_casa(interaction.user.id, self.casa_id)
        if ok:
            embed = discord.Embed(
                title=f"{self.casa['emoji']} PROPRIEDADE ADQUIRIDA!",
                description=f"*Os selos imperiais foram apostos no pergaminho...*\n\n"
                           f"**{interaction.user.display_name}** agora é o orgulhoso habitante de **{self.casa['nome']}**!\n\n"
                           f"*{self.casa['descricao']}*",
                color=TIPO_COR.get(self.casa["tipo"], 0x4B0082)
            )
            embed.add_field(name="🏠 Tipo", value=self.casa["tipo"], inline=True)
            embed.add_field(name="🛏️ Cômodos", value=str(self.casa["comodos"]), inline=True)
            embed.set_footer(text="🏛️ Esta propriedade é exclusivamente sua — ninguém mais pode comprá-la")
            self.clear_items()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(embed=embed_imperial("❌ Erro", msg, 0x8B0000), ephemeral=True)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=embed_imperial("🚪 Cancelado", "A compra foi cancelada.", 0x2C2F33),
            view=None
        )


class VisualizarCasas(discord.ui.View):
    def __init__(self, casas: dict, pagina: int = 0):
        super().__init__(timeout=120)
        self.casas = casas
        self.pagina = pagina
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        items = list(self.casas.items())
        inicio = self.pagina * 4
        fim = inicio + 4
        pagina_items = items[inicio:fim]
        for casa_id, casa in pagina_items:
            self.add_item(BotaoCasa(casa_id, casa))
        if self.pagina > 0:
            btn_ant = discord.ui.Button(label="◀ Anterior", style=discord.ButtonStyle.blurple, row=2)
            btn_ant.callback = self.pagina_anterior
            self.add_item(btn_ant)
        if fim < len(items):
            btn_prox = discord.ui.Button(label="Próxima ▶", style=discord.ButtonStyle.blurple, row=2)
            btn_prox.callback = self.proxima_pagina
            self.add_item(btn_prox)

    async def proxima_pagina(self, interaction: discord.Interaction):
        self.pagina += 1
        self._build_buttons()
        await interaction.response.edit_message(view=self)

    async def pagina_anterior(self, interaction: discord.Interaction):
        self.pagina -= 1
        self._build_buttons()
        await interaction.response.edit_message(view=self)


class Casas:
    def __init__(self, bot):
        self.bot = bot

    async def handle_casas(self, message):
        casas = get_casas()
        disponiveis = sum(1 for c in casas.values() if c["dono"] is None)
        embed = discord.Embed(
            title="🏠 MERCADO IMOBILIÁRIO DE TENSHI",
            description=f"*{disponiveis} propriedades disponíveis* — Clique para comprar!\n\n"
                       f"🟢 Disponível | 🔴 Ocupada\n\n"
                       f"Os botões abaixo mostram as propriedades. Clique para ver detalhes e confirmar a compra.",
            color=0x8B6914
        )
        for casa_id, casa in casas.items():
            status = "🟢 Disponível" if casa["dono"] is None else "🔴 Ocupada"
            embed.add_field(
                name=f"{casa['emoji']} {casa['nome']} — {casa['preco']} moedas",
                value=f"Tipo: **{casa['tipo']}** | {status} | 🛏️ {casa['comodos']} cômodos",
                inline=False
            )
        embed.set_footer(text="🏛️ Uma propriedade por guerreiro — escolha com sabedoria")
        view = VisualizarCasas(casas)
        await message.channel.send(embed=embed, view=view)

    async def handle_minha_casa(self, message):
        user = get_user(message.author.id)
        casa_id = user.get("casa_id")
        if not casa_id:
            await message.channel.send(embed=embed_imperial(
                "🏠 Sem Moradia",
                "*Você ainda não possui uma propriedade no Império...*\n\nUse `Tenshi, casas` para ver as disponíveis.",
                0x2C2F33
            ))
            return
        casas = get_casas()
        casa = casas.get(casa_id)
        if not casa:
            await message.channel.send(embed=embed_imperial("❌ Erro", "Propriedade não encontrada.", 0x8B0000))
            return
        embed = discord.Embed(
            title=f"{casa['emoji']} MINHA PROPRIEDADE",
            description=f"*{casa['descricao']}*",
            color=TIPO_COR.get(casa["tipo"], 0x4B0082)
        )
        embed.add_field(name="🏠 Nome", value=casa["nome"], inline=True)
        embed.add_field(name="📦 Tipo", value=casa["tipo"], inline=True)
        embed.add_field(name="🛏️ Cômodos", value=str(casa["comodos"]), inline=True)
        embed.add_field(name="💎 Valor de Mercado", value=f"{casa['preco']} moedas", inline=True)
        embed.add_field(name="💸 Valor de Venda (70%)", value=f"{int(casa['preco']*0.7)} moedas", inline=True)
        embed.set_footer(text="Use 'Tenshi, vender-casa' para vender a propriedade")
        await message.channel.send(embed=embed)

    async def handle_vender_casa(self, message):
        ok, nome, valor = vender_casa(message.author.id)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Erro", nome, 0x8B0000))
            return
        embed = discord.Embed(
            title="💸 PROPRIEDADE VENDIDA",
            description=f"*{message.author.display_name} assina os papéis de venda...*\n\n"
                       f"**{nome}** foi vendida por **{valor} moedas** (70% do valor original).\n"
                       f"O imóvel está disponível novamente no mercado.",
            color=0x006400
        )
        embed.set_footer(text="🏛️ O mercado imobiliário de Tenshi aguarda novos proprietários")
        await message.channel.send(embed=embed)
