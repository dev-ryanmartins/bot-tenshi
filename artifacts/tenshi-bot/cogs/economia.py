import discord
import random
from database import get_user, save_user, LOJA_ITEMS
from utils import embed_imperial, SEP, RODAPE_IMPERIAL, CORES_PEGADA, IMPERADOR_ID

MERCADO_NEGRO_ITENS = [
    {"id": "veneno_sombrio",      "nome": "Veneno das Sombras",       "preco": 350,  "tipo": "consumivel", "bonus_poder": 45, "descricao": "Uma essência proibida extraída das catacumbas. Proibida pela Corte, adorada pela Máfia."},
    {"id": "relíquia_proibida",   "nome": "Relíquia Proibida",        "preco": 600,  "tipo": "relíquia",   "bonus_poder": 90, "descricao": "Um artefato antigo que emana energia perturbadora. Apenas os corajosos ousam carregá-la."},
    {"id": "mapa_catacumbas",     "nome": "Mapa das Catacumbas Negras","preco": 200,  "tipo": "documento",  "bonus_poder": 20, "descricao": "Mostra passagens secretas que a Guarda Imperial não sabe que existem."},
    {"id": "elixir_poder",        "nome": "Elixir do Poder Proibido",  "preco": 450,  "tipo": "consumivel", "bonus_poder": 70, "descricao": "Síntese ilegal de runas e poções. Amplifica o poder exponencialmente — por um preço."},
    {"id": "identidade_falsa",    "nome": "Identidade Falsa",         "preco": 280,  "tipo": "documento",  "bonus_poder": 0,  "descricao": "Documentos que permitem circular livremente entre facções inimigas."},
    {"id": "grimorio_proibido",   "nome": "Grimório Proibido",        "preco": 800,  "tipo": "grimório",   "bonus_poder": 110,"descricao": "Um livro de feitiços banidos pelo Concílio Esotérico. Poder supremo, risco supremo."},
]

TIPO_EMOJI = {
    "arma":      "⚔️",
    "pocao":     "🧪",
    "armadura":  "🛡️",
    "titulo":    "👑",
    "amuleto":   "📿",
    "runa":      "🔮",
    "acessorio": "💼",
    "consumivel":"⚗️",
    "relíquia":  "🏺",
    "documento": "📄",
    "grimório":  "📖",
}


