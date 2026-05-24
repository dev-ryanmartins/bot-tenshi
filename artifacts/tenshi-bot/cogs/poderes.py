import discord
import random
from database import get_user, save_user
from utils import embed_imperial, SEP, RODAPE_IMPERIAL, CORES_PEGADA

# ─────────────────────────────────────────────────────────────────────────────
# TODOS OS PODERES DE RP
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIAS_PODER = {
    "arcano": {
        "nome": "Poderes Arcanos",
        "emoji": "🔮",
        "cor": 0x4B0082,
        "poderes": [
            {"nome": "Telepatia",           "emoji": "🧠", "desc": "Lê e projeta pensamentos. Útil em negociações e espionagem.", "raridade": "raro",    "bonus_poder": 30},
            {"nome": "Telecinese",          "emoji": "🌀", "desc": "Move objetos com a mente. Pode ser usado em combate ou fuga.", "raridade": "raro",    "bonus_poder": 25},
            {"nome": "Visão do Além",       "emoji": "👁️", "desc": "Vê verdades ocultas, auras e portais dimensionais.",          "raridade": "épico",   "bonus_poder": 40},
            {"nome": "Invocação",           "emoji": "⚡", "desc": "Invoca entidades ou energia do éter para auxiliar.",            "raridade": "lendário","bonus_poder": 60},
            {"nome": "Transmutação",        "emoji": "🔄", "desc": "Transforma matéria. Pode converter materiais e curar.",        "raridade": "épico",   "bonus_poder": 50},
            {"nome": "Fissura Temporal",    "emoji": "⏳", "desc": "Desacelera o tempo ao redor por breves momentos.",             "raridade": "lendário","bonus_poder": 80},
            {"nome": "Escudo Arcano",       "emoji": "🛡️", "desc": "Cria barreiras de energia que absorvem impacto mágico.",      "raridade": "incomum", "bonus_poder": 20},
        ],
    },
    "sombra": {
        "nome": "Poderes das Sombras",
        "emoji": "🌑",
        "cor": 0x1C1C1C,
        "poderes": [
            {"nome": "Passo Fantasma",      "emoji": "👻", "desc": "Atravessa paredes e obstáculos por curtos períodos.",          "raridade": "épico",   "bonus_poder": 45},
            {"nome": "Manipulação das Sombras","emoji":"🖤","desc": "Controla trevas para criar formas, capturar ou desorientar.", "raridade": "raro",    "bonus_poder": 35},
            {"nome": "Invisibilidade",      "emoji": "🫥", "desc": "Torna-se imperceptível para sentidos normais.",               "raridade": "raro",    "bonus_poder": 30},
            {"nome": "Drenagem de Alma",    "emoji": "💀", "desc": "Suga energia vital de adversários fracos de vontade.",        "raridade": "lendário","bonus_poder": 70},
            {"nome": "Portal das Sombras",  "emoji": "🌀", "desc": "Abre portais entre locais escuros no mapa do Império.",       "raridade": "lendário","bonus_poder": 75},
            {"nome": "Névoa Mortal",        "emoji": "🌫️", "desc": "Envolve a área em névoa que desorienta inimigos.",           "raridade": "incomum", "bonus_poder": 18},
        ],
    },
    "elemental": {
        "nome": "Poderes Elementais",
        "emoji": "🌪️",
        "cor": 0x00CED1,
        "poderes": [
            {"nome": "Controle do Fogo",    "emoji": "🔥", "desc": "Manipula e gera chamas. Ataque e defesa com fogo imperial.",  "raridade": "raro",    "bonus_poder": 35},
            {"nome": "Controle da Água",    "emoji": "🌊", "desc": "Controla fluxo de água — cura aliados ou afoga inimigos.",   "raridade": "raro",    "bonus_poder": 30},
            {"nome": "Controle da Terra",   "emoji": "🌍", "desc": "Move pedras, cria muralhas, abre fissuras no chão.",          "raridade": "raro",    "bonus_poder": 32},
            {"nome": "Controle do Ar",      "emoji": "💨", "desc": "Manipula ventos — velocidade, voo curto, cortes de ar.",     "raridade": "raro",    "bonus_poder": 28},
            {"nome": "Raio Imperial",       "emoji": "⚡", "desc": "Projeta raios de energia devastadora em linha reta.",          "raridade": "épico",   "bonus_poder": 55},
            {"nome": "Fusão Elemental",     "emoji": "🌈", "desc": "Combina dois elementos simultaneamente para ataques únicos.", "raridade": "lendário","bonus_poder": 85},
            {"nome": "Terremoto",           "emoji": "💥", "desc": "Provoca tremores localizados. Uso em batalhas em massa.",     "raridade": "épico",   "bonus_poder": 50},
        ],
    },
    "corpo": {
        "nome": "Poderes Físicos Aprimorados",
        "emoji": "💪",
        "cor": 0x8B0000,
        "poderes": [
            {"nome": "Velocidade Sobre-humana","emoji":"⚡","desc": "Move-se mais rápido que olhos comuns conseguem seguir.",     "raridade": "raro",    "bonus_poder": 30},
            {"nome": "Força Colossal",      "emoji": "💪", "desc": "Força física amplificada dezenas de vezes.",                  "raridade": "raro",    "bonus_poder": 35},
            {"nome": "Regeneração",         "emoji": "💚", "desc": "Recupera ferimentos físicos em minutos ou horas.",            "raridade": "épico",   "bonus_poder": 40},
            {"nome": "Pele de Aço",         "emoji": "🛡️", "desc": "Pele endurecida que resiste a impactos normais.",           "raridade": "incomum", "bonus_poder": 22},
            {"nome": "Adrenalina Extrema",  "emoji": "🔥", "desc": "Libera surto de potência em momentos críticos.",             "raridade": "incomum", "bonus_poder": 15},
            {"nome": "Corpo Espectral",     "emoji": "✨", "desc": "O corpo torna-se parcialmente imaterial brevemente.",         "raridade": "épico",   "bonus_poder": 45},
        ],
    },
    "divino": {
        "nome": "Poderes Divinos",
        "emoji": "👑",
        "cor": 0xFFD700,
        "poderes": [
            {"nome": "Cura Divina",         "emoji": "✨", "desc": "Cura ferimentos graves em si ou em aliados.",                "raridade": "raro",    "bonus_poder": 25},
            {"nome": "Bênção Imperial",     "emoji": "⚜️", "desc": "Bênção que amplia todos os atributos temporariamente.",     "raridade": "épico",   "bonus_poder": 55},
            {"nome": "Maldição Ancestral",  "emoji": "💀", "desc": "Lança uma maldição que debilita gradualmente o alvo.",      "raridade": "épico",   "bonus_poder": 50},
            {"nome": "Ressurreição",        "emoji": "🌟", "desc": "Pode trazer de volta aliados caídos (uso único por batalha)","raridade": "lendário","bonus_poder": 100},
            {"nome": "Decreto Divino",      "emoji": "📜", "desc": "Uma palavra que force entidades menores a obedecer.",       "raridade": "lendário","bonus_poder": 90},
            {"nome": "Aura Imperial",       "emoji": "🌠", "desc": "Projeta autoridade — inimigos hesitam em atacar.",          "raridade": "raro",    "bonus_poder": 20},
        ],
    },
}

