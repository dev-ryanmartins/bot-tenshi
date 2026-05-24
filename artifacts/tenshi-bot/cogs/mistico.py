import discord
import random
from datetime import datetime, timedelta
from database import get_user, save_user
from utils import embed_imperial, embed_pegada, SEP, RODAPE_IMPERIAL, CORES_PEGADA, CORES_DESTAQUE

CARTAS_TAROT = [
    {"nome": "O Mago",            "simbolo": "🧙", "cor": 0x8A2BE2,
     "interpretacao": "A vontade manifesta realidade. Tudo que você declarar hoje tem peso de decreto imperial. Sua ação é sua magia.",
     "bonus": {"poder": 15}},
    {"nome": "A Sacerdotisa",     "simbolo": "🌙", "cor": 0x191970,
     "interpretacao": "Segredos aguardam nas sombras de Tenshi. O silêncio é mais afiado que qualquer lâmina. Observe antes de agir.",
     "bonus": {"xp": 30}},
    {"nome": "A Imperatriz",      "simbolo": "🌸", "cor": 0xC71585,
     "interpretacao": "A abundância flui como o Rio Eterno. O Império sorri para você — colha o que plantou com sangue e esforço.",
     "bonus": {"moedas": 60}},
    {"nome": "O Imperador",       "simbolo": "👑", "cor": 0xFFD700,
     "interpretacao": "A autoridade absoluta ressoa em seu espírito. Como o grande Alloy, você projeta poder e domínio irresistível.",
     "bonus": {"poder": 30}},
    {"nome": "O Hierofante",      "simbolo": "📿", "cor": 0x4B0082,
     "interpretacao": "A tradição e a sabedoria ancestral de Tenshi guiam seus passos. Honre os juramentos feitos.",
     "bonus": {"xp": 45}},
    {"nome": "Os Amantes",        "simbolo": "💫", "cor": 0xFF69B4,
     "interpretacao": "Uma escolha decisiva se aproxima. Dois caminhos — apenas um conduz à glória imperial.",
     "bonus": {"xp": 25, "moedas": 25}},
    {"nome": "O Carro",           "simbolo": "⚔️", "cor": 0x8B0000,
     "interpretacao": "Vitória conquistada pela determinação pura. Sua vontade domina o caos. Avance sem hesitar.",
     "bonus": {"poder": 20}},
    {"nome": "A Torre",           "simbolo": "⚡", "cor": 0x2F4F4F,
     "interpretacao": "Transformação violenta, necessária. O que cai hoje abre espaço para algo muito maior nas cinzas.",
     "bonus": {"xp": 55}},
    {"nome": "A Estrela",         "simbolo": "⭐", "cor": 0x00CED1,
     "interpretacao": "Esperança e renovação banham sua aura. Os astros de Tenshi conspiraram em seu favor esta jornada.",
     "bonus": {"poder": 10, "moedas": 40}},
    {"nome": "A Lua",             "simbolo": "🌕", "cor": 0x6A0DAD,
     "interpretacao": "O véu entre os mundos está fino. Ilusões e verdades se entrelaçam — confie apenas nos instintos mais profundos.",
     "bonus": {"xp": 40}},
    {"nome": "O Sol",             "simbolo": "☀️", "cor": 0xFFA500,
     "interpretacao": "Vitória e clareza absolutas. Tudo que tocar hoje florescerá. A luz imperial brilha especialmente sobre você.",
     "bonus": {"poder": 20, "moedas": 25}},
    {"nome": "O Julgamento",      "simbolo": "🔔", "cor": 0x696969,
     "interpretacao": "Um chamado ao renascimento. Uma fase de sua história em Tenshi se encerra — e outra épica começa.",
     "bonus": {"xp": 60}},
    {"nome": "O Mundo",           "simbolo": "🌍", "cor": 0x228B22,
     "interpretacao": "Completude e triunfo absoluto. Você está em perfeita harmonia com o destino imperial.",
     "bonus": {"poder": 15, "xp": 25, "moedas": 30}},
    {"nome": "O Louco",           "simbolo": "🃏", "cor": 0xFF6347,
     "interpretacao": "O início de algo extraordinário. A coragem de dar o salto sem garantias — isso define os lendários de Tenshi.",
     "bonus": {"moedas": 80}},
    {"nome": "A Força",           "simbolo": "🦁", "cor": 0xB8860B,
     "interpretacao": "Não a força bruta, mas a coragem interior. Você doma as feras internas — isso é poder verdadeiro.",
     "bonus": {"poder": 25, "xp": 20}},
    {"nome": "A Roda da Fortuna", "simbolo": "🎡", "cor": 0x9400D3,
     "interpretacao": "Os ciclos giram em seu favor hoje. O destino de Tenshi sorri — aproveite cada momento desta maré.",
     "bonus": {"moedas": 70, "xp": 30}},
    {"nome": "O Eremita",         "simbolo": "🕯️", "cor": 0x2F2F2F,
     "interpretacao": "A sabedoria interior ilumina mais que qualquer tocha do Palácio. O recolhimento revela segredos preciosos.",
     "bonus": {"xp": 65}},
    {"nome": "A Morte",           "simbolo": "💀", "cor": 0x1C1C1C,
     "interpretacao": "Transformação profunda. Nada verdadeiro morre — apenas se transforma. Nasça das cinzas mais poderoso.",
     "bonus": {"poder": 35}},
]

