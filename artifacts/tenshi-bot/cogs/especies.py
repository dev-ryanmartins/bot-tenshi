import discord
import asyncio
from database import get_user, save_user
from utils import embed_imperial, IMPERADOR_ID, SEP, RODAPE_IMPERIAL, CORES_PEGADA

# ─────────────────────────────────────────────────────────────────────────────
# ESPÉCIES
# ─────────────────────────────────────────────────────────────────────────────
ESPECIES = {
    "tenshin": {
        "nome": "Tenshin",
        "emoji": "⚜️",
        "cor": 0xFFD700,
        "descricao": (
            "Filhos legítimos do Império. Nascidos sob a luz do Trono, carregam o sangue do primeiro Imperador. "
            "São líderes natos, guerreiros honrados e portadores da chama imperial imortal."
        ),
        "passiva": "Herança Imperial",
        "passiva_desc": "Bônus de 10% em XP de treinos e missões dentro da Cidadela. Diplomacia sempre favorável.",
        "atributos": {"vida": 150, "mana": 80, "forca": 120, "agilidade": 80},
        "bonus_poder": 30,
    },
    "phantasma": {
        "nome": "Sombra Phantasma",
        "emoji": "🌑",
        "cor": 0x1C1C1C,
        "descricao": (
            "Seres nascidos nas fronteiras entre o mundo dos vivos e das sombras. Invisíveis para olhos comuns, "
            "sua existência é um segredo que o Império teme — e usa."
        ),
        "passiva": "Passo Etéreo",
        "passiva_desc": "Custo de viagem reduzido. +20% dano em duelos PvP. Invisível para invasões automaticamente.",
        "atributos": {"vida": 90, "mana": 130, "forca": 80, "agilidade": 150},
        "bonus_poder": 25,
    },
    "forjado": {
        "nome": "Forjado em Runas",
        "emoji": "🔮",
        "cor": 0x4B0082,
        "descricao": (
            "Construídos pela Ordem Esotérica no auge do poder arcano. Não nascidos — forjados. "
            "Cada runa em seu corpo é uma lei do universo gravada em carne e energia."
        ),
        "passiva": "Absorção Rúnica",
        "passiva_desc": "Tarot e Runas concedem bônus 50% maiores. Missões esotéricas dão XP dobrado.",
        "atributos": {"vida": 100, "mana": 170, "forca": 90, "agilidade": 90},
        "bonus_poder": 20,
    },
    "desperto": {
        "nome": "Plebeu Desperto",
        "emoji": "👁️",
        "cor": 0x2E8B57,
        "descricao": (
            "Humanos comuns que tocaram algo além do ordinário — seja por acidente, trauma ou destino. "
            "Sua força não vem de sangue ou magia: vem de uma vontade inquebrantável."
        ),
        "passiva": "Versatilidade Ilimitada",
        "passiva_desc": "Pode aprender habilidades de qualquer espécie. +15% em todas as recompensas.",
        "atributos": {"vida": 110, "mana": 110, "forca": 110, "agilidade": 110},
        "bonus_poder": 15,
    },
    "draconiano": {
        "nome": "Draconiano",
        "emoji": "🐉",
        "cor": 0x8B0000,
        "descricao": (
            "Descendentes dos Dragões Ancestrais que dominaram Tenshi antes do primeiro Imperador. "
            "Portam escamas invisíveis, resistência sobre-humana e um rugido que move montanhas."
        ),
        "passiva": "Sangue de Dragão",
        "passiva_desc": "Imune a penalidades de localização. +30% poder em invasões. Regeneração natural de HP.",
        "atributos": {"vida": 200, "mana": 60, "forca": 160, "agilidade": 60},
        "bonus_poder": 40,
    },
    "voidwalker": {
        "nome": "Voidwalker",
        "emoji": "🌌",
        "cor": 0x0D0D2B,
        "descricao": (
            "Viajantes que cruzaram o Vazio entre dimensões e retornaram... transformados. "
            "Seu corpo existe parcialmente em outro plano — incompreendidos, temidos, poderosos."
        ),
        "passiva": "Fissura Dimensional",
        "passiva_desc": "Pode usar habilidades do Subterrâneo de qualquer localização. Custo de skills reduzido.",
        "atributos": {"vida": 80, "mana": 160, "forca": 80, "agilidade": 130},
        "bonus_poder": 35,
    },
    "nobre_corrompido": {
        "nome": "Nobre Corrompido",
        "emoji": "💀",
        "cor": 0x2F2F2F,
        "descricao": (
            "Antigos nobres de Tenshi que venderam parte de sua alma por poder eterno. "
            "Vivem na fronteira entre os vivos e os mortos — sua influência política permanece intacta, mas o preço foi alto."
        ),
        "passiva": "Pacto das Sombras",
        "passiva_desc": "Acesso automático ao Mercado Negro. Missões políticas e da máfia rendem 25% mais moedas.",
        "atributos": {"vida": 120, "mana": 120, "forca": 100, "agilidade": 100},
        "bonus_poder": 28,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# LOCALIZAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
LOCALIZACOES = {
    "cidadela": {
        "nome": "Cidadela Imperial",
        "emoji": "🏛️",
        "cor": 0xFFD700,
        "descricao": "O coração político e militar de Tenshi. O Trono fica aqui — segurança máxima, glória máxima.",
        "bonus_treino_xp": 1.15,
        "bonus_missao_moedas": 1.0,
        "bonus_meditacao_xp": 1.0,
        "risco_invasao": False,
        "acesso_mercado_negro": False,
        "custo_viagem": 0,
    },
    "subterraneo": {
        "nome": "Subterrâneo",
        "emoji": "🌑",
        "cor": 0x1C1C1C,
        "descricao": "Os labirintos sob a Cidadela, onde a lei não chega. Domínio da Máfia e dos mistérios proibidos.",
        "bonus_treino_xp": 0.90,
        "bonus_missao_moedas": 1.30,
        "bonus_meditacao_xp": 1.20,
        "risco_invasao": False,
        "acesso_mercado_negro": True,
        "custo_viagem": 30,
    },
    "fronteiras": {
        "nome": "Fronteiras do Norte",
        "emoji": "⚔️",
        "cor": 0x8B0000,
        "descricao": "Terra de guerra constante. Perigo e glória a cada passo — aqui os guerreiros verdadeiros nascem.",
        "bonus_treino_xp": 1.30,
        "bonus_missao_moedas": 1.20,
        "bonus_meditacao_xp": 0.80,
        "risco_invasao": True,
        "acesso_mercado_negro": False,
        "custo_viagem": 20,
    },
    "santuario": {
        "nome": "Santuário Ancestral",
        "emoji": "🌿",
        "cor": 0x2E8B57,
        "descricao": "Floresta sagrada dos Forjados em Runas. Energias místicas pulsam em cada pedra e árvore.",
        "bonus_treino_xp": 1.0,
        "bonus_missao_moedas": 1.0,
        "bonus_meditacao_xp": 1.50,
        "risco_invasao": False,
        "acesso_mercado_negro": False,
        "custo_viagem": 25,
    },
    "porto_sombras": {
        "nome": "Porto das Sombras",
        "emoji": "⚓",
        "cor": 0x00008B,
        "descricao": "Cidade portuária onde contrabandistas, mercadores e piratas se encontram. Comércio sem lei.",
        "bonus_treino_xp": 0.95,
        "bonus_missao_moedas": 1.40,
        "bonus_meditacao_xp": 0.90,
        "risco_invasao": False,
        "acesso_mercado_negro": True,
        "custo_viagem": 35,
    },
    "torre_arcana": {
        "nome": "Torre Arcana de Runas",
        "emoji": "🗼",
        "cor": 0x4B0082,
        "descricao": "A sede da Ordem Esotérica. Apenas iniciados chegam até aqui — e alguns não voltam do mesmo jeito.",
        "bonus_treino_xp": 1.10,
        "bonus_missao_moedas": 0.90,
        "bonus_meditacao_xp": 1.80,
        "risco_invasao": False,
        "acesso_mercado_negro": False,
        "custo_viagem": 40,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# View de criação de ficha — Dropdown de Espécie
# ─────────────────────────────────────────────────────────────────────────────
class SelectEspecie(discord.ui.Select):
    def __init__(self):
        opcoes = [
            discord.SelectOption(
                label=f"{info['emoji']} {info['nome']}",
                value=key,
                description=info["descricao"][:100],
                emoji=info["emoji"],
            )
            for key, info in ESPECIES.items()
        ]
        super().__init__(
            placeholder="⚜️ Escolha sua Espécie...",
            min_values=1,
            max_values=1,
            options=opcoes,
        )

    async def callback(self, interaction: discord.Interaction):
        view: FichaView = self.view
        if interaction.user.id != view.user_id:
            await interaction.response.send_message("*Este pergaminho não é seu.*", ephemeral=True)
            return
        especie_key = self.values[0]
        especie     = ESPECIES[especie_key]
        view.especie_escolhida = especie_key
        view.clear_items()
        view.add_item(SelectRaca())
        await interaction.response.edit_message(
            embed=_embed_preview_especie(especie, interaction.user),
            view=view
        )


class SelectRaca(discord.ui.Select):
    """Segundo dropdown — confirmar ou escolher outra espécie"""
    def __init__(self):
        super().__init__(
            placeholder="✅ Confirmar esta espécie ou escolher outra...",
            min_values=1, max_values=1,
            options=[
                discord.SelectOption(label="✅ Confirmar esta espécie", value="confirmar", emoji="✅"),
                discord.SelectOption(label="🔄 Escolher outra espécie", value="voltar",    emoji="🔄"),
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        view: FichaView = self.view
        if interaction.user.id != view.user_id:
            await interaction.response.send_message("*Este pergaminho não é seu.*", ephemeral=True)
            return
        if self.values[0] == "voltar":
            view.especie_escolhida = None
            view.clear_items()
            view.add_item(SelectEspecie())
            await interaction.response.edit_message(
                embed=_embed_intro_criacao(interaction.user),
                view=view
            )
            return
        # Confirmar — envia para #fichas-para-avaliar
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="📜 FICHA ENVIADA PARA AVALIAÇÃO",
                description=(
                    f"*Os Escribas imperiais receberam sua ficha...*\n{SEP}\n\n"
                    f"Sua ficha foi enviada para o canal **#fichas-para-avaliar**.\n"
                    f"Aguarde a aprovação da **Staff Imperial** ou do **Imperador Alloy**.\n\n"
                    f"*Você será notificado quando sua ficha for avaliada.*\n\n{SEP}"
                ),
                color=0x006400
            ),
            view=discord.ui.View()
        )
        await _enviar_para_avaliar(interaction, view)


def _embed_intro_criacao(member: discord.Member | discord.User) -> discord.Embed:
    embed = discord.Embed(
        title="📜 CRIAÇÃO DE PERSONAGEM — IMPÉRIO DE TENSHI",
        description=(
            f"*Bem-vindo ao rito de criação, {member.display_name}...*\n{SEP}\n\n"
            "Este é o momento em que sua identidade no Império é forjada para sempre.\n\n"
            "**Escolha sua Espécie** — ela determina seus atributos base e sua habilidade passiva.\n\n"
            f"{SEP}\n*Cada escolha é permanente. Reflita bem.*"
        ),
        color=0x2B0A3D
    )
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


def _embed_preview_especie(especie: dict, member: discord.Member | discord.User) -> discord.Embed:
    atribs = especie["atributos"]
    embed = discord.Embed(
        title=f"{especie['emoji']} {especie['nome'].upper()} — PRÉ-VISUALIZAÇÃO",
        description=f"*{especie['descricao']}*\n\n{SEP}",
        color=especie["cor"]
    )
    embed.add_field(
        name="📊 Atributos Base",
        value=(
            f"❤️ **Vida:** {atribs['vida']}\n"
            f"💙 **Mana:** {atribs['mana']}\n"
            f"💪 **Força:** {atribs['forca']}\n"
            f"🌪️ **Agilidade:** {atribs['agilidade']}"
        ),
        inline=True
    )
    embed.add_field(
        name="⚡ Habilidade Passiva",
        value=f"**{especie['passiva']}**\n*{especie['passiva_desc']}*",
        inline=True
    )
    embed.add_field(name="💥 Bônus de Poder", value=f"+{especie['bonus_poder']} Poder inicial", inline=False)
    embed.set_footer(text=f"Confirme abaixo ou escolha outra espécie  •  {RODAPE_IMPERIAL}")
    return embed


async def _enviar_para_avaliar(interaction: discord.Interaction, view: "FichaView"):
    especie    = ESPECIES[view.especie_escolhida]
    member     = interaction.user
    guild      = interaction.guild

    # Encontrar #fichas-para-avaliar
    canal_fichas = discord.utils.get(guild.text_channels, name="fichas-para-avaliar")
    if not canal_fichas:
        # Tentar criar
        try:
            canal_fichas = await guild.create_text_channel("fichas-para-avaliar")
        except Exception:
            return

    atribs = especie["atributos"]
    embed = discord.Embed(
        title=f"📋 FICHA PARA AVALIAÇÃO — {member.display_name.upper()}",
        description=f"*Um novo personagem aguarda aprovação da Staff Imperial...*\n{SEP}",
        color=especie["cor"]
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="👤 Jogador",           value=member.mention,          inline=True)
    embed.add_field(name=f"{especie['emoji']} Espécie", value=especie["nome"],  inline=True)
    embed.add_field(name="🆔 ID",                value=str(member.id),          inline=True)
    embed.add_field(
        name="📊 Atributos",
        value=(
            f"❤️ Vida: **{atribs['vida']}**  •  "
            f"💙 Mana: **{atribs['mana']}**\n"
            f"💪 Força: **{atribs['forca']}**  •  "
            f"🌪️ Agilidade: **{atribs['agilidade']}**"
        ),
        inline=False
    )
    embed.add_field(name="⚡ Passiva", value=f"**{especie['passiva']}** — *{especie['passiva_desc']}*", inline=False)
    embed.add_field(name="💥 Bônus Poder", value=f"+{especie['bonus_poder']}", inline=True)
    embed.set_footer(text=f"Aguardando avaliação da Staff  •  {RODAPE_IMPERIAL}")

    avaliar_view = AvaliacaoView(member.id, view.especie_escolhida, guild)
    await canal_fichas.send(embed=embed, view=avaliar_view)


# ─────────────────────────────────────────────────────────────────────────────
# View de avaliação (staff)
# ─────────────────────────────────────────────────────────────────────────────
class AvaliacaoView(discord.ui.View):
    def __init__(self, jogador_id: int, especie_key: str, guild: discord.Guild):
        super().__init__(timeout=None)
        self.jogador_id  = jogador_id
        self.especie_key = especie_key
        self.guild       = guild
        self.avaliado    = False

    def _is_staff(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == IMPERADOR_ID:
            return True
        try:
            return (
                interaction.user.guild_permissions.manage_roles or
                interaction.user.guild_permissions.administrator
            )
        except Exception:
            return False

    @discord.ui.button(label="✅ Aprovar Ficha", style=discord.ButtonStyle.success, emoji="⚜️")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_staff(interaction):
            await interaction.response.send_message("*Apenas a Staff Imperial pode avaliar fichas.*", ephemeral=True)
            return
        if self.avaliado:
            await interaction.response.send_message("*Esta ficha já foi avaliada.*", ephemeral=True)
            return
        self.avaliado = True
        self.clear_items()

        especie = ESPECIES[self.especie_key]
        user_db = get_user(self.jogador_id)
        atribs  = especie["atributos"]

        user_db["especie"]    = self.especie_key
        user_db["atributos"]  = dict(atribs)
        user_db["poder"]      = user_db.get("poder", 100) + especie["bonus_poder"]
        user_db["local_atual"] = "cidadela"
        user_db.setdefault("ficha", {})["especie"]   = especie["nome"]
        user_db.setdefault("ficha", {})["passiva"]   = especie["passiva"]
        user_db["ficha_aprovada"] = True
        save_user(self.jogador_id, user_db)

        # Dar cargo inicial
        try:
            membro = await self.guild.fetch_member(self.jogador_id)
            cargo  = discord.utils.get(self.guild.roles, name="Aventureiro")
            if not cargo:
                cargo = await self.guild.create_role(name="Aventureiro", color=discord.Color.gold())
            await membro.add_roles(cargo)
            try:
                await membro.send(embed=discord.Embed(
                    title="⚜️ FICHA APROVADA!",
                    description=(
                        f"*Os Escribas do Império gravaram seu nome nos Pergaminhos Eternos...*\n{SEP}\n\n"
                        f"Sua ficha como **{especie['emoji']} {especie['nome']}** foi aprovada!\n\n"
                        f"Você recebeu o cargo **Aventureiro** e pode começar sua jornada.\n\n"
                        f"Use `Tenshi, status` para ver seu perfil completo.\n\n{SEP}"
                    ),
                    color=0xFFD700
                ).set_footer(text=RODAPE_IMPERIAL))
            except Exception:
                pass
        except Exception:
            pass

        embed_resultado = discord.Embed(
            title="✅ FICHA APROVADA",
            description=(
                f"*A ficha foi aprovada por {interaction.user.display_name}.*\n\n"
                f"**Jogador:** <@{self.jogador_id}>\n"
                f"**Espécie:** {especie['emoji']} {especie['nome']}\n"
                f"**Cargo concedido:** Aventureiro"
            ),
            color=0x006400
        )
        embed_resultado.set_footer(text=RODAPE_IMPERIAL)
        await interaction.response.edit_message(embed=embed_resultado, view=self)

    @discord.ui.button(label="❌ Reprovar Ficha", style=discord.ButtonStyle.danger, emoji="🚫")
    async def reprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_staff(interaction):
            await interaction.response.send_message("*Apenas a Staff Imperial pode avaliar fichas.*", ephemeral=True)
            return
        if self.avaliado:
            await interaction.response.send_message("*Esta ficha já foi avaliada.*", ephemeral=True)
            return
        self.avaliado = True
        self.clear_items()

        try:
            membro = await self.guild.fetch_member(self.jogador_id)
            try:
                await membro.send(embed=discord.Embed(
                    title="❌ Ficha Reprovada",
                    description=(
                        f"*Sua ficha não passou pela avaliação da Staff Imperial.*\n\n"
                        f"Você pode tentar novamente com `Tenshi, criar-ficha`.\n"
                        f"Se tiver dúvidas, entre em contato com um administrador."
                    ),
                    color=0x8B0000
                ).set_footer(text=RODAPE_IMPERIAL))
            except Exception:
                pass
        except Exception:
            pass

        embed_resultado = discord.Embed(
            title="❌ FICHA REPROVADA",
            description=(
                f"*A ficha foi reprovada por {interaction.user.display_name}.*\n\n"
                f"**Jogador:** <@{self.jogador_id}>\n"
                f"*O jogador foi notificado e pode tentar novamente.*"
            ),
            color=0x8B0000
        )
        embed_resultado.set_footer(text=RODAPE_IMPERIAL)
        await interaction.response.edit_message(embed=embed_resultado, view=self)


class FichaView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id          = user_id
        self.especie_escolhida = None
        self.add_item(SelectEspecie())


# ─────────────────────────────────────────────────────────────────────────────
# View de seleção de localização
# ─────────────────────────────────────────────────────────────────────────────
class SelectLocalView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.add_item(SelectLocalDropdown())


class SelectLocalDropdown(discord.ui.Select):
    def __init__(self):
        opcoes = [
            discord.SelectOption(
                label=f"{loc['emoji']} {loc['nome']}",
                value=key,
                description=loc["descricao"][:100],
                emoji=loc["emoji"],
            )
            for key, loc in LOCALIZACOES.items()
        ]
        super().__init__(placeholder="📍 Para onde viajar?", options=opcoes)

    async def callback(self, interaction: discord.Interaction):
        view: SelectLocalView = self.view
        if interaction.user.id != view.user_id:
            await interaction.response.send_message("*Esta rota não é sua.*", ephemeral=True)
            return

        destino_key = self.values[0]
        destino     = LOCALIZACOES[destino_key]
        user        = get_user(interaction.user.id)
        local_atual = user.get("local_atual", "cidadela")

        if destino_key == local_atual:
            await interaction.response.send_message(
                f"*Você já está na {destino['nome']}...*", ephemeral=True
            )
            return

        custo = destino["custo_viagem"]
        if user["moedas"] < custo and custo > 0:
            await interaction.response.send_message(
                embed=embed_imperial("💸 Moedas Insuficientes", f"A viagem custa **{custo}** moedas.", 0x6B0000),
                ephemeral=True
            )
            return

        if custo > 0:
            user["moedas"] -= custo
        user["local_atual"] = destino_key
        save_user(interaction.user.id, user)

        bonus_lines = []
        if destino["bonus_treino_xp"] > 1:
            bonus_lines.append(f"⚡ +{int((destino['bonus_treino_xp']-1)*100)}% XP em treinos")
        if destino["bonus_missao_moedas"] > 1:
            bonus_lines.append(f"💰 +{int((destino['bonus_missao_moedas']-1)*100)}% moedas em missões")
        if destino["bonus_meditacao_xp"] > 1:
            bonus_lines.append(f"🧘 +{int((destino['bonus_meditacao_xp']-1)*100)}% XP em meditação")
        if destino["acesso_mercado_negro"]:
            bonus_lines.append("🖤 Acesso ao Mercado Negro desbloqueado")
        if destino["risco_invasao"]:
            bonus_lines.append("⚠️ Risco de invasões aumentado")

        embed = discord.Embed(
            title=f"🗺️ VIAGEM — {destino['emoji']} {destino['nome']}",
            description=(
                f"*{interaction.user.display_name} parte em jornada...*\n{SEP}\n\n"
                f"*{destino['descricao']}*\n\n{SEP}"
            ),
            color=destino["cor"]
        )
        if custo > 0:
            embed.add_field(name="💸 Custo de Viagem", value=f"**{custo}** moedas", inline=True)
        if bonus_lines:
            embed.add_field(name="🌟 Bônus desta Área", value="\n".join(bonus_lines), inline=False)
        embed.set_footer(text=RODAPE_IMPERIAL)
        view.clear_items()
        await interaction.response.edit_message(embed=embed, view=view)


# ─────────────────────────────────────────────────────────────────────────────
# Cog principal
# ─────────────────────────────────────────────────────────────────────────────
class Especies:
    def __init__(self, bot):
        self.bot = bot

    async def handle_criar_ficha(self, message):
        user = get_user(message.author.id)
        if user.get("ficha_aprovada"):
            await message.channel.send(embed=embed_imperial(
                "⚠️ Ficha Já Aprovada",
                f"*Você já possui uma ficha aprovada como **{ESPECIES.get(user.get('especie',{}), {}).get('nome', 'espécie registrada')}**.*\n\n"
                f"Use `Tenshi, status` para ver seu perfil completo.",
                0xFF8C00
            ))
            return
        if user.get("especie") and not user.get("ficha_aprovada"):
            await message.channel.send(embed=embed_imperial(
                "⏳ Ficha Aguardando Aprovação",
                "*Sua ficha já foi enviada e está sendo avaliada pela Staff Imperial.*\n\nAguarde!",
                0xFF8C00
            ))
            return

        embed = _embed_intro_criacao(message.author)
        view  = FichaView(message.author.id)
        await message.channel.send(embed=embed, view=view)

    async def handle_viajar(self, message):
        user = get_user(message.author.id)
        local_atual = user.get("local_atual", "cidadela")
        loc_info    = LOCALIZACOES.get(local_atual, LOCALIZACOES["cidadela"])

        embed = discord.Embed(
            title="🗺️ MAPA DO IMPÉRIO DE TENSHI",
            description=(
                f"*Você está em: {loc_info['emoji']} **{loc_info['nome']}***\n{SEP}\n\n"
                f"Escolha seu próximo destino no menu abaixo:"
            ),
            color=0x2B0A3D
        )
        for key, loc in LOCALIZACOES.items():
            ativo = "📍 **AQUI**" if key == local_atual else f"{loc['custo_viagem']} moedas" if loc["custo_viagem"] > 0 else "Grátis"
            embed.add_field(
                name=f"{loc['emoji']} {loc['nome']}",
                value=f"*{loc['descricao'][:60]}...*\n💸 {ativo}",
                inline=True
            )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = SelectLocalView(message.author.id)
        await message.channel.send(embed=embed, view=view)

    async def handle_especies(self, message):
        embed = discord.Embed(
            title="🌍 ESPÉCIES DO IMPÉRIO DE TENSHI",
            description=f"*As raças que habitam os domínios eternos...*\n{SEP}",
            color=0x2B0A3D
        )
        for key, esp in ESPECIES.items():
            atribs = esp["atributos"]
            embed.add_field(
                name=f"{esp['emoji']} {esp['nome']}",
                value=(
                    f"*{esp['descricao'][:80]}...*\n"
                    f"❤️{atribs['vida']} 💙{atribs['mana']} 💪{atribs['forca']} 🌪️{atribs['agilidade']}\n"
                    f"⚡ *{esp['passiva']}*"
                ),
                inline=False
            )
        embed.add_field(name="\u200b", value=f"*Use `Tenshi, criar-ficha` para começar sua jornada!*", inline=False)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_meu_local(self, message):
        user = get_user(message.author.id)
        local_key = user.get("local_atual", "cidadela")
        loc       = LOCALIZACOES.get(local_key, LOCALIZACOES["cidadela"])

        embed = discord.Embed(
            title=f"{loc['emoji']} LOCALIZAÇÃO ATUAL",
            description=(
                f"*{message.author.display_name} está em...*\n{SEP}\n\n"
                f"**{loc['nome']}**\n*{loc['descricao']}*\n\n{SEP}"
            ),
            color=loc["cor"]
        )
        bonus_lines = []
        if loc["bonus_treino_xp"] != 1.0:
            sign = "+" if loc["bonus_treino_xp"] > 1 else ""
            bonus_lines.append(f"⚡ {sign}{int((loc['bonus_treino_xp']-1)*100)}% XP em treinos")
        if loc["bonus_missao_moedas"] != 1.0:
            sign = "+" if loc["bonus_missao_moedas"] > 1 else ""
            bonus_lines.append(f"💰 {sign}{int((loc['bonus_missao_moedas']-1)*100)}% moedas em missões")
        if loc["bonus_meditacao_xp"] != 1.0:
            sign = "+" if loc["bonus_meditacao_xp"] > 1 else ""
            bonus_lines.append(f"🧘 {sign}{int((loc['bonus_meditacao_xp']-1)*100)}% XP em meditação")
        if loc["acesso_mercado_negro"]:
            bonus_lines.append("🖤 Mercado Negro acessível")
        if loc["risco_invasao"]:
            bonus_lines.append("⚠️ Área de risco — invasões frequentes")
        if bonus_lines:
            embed.add_field(name="🌟 Bônus Ativos", value="\n".join(bonus_lines), inline=False)
        embed.add_field(name="🗺️ Viajar", value="`Tenshi, viajar` para mudar de localização", inline=False)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)