COR_RARIDADE = {
    "comum":    ("⚪", 0x808080),
    "incomum":  ("🟢", 0x228B22),
    "raro":     ("🔵", 0x0047AB),
    "épico":    ("🟣", 0x4B0082),
    "lendário": ("🟡", 0xFFD700),
}


class SelectPoder(discord.ui.Select):
    def __init__(self, categoria_key: str, user_id: int):
        self.categoria_key = categoria_key
        self.user_id_ref   = user_id
        cat     = CATEGORIAS_PODER[categoria_key]
        poderes = cat["poderes"]
        opcoes  = [
            discord.SelectOption(
                label=f"{p['emoji']} {p['nome']} ({p['raridade']})",
                value=p["nome"],
                description=p["desc"][:100],
                emoji=p["emoji"],
            )
            for p in poderes
        ]
        super().__init__(placeholder=f"⚡ Escolha um poder de {cat['nome']}...", options=opcoes)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id_ref:
            await interaction.response.send_message("*Este menu não é seu.*", ephemeral=True)
            return
        cat    = CATEGORIAS_PODER[self.categoria_key]
        poder_nome = self.values[0]
        poder_info = next((p for p in cat["poderes"] if p["nome"] == poder_nome), None)
        if not poder_info:
            return

        user = get_user(interaction.user.id)
        poderes_atuais = user.get("poderes", [])

        if poder_nome in poderes_atuais:
            await interaction.response.send_message(
                embed=embed_imperial("⚠️ Já Possui", f"Você já possui o poder **{poder_nome}**.", 0xFF8C00),
                ephemeral=True
            )
            return

        # Custo em XP para aprender
        custo_xp = {"incomum": 50, "raro": 120, "épico": 300, "lendário": 600}.get(poder_info["raridade"], 50)
        if user["xp"] < custo_xp:
            await interaction.response.send_message(
                embed=embed_imperial("❌ XP Insuficiente", f"**{poder_nome}** requer **{custo_xp} XP**. Você tem **{user['xp']}**.", 0x6B0000),
                ephemeral=True
            )
            return

        user["xp"]    -= custo_xp
        user["poder"] += poder_info["bonus_poder"]
        poderes_atuais.append(poder_nome)
        user["poderes"] = poderes_atuais
        user.setdefault("habilidades", []).append(poder_nome)
        save_user(interaction.user.id, user)

        cor_emoji, cor_hex = COR_RARIDADE.get(poder_info["raridade"], ("⚪", 0x2B0A3D))
        embed = discord.Embed(
            title=f"{poder_info['emoji']} PODER APRENDIDO — {poder_nome.upper()}",
            description=(
                f"*A energia flui pelo corpo de {interaction.user.display_name}...*\n{SEP}\n\n"
                f"*{poder_info['desc']}*\n\n{SEP}"
            ),
            color=cor_hex
        )
        embed.add_field(name="⚡ Bônus de Poder", value=f"+{poder_info['bonus_poder']}", inline=True)
        embed.add_field(name=f"{cor_emoji} Raridade", value=poder_info["raridade"].capitalize(), inline=True)
        embed.add_field(name="💸 Custo pago", value=f"{custo_xp} XP", inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await interaction.response.send_message(embed=embed, ephemeral=False)


class SelectCategoriaPoder(discord.ui.Select):
    def __init__(self, user_id: int):
        self.user_id_ref = user_id
        opcoes = [
            discord.SelectOption(
                label=f"{cat['emoji']} {cat['nome']}",
                value=key,
                description=f"{len(cat['poderes'])} poderes disponíveis",
                emoji=cat["emoji"]
            )
            for key, cat in CATEGORIAS_PODER.items()
        ]
        super().__init__(placeholder="🌟 Escolha uma categoria de poderes...", options=opcoes)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id_ref:
            await interaction.response.send_message("*Este menu não é seu.*", ephemeral=True)
            return
        cat_key = self.values[0]
        cat     = CATEGORIAS_PODER[cat_key]
        user    = get_user(interaction.user.id)
        poderes_atuais = set(user.get("poderes", []))

        embed = discord.Embed(
            title=f"{cat['emoji']} {cat['nome'].upper()}",
            description=f"*Escolha um poder para aprender:*\n{SEP}",
            color=cat["cor"]
        )
        for p in cat["poderes"]:
            cor_emoji, _ = COR_RARIDADE.get(p["raridade"], ("⚪", 0))
            custo = {"incomum": 50, "raro": 120, "épico": 300, "lendário": 600}.get(p["raridade"], 50)
            status = "✅ **Adquirido**" if p["nome"] in poderes_atuais else f"💸 {custo} XP"
            embed.add_field(
                name=f"{p['emoji']} {p['nome']} {cor_emoji}",
                value=f"*{p['desc']}*\n+{p['bonus_poder']} Poder `•` {status}",
                inline=False
            )
        embed.set_footer(text=RODAPE_IMPERIAL)

        new_view = discord.ui.View(timeout=120)
        new_view.add_item(SelectPoder(cat_key, self.user_id_ref))
        back_btn = discord.ui.Button(label="◀ Voltar às Categorias", style=discord.ButtonStyle.secondary)
        async def back_cb(inter):
            if inter.user.id != self.user_id_ref:
                await inter.response.send_message("*Este menu não é seu.*", ephemeral=True)
                return
            view2 = PoderesView(self.user_id_ref)
            await inter.response.edit_message(embed=_embed_poderes_intro(inter.user), view=view2)
        back_btn.callback = back_cb
        new_view.add_item(back_btn)
        await interaction.response.edit_message(embed=embed, view=new_view)


class PoderesView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.add_item(SelectCategoriaPoder(user_id))


def _embed_poderes_intro(member) -> discord.Embed:
    user = get_user(member.id)
    poderes_atuais = user.get("poderes", [])
    embed = discord.Embed(
        title="⚡ ÁRVORE DE PODERES DE TENSHI",
        description=(
            f"*Cada guerreiro carrega dentro de si um potencial inexplorado...*\n{SEP}\n\n"
            f"Escolha uma **categoria** e gaste **XP** para aprender poderes.\n\n"
            f"**Seus poderes:** {', '.join(poderes_atuais) if poderes_atuais else '*Nenhum ainda*'}\n"
            f"**Seu XP disponível:** **{user.get('xp', 0)}**\n\n{SEP}"
        ),
        color=0x2B0A3D
    )
    for key, cat in CATEGORIAS_PODER.items():
        embed.add_field(
            name=f"{cat['emoji']} {cat['nome']}",
            value=f"{len(cat['poderes'])} poderes `•` do Incomum ao Lendário",
            inline=True
        )
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


class Poderes:
    def __init__(self, bot):
        self.bot = bot

    async def handle_poderes(self, message):
        embed = _embed_poderes_intro(message.author)
        view  = PoderesView(message.author.id)
        await message.channel.send(embed=embed, view=view)

    async def handle_meus_poderes(self, message):
        user = get_user(message.author.id)
        poderes = user.get("poderes", [])
        pegada  = user.get("pegada", "imperial")
        embed = discord.Embed(
            title="⚡ PODERES APRENDIDOS",
            description=f"*Arsenal de {message.author.display_name}...*\n{SEP}",
            color=CORES_PEGADA.get(pegada, 0x2B0A3D)
        )
        if not poderes:
            embed.add_field(name="📭 Nenhum poder", value="*Use `Tenshi, poderes` para aprender poderes.*", inline=False)
        else:
            for poder_nome in poderes:
                # Encontrar info do poder
                info = None
                for cat in CATEGORIAS_PODER.values():
                    info = next((p for p in cat["poderes"] if p["nome"] == poder_nome), None)
                    if info:
                        break
                if info:
                    cor_emoji, _ = COR_RARIDADE.get(info["raridade"], ("⚪", 0))
                    embed.add_field(
                        name=f"{info['emoji']} {info['nome']} {cor_emoji}",
                        value=f"*{info['desc']}*",
                        inline=True
                    )
                else:
                    embed.add_field(name=f"⚡ {poder_nome}", value="\u200b", inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)