RUNAS = [
    {"nome": "Fehu",    "simbolo": "ᚠ", "cor": 0xDAA520,
     "interpretacao": "A runa da riqueza e abundância flui através de você. Os cofres de Tenshi se abrem em seu nome.",
     "bonus": {"moedas": 70}},
    {"nome": "Uruz",    "simbolo": "ᚢ", "cor": 0x8B0000,
     "interpretacao": "A força primordial do auroque corre em suas veias. Sua determinação é inabalável hoje.",
     "bonus": {"poder": 40}},
    {"nome": "Thurisaz","simbolo": "ᚦ", "cor": 0x1C1C1C,
     "interpretacao": "O martelo de Thor ressoa. A força destruidora trabalha a seu favor — o que resiste a você quebra.",
     "bonus": {"poder": 22, "xp": 22}},
    {"nome": "Ansuz",   "simbolo": "ᚨ", "cor": 0x4B0082,
     "interpretacao": "Odin sussurra segredos ancestrais de Tenshi em seu ouvido. Palavras têm poder hoje — use-as.",
     "bonus": {"xp": 75}},
    {"nome": "Raidho",  "simbolo": "ᚱ", "cor": 0x006400,
     "interpretacao": "O caminho se abre diante de você. Uma jornada épica começa — os passos certos aparecem naturalmente.",
     "bonus": {"xp": 45, "moedas": 25}},
    {"nome": "Kenaz",   "simbolo": "ᚲ", "cor": 0xFF4500,
     "interpretacao": "A tocha da criatividade e da técnica ilumina seu espírito. Forge algo grandioso hoje.",
     "bonus": {"xp": 50, "poder": 10}},
    {"nome": "Hagalaz", "simbolo": "ᚺ", "cor": 0x708090,
     "interpretacao": "A tempestade purificadora varre tudo que é fraco. O que sobrevive é aço puro — assim como você.",
     "bonus": {"xp": 55}},
    {"nome": "Sowilo",  "simbolo": "ᛋ", "cor": 0xFFD700,
     "interpretacao": "A runa solar irradia. Vitória é inevitável quando carregada — hoje você não pode ser derrotado.",
     "bonus": {"poder": 30, "moedas": 30}},
    {"nome": "Tiwaz",   "simbolo": "ᛏ", "cor": 0x00008B,
     "interpretacao": "A runa do guerreiro justo. Sua causa é honrada pelos deuses de Tenshi — lute com honra.",
     "bonus": {"poder": 45}},
    {"nome": "Othala",  "simbolo": "ᛟ", "cor": 0x8B4513,
     "interpretacao": "A runa do lar, herança e pertencimento. Suas raízes em Tenshi se aprofundam. Proteja o que é seu.",
     "bonus": {"poder": 15, "xp": 30, "moedas": 35}},
]