class LojaView(discord.ui.View):
    """Loja com paginação e botão de compra"""

    def __init__(self, user_id: int, itens: list, titulo: str, cor: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.itens   = itens
        self.titulo  = titulo
        self.cor     = cor
        self.pagina  = 0
        self.por_pag = 4
        self._atualizar_botoes()

    def _build_embed(self) -> discord.Embed:
        inicio = self.pagina * self.por_pag
        fim    = inicio + self.por_pag
        pagina_itens = self.itens[inicio:fim]
        total_pags = max(1, (len(self.itens) + self.por_pag - 1) // self.por_pag)

        embed = discord.Embed(
            title=self.titulo,
            description=f"*Use o ID do item para comprar*\n{SEP}",
            color=self.cor
        )
        for item in pagina_itens:
            emoji = TIPO_EMOJI.get(item["tipo"], "📦")
            embed.add_field(
                name=f"{emoji} **{item['nome']}** — `{item['preco']}` moedas",
                value=(
                    f"*{item['descricao']}*\n"
                    f"⚡ +{item['bonus_poder']} Poder  `•`  ID: `{item['id']}`"
                ),
                inline=False
            )
        embed.set_footer(text=f"Página {self.pagina+1}/{total_pags}  •  {RODAPE_IMPERIAL}")
        return embed

    def _atualizar_botoes(self):
        self.clear_items()
        total_pags = max(1, (len(self.itens) + self.por_pag - 1) // self.por_pag)

        if self.pagina > 0:
            btn_ant = discord.ui.Button(label="◀ Anterior", style=discord.ButtonStyle.secondary, row=1)
            btn_ant.callback = self._cb_anterior
            self.add_item(btn_ant)

        if self.pagina < total_pags - 1:
            btn_prox = discord.ui.Button(label="Próxima ▶", style=discord.ButtonStyle.secondary, row=1)
            btn_prox.callback = self._cb_proxima
            self.add_item(btn_prox)

        inicio = self.pagina * self.por_pag
        fim    = inicio + self.por_pag
        pagina_itens = self.itens[inicio:fim]

        for item in pagina_itens:
            emoji = TIPO_EMOJI.get(item["tipo"], "📦")
            btn = discord.ui.Button(
                label=f"{emoji} {item['nome'][:20]} ({item['preco']})",
                style=discord.ButtonStyle.success,
                row=0
            )
            btn.callback = self._make_compra_cb(item)
            self.add_item(btn)

    def _make_compra_cb(self, item: dict):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("*Esta loja foi aberta para outro comprador.*", ephemeral=True)
                return
            user = get_user(interaction.user.id)
            if item["nome"] in user.get("inventario", []):
                await interaction.response.send_message(
                    embed=embed_imperial("⚠️", f"Você já possui **{item['nome']}**.", 0xFF8C00),
                    ephemeral=True
                )
                return
            if user["moedas"] < item["preco"]:
                falta = item["preco"] - user["moedas"]
                await interaction.response.send_message(
                    embed=embed_imperial("💸", f"Faltam **{falta}** moedas para **{item['nome']}**.", 0x6B0000),
                    ephemeral=True
                )
                return
            user["moedas"] -= item["preco"]
            user["poder"]  += item["bonus_poder"]
            user.setdefault("inventario", []).append(item["nome"])
            if item["tipo"] == "titulo":
                user["titulo"] = item["nome"].replace("Título: ", "")
            save_user(interaction.user.id, user)
            emoji = TIPO_EMOJI.get(item["tipo"], "📦")
            embed = discord.Embed(
                title=f"{emoji} AQUISIÇÃO CONFIRMADA",
                description=(
                    f"*O selo do Mercado Imperial foi aposto...*\n{SEP}\n\n"
                    f"**{item['nome']}** agora pertence a {interaction.user.display_name}.\n\n"
                    f"💸 **-{item['preco']}** moedas  `•`  ⚡ **+{item['bonus_poder']}** Poder\n"
                    f"💰 Saldo restante: **{user['moedas']}** moedas\n\n{SEP}"
                ),
                color=0x006400
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        return callback

    async def _cb_anterior(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("*Esta loja foi aberta para outro comprador.*", ephemeral=True)
            return
        self.pagina -= 1
        self._atualizar_botoes()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    async def _cb_proxima(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("*Esta loja foi aberta para outro comprador.*", ephemeral=True)
            return
        self.pagina += 1
        self._atualizar_botoes()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)


class Economia:
    def __init__(self, bot):
        self.bot = bot

    def _nivel_economico(self, total: int) -> str:
        if total < 100:   return "🪨 Súdito Humilde"
        if total < 300:   return "🥉 Comerciante"
        if total < 700:   return "🥈 Mercador Imperial"
        if total < 1500:  return "🥇 Nobre Comerciante"
        if total < 5000:  return "💎 Magnata Imperial"
        return "🏆 Tycoon do Império"

    async def handle_carteira(self, message):
        user = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")
        moedas = user.get("moedas", 0)
        banco  = user.get("conta_banco", 0)
        divida = sum(e["valor_restante"] for e in user.get("emprestimos", []))
        embed = discord.Embed(
            title="💰 CÂMARA DO TESOURO",
            description=f"*Os cofres imperiais de {message.author.display_name}...*\n{SEP}",
            color=CORES_PEGADA.get(pegada, 0x2B0A3D)
        )
        embed.add_field(name="🪙 Em Mãos",        value=f"**{moedas}** moedas",                     inline=True)
        embed.add_field(name="🏦 No Banco",        value=f"**{banco}** moedas",                      inline=True)
        embed.add_field(name="💸 Dívidas",         value=f"**{divida}** moedas",                     inline=True)
        embed.add_field(name="💎 Patrimônio",      value=f"**{moedas+banco-divida}** moedas",        inline=True)
        embed.add_field(name="🎒 Itens",           value=str(len(user.get("inventario", []))),       inline=True)
        embed.add_field(name="📊 Nível Econômico", value=self._nivel_economico(moedas+banco),        inline=True)
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_loja(self, message):
        user = get_user(message.author.id)
        view  = LojaView(message.author.id, LOJA_ITEMS, "🏪 MERCADO IMPERIAL DE TENSHI", 0x8B6914)
        await message.channel.send(embed=view._build_embed(), view=view)

    async def handle_mercado_negro(self, message):
        user = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")
        pode_acessar = pegada in ("mafia", "imperial") or user.get("nivel", 1) >= 5

        if not pode_acessar:
            await message.channel.send(embed=embed_imperial(
                "🚫 Acesso Negado",
                f"*Um guardião encapuzado bloqueia sua entrada...*\n{SEP}\n\n"
                f"*\"Esse lugar não é para qualquer um. Volte quando for digno.\"*\n\n"
                f"*Requisito: Nível 5+ ou pegada Máfia/Imperial.*",
                0x1C1C1C
            ))
            return

        view  = LojaView(message.author.id, MERCADO_NEGRO_ITENS, "🖤 MERCADO NEGRO DE TENSHI", 0x1C1C1C)
        embed = view._build_embed()
        embed.description = f"*Você encontrou a entrada secreta... bem-vindo.*\n{SEP}"
        await message.channel.send(embed=embed, view=view)

    async def handle_comprar(self, message, args):
        if not args:
            await message.channel.send(embed=embed_imperial("❓", "`Tenshi, comprar [id]`\nVeja: `Tenshi, mercado` ou `Tenshi, mercado-negro`", 0x6B0000))
            return
        item_id = args[0].lower()
        todos   = LOJA_ITEMS + MERCADO_NEGRO_ITENS
        item    = next((i for i in todos if i["id"] == item_id), None)
        if not item:
            await message.channel.send(embed=embed_imperial("❌", f"Item `{item_id}` não encontrado.", 0x6B0000))
            return
        user = get_user(message.author.id)
        if item["nome"] in user.get("inventario", []):
            await message.channel.send(embed=embed_imperial("⚠️", f"Você já possui **{item['nome']}**.", 0xFF8C00))
            return
        if user["moedas"] < item["preco"]:
            await message.channel.send(embed=embed_imperial("💸", f"Faltam **{item['preco'] - user['moedas']}** moedas.", 0x6B0000))
            return
        user["moedas"] -= item["preco"]
        user["poder"]  += item["bonus_poder"]
        user.setdefault("inventario", []).append(item["nome"])
        if item["tipo"] == "titulo":
            user["titulo"] = item["nome"].replace("Título: ", "")
        save_user(message.author.id, user)
        emoji = TIPO_EMOJI.get(item["tipo"], "📦")
        embed = discord.Embed(
            title=f"{emoji} AQUISIÇÃO IMPERIAL",
            description=(
                f"*{item['nome']}* foi adquirido por {message.author.display_name}.\n{SEP}\n\n"
                f"*{item['descricao']}*\n\n"
                f"💸 **-{item['preco']}** moedas  `•`  ⚡ **+{item['bonus_poder']}** Poder\n\n{SEP}"
            ),
            color=0x006400
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_leilao(self, message, args):
        await message.channel.send(embed=embed_imperial(
            "🔨 Leilão Imperial",
            f"*O sistema de leilões está sendo preparado pelos escribas...*\n{SEP}\n\n"
            f"Em breve disponível! Por enquanto, use `Tenshi, transferir @user [valor]` para negociar.",
            0x2B0A3D
        ))

    async def handle_sorteio(self, message):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.administrator
        except: pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Apenas administradores podem iniciar sorteios.", 0x6B0000))
            return
        premio_moedas = random.randint(100, 500)
        embed = discord.Embed(
            title="🎉 SORTEIO REAL DE TENSHI",
            description=(
                f"*Os heralds imperiais anunciam um grande sorteio!*\n{SEP}\n\n"
                f"**Prêmio:** `{premio_moedas}` moedas imperiais!\n\n"
                f"*React com 🎉 nesta mensagem nos próximos 60 segundos para participar!*\n\n{SEP}"
            ),
            color=0xFFD700
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        msg = await message.channel.send(embed=embed)
        await msg.add_reaction("🎉")
        import asyncio
        await asyncio.sleep(60)
        msg = await message.channel.fetch_message(msg.id)
        participantes = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        participantes.append(user)
        if not participantes:
            await message.channel.send(embed=embed_imperial("😔 Sorteio sem participantes", "*Ninguém reagiu... O prêmio volta para os cofres imperiais.*", 0x2B0A3D))
            return
        vencedor = random.choice(participantes)
        u = get_user(vencedor.id)
        u["moedas"] += premio_moedas
        save_user(vencedor.id, u)
        await message.channel.send(embed=discord.Embed(
            title="🏆 VENCEDOR DO SORTEIO REAL",
            description=(
                f"*O destino escolheu...*\n{SEP}\n\n"
                f"**{vencedor.mention}** ganhou **{premio_moedas} moedas imperiais**!\n\n"
                f"*{len(participantes)} guerreiros participaram.*\n\n{SEP}"
            ),
            color=0xFFD700
        ).set_footer(text=RODAPE_IMPERIAL))