ASTROS = [
    {"nome": "Constelação de Tenshi — O Dragão",   "emoji": "🐉", "cor": 0x8A2BE2, "efeito": "Guerreiros ganham +20% XP em treinos", "bonus_classe": "Guarda Imperial"},
    {"nome": "Constelação do Véu Negro",           "emoji": "🌑", "cor": 0x1C1C1C, "efeito": "Místicos sentem a magia ampliada. Tarot concede bônus duplo", "bonus_classe": "Ordem Esotérica"},
    {"nome": "Constelação da Coroa Dourada",       "emoji": "👑", "cor": 0xFFD700, "efeito": "Diplomatas e nobres ganham +50% em transações políticas", "bonus_classe": "Corte de Tenshi"},
    {"nome": "Constelação da Espada Partida",      "emoji": "⚔️", "cor": 0x8B0000, "efeito": "Duelos têm intensidade aumentada. Vencedores ganham XP dobrado", "bonus_classe": "Todos"},
    {"nome": "Constelação do Mercador das Sombras","emoji": "🖤", "cor": 0x2C2C2C, "efeito": "Transações na máfia e mercado negro ganham bônus oculto", "bonus_classe": "Máfia"},
    {"nome": "Constelação da Fênix Renascida",     "emoji": "🔥", "cor": 0xFF4500, "efeito": "Mortes em duelo concedem renascimento imediato. Poder nunca cai", "bonus_classe": "Todos"},
]


class TarotView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.revelado = False

    @discord.ui.button(label="🃏 Puxar do Deck", style=discord.ButtonStyle.primary, emoji="✨")
    async def puxar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("*Este deck não é seu para consultar...*", ephemeral=True)
            return
        if self.revelado:
            await interaction.response.send_message("*A carta já foi revelada.*", ephemeral=True)
            return

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🃏 O DECK TREMULA...",
                description="*As cartas giram no éter de Tenshi...\nO destino se revela...*",
                color=0x1a1a2e
            ),
            view=None
        )

        user = get_user(interaction.user.id)
        agora = datetime.utcnow()
        if user.get("ultimo_tarot"):
            ultimo = datetime.fromisoformat(user["ultimo_tarot"])
            if agora - ultimo < timedelta(hours=20):
                proximo = ultimo + timedelta(hours=20)
                horas = int((proximo - agora).total_seconds() // 3600)
                mins  = int(((proximo - agora).total_seconds() % 3600) // 60)
                await interaction.edit_original_response(embed=embed_imperial(
                    "🌙 Os Arcanos Repousam",
                    f"*As cartas se recusam a falar por enquanto...*\n\nPróxima consulta em: **{horas}h {mins}m**",
                    0x1a1a2e
                ))
                return

        carta = random.choice(CARTAS_TAROT)
        bonus_str = []
        for stat, val in carta["bonus"].items():
            user[stat] = user.get(stat, 0) + val
            nomes = {"poder": "Poder", "xp": "XP", "moedas": "Moedas"}
            bonus_str.append(f"**+{val}** {nomes.get(stat, stat)}")

        user["ultimo_tarot"] = agora.isoformat()
        save_user(interaction.user.id, user)

        self.revelado = True
        embed = discord.Embed(
            title=f"🃏 {carta['simbolo']} {carta['nome'].upper()}",
            description=(
                f"*Os Arcanos de Tenshi falam...*\n{SEP}\n\n"
                f"*\"{carta['interpretacao']}\"*\n\n{SEP}"
            ),
            color=carta["cor"]
        )
        embed.add_field(name="✨ Bênção do Dia", value=" `•` ".join(bonus_str), inline=False)
        embed.set_footer(text=f"🌙 Nova consulta em 20 horas  •  {RODAPE_IMPERIAL}")

        purificar_view = None
        if random.random() < 0.15:
            embed.add_field(name="⚠️ Maldição Detectada", value="*A carta revela uma sombra sobre seu destino...*\nUse o botão abaixo para tentar purificar!", inline=False)
            purificar_view = PurificarView(interaction.user.id)

        await interaction.edit_original_response(embed=embed, view=purificar_view)


class PurificarView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="🔥 Sacrificar 50 Moedas para Purificar", style=discord.ButtonStyle.danger)
    async def purificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("*Essa maldição não é sua...*", ephemeral=True)
            return
        user = get_user(interaction.user.id)
        if user["moedas"] < 50:
            await interaction.response.send_message(embed=embed_imperial("❌", "Moedas insuficientes para o sacrifício.", 0x6B0000), ephemeral=True)
            return
        user["moedas"] -= 50
        sucesso = random.random() > 0.4
        if sucesso:
            user["poder"] += 10
            msg = "✅ *A sombra foi dissipada! Seu poder cresceu nas chamas do sacrifício.*\n**+10 Poder**"
        else:
            msg = "❌ *As chamas não foram suficientes... A sombra persiste por mais um ciclo.*"
        save_user(interaction.user.id, user)
        self.clear_items()
        await interaction.response.edit_message(
            embed=embed_imperial("🔥 Ritual de Purificação", msg, 0x8A2BE2 if sucesso else 0x6B0000),
            view=self
        )


class RunaView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id  = user_id
        self.revelado = False

    @discord.ui.button(label="🔮 Consultar a Pedra Rúnica", style=discord.ButtonStyle.secondary, emoji="⚡")
    async def consultar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("*Esta runa não responde a você...*", ephemeral=True)
            return
        if self.revelado:
            return

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🔮 A PEDRA PULSA...",
                description="*Luz violeta emana das inscrições ancestrais...*",
                color=0x4B0082
            ),
            view=None
        )

        user = get_user(interaction.user.id)
        agora = datetime.utcnow()
        if user.get("ultimo_tarot"):
            ultimo = datetime.fromisoformat(user["ultimo_tarot"])
            if agora - ultimo < timedelta(hours=20):
                proximo = ultimo + timedelta(hours=20)
                horas = int((proximo - agora).total_seconds() // 3600)
                mins  = int(((proximo - agora).total_seconds() % 3600) // 60)
                await interaction.edit_original_response(embed=embed_imperial(
                    "🔮 As Runas Dormem",
                    f"*A pedra rúnica repousa...*\n\nPróxima consulta em: **{horas}h {mins}m**",
                    0x1a1a2e
                ))
                return

        runa = random.choice(RUNAS)
        bonus_str = []
        for stat, val in runa["bonus"].items():
            user[stat] = user.get(stat, 0) + val
            nomes = {"poder": "Poder", "xp": "XP", "moedas": "Moedas"}
            bonus_str.append(f"**+{val}** {nomes.get(stat, stat)}")

        user["ultimo_tarot"] = agora.isoformat()
        save_user(interaction.user.id, user)

        self.revelado = True
        embed = discord.Embed(
            title=f"🔮 {runa['simbolo']} {runa['nome'].upper()} — Runa Ancestral",
            description=(
                f"*A pedra rúnica de Tenshi fala...*\n{SEP}\n\n"
                f"*\"{runa['interpretacao']}\"*\n\n{SEP}"
            ),
            color=runa["cor"]
        )
        embed.add_field(name="⚡ Poder Rúnico", value=" `•` ".join(bonus_str), inline=False)
        embed.set_footer(text=f"🔮 Nova runa em 20 horas  •  {RODAPE_IMPERIAL}")
        await interaction.edit_original_response(embed=embed, view=None)


class Mistico:
    def __init__(self, bot):
        self.bot = bot

    async def handle_tarot(self, message):
        user = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")
        embed = discord.Embed(
            title="🃏 OS ARCANOS DE TENSHI",
            description=(
                f"*As cartas aguardam ser consultadas, {message.author.display_name}...*\n{SEP}\n\n"
                f"Clique no botão para que o destino se revele através dos Arcanos Maiores.\n\n"
                f"*Uma leitura por dia — 20 horas de cooldown.*\n{SEP}"
            ),
            color=CORES_PEGADA.get(pegada, 0x2B0A3D)
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = TarotView(message.author.id)
        await message.channel.send(embed=embed, view=view)

    async def handle_runa(self, message):
        user = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")
        embed = discord.Embed(
            title="🔮 RUNAS ANCESTRAIS DE TENSHI",
            description=(
                f"*A pedra rúnica aguarda sua mão, {message.author.display_name}...*\n{SEP}\n\n"
                f"Clique no botão para consultar os símbolos dos guerreiros nórdicos de Tenshi.\n\n"
                f"*Uma runa por dia — 20 horas de cooldown.*\n{SEP}"
            ),
            color=CORES_PEGADA.get(pegada, 0x2B0A3D)
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = RunaView(message.author.id)
        await message.channel.send(embed=embed, view=view)

    async def handle_astros(self, message):
        astro = random.choice(ASTROS)
        embed = discord.Embed(
            title=f"🌌 {astro['emoji']} {astro['nome']}",
            description=(
                f"*Os astrônomos da Torre Imperial observam os céus de Tenshi...*\n{SEP}\n\n"
                f"**Influência Atual:**\n*{astro['efeito']}*\n\n"
                f"**Facção/Classe Favorecida:** {astro['bonus_classe']}\n\n{SEP}"
            ),
            color=astro["cor"]
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_destino(self, message, args):
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "Mencione alguém: `Tenshi, destino @usuario`", 0x6B0000))
            return
        alvo = message.mentions[0]
        compatibilidade = random.randint(30, 100)
        tipo = random.choice([
            ("Almas Gêmeas Imperiais", "✨", "Uma ligação rara — seus destinos estão entrelaçados pelos fios do cosmos de Tenshi."),
            ("Rivais Destinados",      "⚔️", "Forjados para se enfrentar. Essa tensão move montanhas no Império."),
            ("Aliados de Sangue",      "🤝", "A confiança entre vocês resiste ao tempo e à traição. Um vínculo raro."),
            ("Mistério Profundo",      "🌑", "Os Arcanos se recusam a revelar completamente. Há algo oculto nesta conexão."),
            ("Laços de Guerra",        "🔥", "Forjados nas chamas do conflito — apenas a batalha revela a verdade entre vocês."),
        ])
        barra = "█" * (compatibilidade // 10) + "░" * (10 - compatibilidade // 10)
        embed = discord.Embed(
            title=f"🔮 LEITURA DE DESTINO EMPARELHADA",
            description=(
                f"*Os Arcanos revelam o fio que conecta dois súditos de Tenshi...*\n{SEP}"
            ),
            color=0x4B0082
        )
        embed.add_field(name="👤 Almas",       value=f"{message.author.display_name} ↔ {alvo.display_name}", inline=False)
        embed.add_field(name=f"{tipo[1]} Vínculo", value=f"**{tipo[0]}**\n*{tipo[2]}*", inline=False)
        embed.add_field(name="💫 Compatibilidade", value=f"`{barra}` **{compatibilidade}%**", inline=False)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_sacrificio(self, message, args):
        user = get_user(message.author.id)
        if not args:
            divida_moedas = sum(e["valor_restante"] for e in user.get("emprestimos", []))
            embed = embed_imperial(
                "🔥 SACRIFÍCIO RITUALÍSTICO",
                f"*Queime recursos para tentar remover uma maldição...*\n{SEP}\n\n"
                f"Use: `Tenshi, sacrificio [moedas] [quantidade]`\n"
                f"Exemplo: `Tenshi, sacrificio moedas 100`\n\n"
                f"*O sucesso não é garantido — é um ritual, não um negócio.*",
                0x8A2BE2
            )
            await message.channel.send(embed=embed)
            return
        tipo  = args[0].lower() if args else "moedas"
        valor = 0
        for a in args[1:]:
            if a.isdigit():
                valor = int(a)
                break
        if valor <= 0:
            valor = 50
        if tipo in ("moedas", "coins") and user["moedas"] >= valor:
            user["moedas"] -= valor
            sucesso = random.random() > 0.45
            if sucesso:
                user["poder"] += valor // 10
                msg = f"✅ *As chamas consumiram {valor} moedas e purificaram sua aura!*\n**+{valor // 10} Poder** concedido pelo ritual."
            else:
                msg = f"❌ *As chamas se apagaram antes de completar o ritual. {valor} moedas foram perdidas...*\n*Tente novamente quando os astros estiverem favoráveis.*"
            save_user(message.author.id, user)
            await message.channel.send(embed=embed_imperial("🔥 Ritual de Sacrifício", msg, 0x8A2BE2 if sucesso else 0x6B0000))
        else:
            await message.channel.send(embed=embed_imperial("❌", "Moedas insuficientes para o sacrifício.", 0x6B0000))

    async def handle_ritual(self, message):
        user = get_user(message.author.id)
        faccao = user.get("faccao")
        if not faccao:
            await message.channel.send(embed=embed_imperial("❌", "Você precisa pertencer a uma facção para realizar rituais de proteção.", 0x6B0000))
            return
        embed = discord.Embed(
            title="🛡️ RITUAL DE PROTEÇÃO FACCIONAL",
            description=(
                f"*Os membros da **{faccao}** se unem em círculo ritual...*\n{SEP}\n\n"
                f"**{message.author.display_name}** selou as energias protetoras deste canal.\n"
                f"*Nenhum espião pode penetrar os véus místicos por **24 horas**.*\n\n{SEP}"
            ),
            color=0x4B0082
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)
