import discord
import random
import asyncio
from datetime import datetime
from database import get_user, save_user, add_pontos_faccao, calcular_nivel
from utils import embed_imperial, embed_pegada, IMPERADOR_ID, SEP, RODAPE_IMPERIAL, CORES_PEGADA

# Narrativas de ataque para RP de texto
NARRATIVAS_ATAQUE = [
    "avança com um golpe brutal que faz o ar vibrar",
    "desfere uma sequência relâmpago de três golpes consecutivos",
    "canaliza a energia imperial em seus punhos e ataca",
    "executa um corte diagonal com precisão letal",
    "usa a técnica aprendida nas catacumbas de Tenshi",
    "invoca a força das runas em um soco sísmico",
    "lança uma rajada de energia sombria condensada",
    "avança em velocidade sobrenatural e desfere um golpe certeiro",
    "rompe a guarda do adversário com uma investida brutal",
    "descarrega toda a energia acumulada em um ataque devastador",
]

NARRATIVAS_DEFESA = [
    "assume postura de pedra e absorve o impacto",
    "desvia no último segundo com um passo de lado elegante",
    "usa o manto sombrio para dissipar o ataque",
    "cria uma barreira de energia e bloqueia o golpe",
    "recua estrategicamente e mantém a compostura",
    "usa o terreno a seu favor e esquiva com maestria",
    "interpõe a arma e redireciona a força do ataque",
]

NARRATIVAS_POCAO = [
    "abre uma vial de poção carmesim e bebe de um gole",
    "usa um amuleto de cura e sente a energia fluir",
    "conjura uma bênção das runas e recupera forças",
    "consome uma erva rara colhida nas florestas de Tenshi",
]


class DueloView(discord.ui.View):
    """View interativa de duelo turno a turno com botões"""

    def __init__(self, desafiante: discord.User | discord.Member,
                 alvo: discord.User | discord.Member,
                 aposta: int, bot):
        super().__init__(timeout=300)
        self.desafiante   = desafiante
        self.alvo         = alvo
        self.aposta       = aposta
        self.bot          = bot

        self.hp           = {desafiante.id: 100, alvo.id: 100}
        self.poder        = {desafiante.id: 0, alvo.id: 0}
        self.defesa_bonus = {desafiante.id: 0, alvo.id: 0}
        self.turno        = desafiante.id
        self.rodada       = 1
        self.log          = []
        self.encerrado    = False
        self._carregar_poder()

    def _carregar_poder(self):
        ud = get_user(self.desafiante.id)
        ua = get_user(self.alvo.id)
        self.poder[self.desafiante.id] = max(20, ud.get("poder", 50))
        self.poder[self.alvo.id]       = max(20, ua.get("poder", 50))

    def _outro(self, uid: int) -> int:
        return self.alvo.id if uid == self.desafiante.id else self.desafiante.id

    def _nome(self, uid: int) -> str:
        return self.desafiante.display_name if uid == self.desafiante.id else self.alvo.display_name

    def _build_embed(self) -> discord.Embed:
        hp_d = self.hp[self.desafiante.id]
        hp_a = self.hp[self.alvo.id]
        bar_d = "❤️" * max(0, hp_d // 10) + "🖤" * (10 - max(0, hp_d // 10))
        bar_a = "❤️" * max(0, hp_a // 10) + "🖤" * (10 - max(0, hp_a // 10))
        vez   = self._nome(self.turno)
        cor   = 0x8B0000 if self.rodada > 3 else 0xFFD700

        embed = discord.Embed(
            title=f"⚔️ ARENA IMPERIAL — Rodada {self.rodada}",
            description=f"*As arenas de Tenshi aguardam... É a vez de **{vez}**!*\n{SEP}",
            color=cor
        )
        embed.add_field(
            name=f"🗡️ {self.desafiante.display_name}",
            value=f"`{bar_d}` **{max(0,hp_d)} HP**",
            inline=True
        )
        embed.add_field(name="VS", value="⚔️", inline=True)
        embed.add_field(
            name=f"🗡️ {self.alvo.display_name}",
            value=f"`{bar_a}` **{max(0,hp_a)} HP**",
            inline=True
        )
        if self.log:
            ultimos = self.log[-3:]
            embed.add_field(name="📜 Últimas ações", value="\n".join(ultimos), inline=False)
        if self.aposta > 0:
            embed.add_field(name="💰 Aposta", value=f"**{self.aposta}** moedas em jogo", inline=False)
        embed.set_footer(text=f"⚔️ Clique no botão para agir  •  {RODAPE_IMPERIAL}")
        return embed

    def _atualizar_botoes(self):
        self.clear_items()
        if self.encerrado:
            return
        u_pode = get_user(self.turno)
        tem_pocao = len(u_pode.get("inventario", [])) > 0

        btn_atk = discord.ui.Button(label="⚔️ Atacar",    style=discord.ButtonStyle.danger,   row=0)
        btn_def = discord.ui.Button(label="🛡️ Defender",  style=discord.ButtonStyle.secondary, row=0)
        btn_poc = discord.ui.Button(label="🧪 Usar Poção", style=discord.ButtonStyle.success,   row=0, disabled=not tem_pocao)
        btn_rnd = discord.ui.Button(label="🏳️ Render-se",  style=discord.ButtonStyle.secondary, row=1)

        btn_atk.callback = self._cb_atacar
        btn_def.callback = self._cb_defender
        btn_poc.callback = self._cb_pocao
        btn_rnd.callback = self._cb_render

        for b in [btn_atk, btn_def, btn_poc, btn_rnd]:
            self.add_item(b)

    async def _verificar_vez(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.turno:
            outro = self._nome(self.turno)
            await interaction.response.send_message(
                f"*Aguarde — é a vez de **{outro}** agir na arena.*", ephemeral=True
            )
            return False
        if self.encerrado:
            await interaction.response.send_message("*O duelo já foi encerrado.*", ephemeral=True)
            return False
        return True

    async def _cb_atacar(self, interaction: discord.Interaction):
        if not await self._verificar_vez(interaction):
            return
        atacante = interaction.user.id
        alvo_id  = self._outro(atacante)
        poder_at = self.poder[atacante]
        poder_al = self.poder[alvo_id]
        def_bonus = self.defesa_bonus[alvo_id]

        dano_base = max(5, int(poder_at / max(poder_al, 1) * random.randint(18, 35)))
        dano_final = max(0, dano_base - def_bonus)
        self.hp[alvo_id] -= dano_final
        self.defesa_bonus[alvo_id] = 0

        narrativa = random.choice(NARRATIVAS_ATAQUE)
        self.log.append(f"⚔️ **{self._nome(atacante)}** {narrativa} → **-{dano_final} HP** para {self._nome(alvo_id)}")

        if self.hp[alvo_id] <= 0:
            await self._encerrar(interaction, vencedor_id=atacante)
            return

        self.turno  = alvo_id
        self.rodada += 1
        self._atualizar_botoes()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    async def _cb_defender(self, interaction: discord.Interaction):
        if not await self._verificar_vez(interaction):
            return
        uid = interaction.user.id
        bonus = random.randint(10, 20)
        self.defesa_bonus[uid] = bonus
        narrativa = random.choice(NARRATIVAS_DEFESA)
        self.log.append(f"🛡️ **{self._nome(uid)}** {narrativa} → **+{bonus} defesa** no próximo golpe")
        self.turno  = self._outro(uid)
        self.rodada += 1
        self._atualizar_botoes()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    async def _cb_pocao(self, interaction: discord.Interaction):
        if not await self._verificar_vez(interaction):
            return
        uid = interaction.user.id
        user = get_user(uid)
        inv = user.get("inventario", [])
        if not inv:
            await interaction.response.send_message("*Seu inventário está vazio.*", ephemeral=True)
            return
        cura = random.randint(15, 35)
        self.hp[uid] = min(100, self.hp[uid] + cura)
        item_usado = inv.pop(0)
        user["inventario"] = inv
        save_user(uid, user)
        narrativa = random.choice(NARRATIVAS_POCAO)
        self.log.append(f"🧪 **{self._nome(uid)}** {narrativa} → **+{cura} HP** recuperado")
        self.turno  = self._outro(uid)
        self.rodada += 1
        self._atualizar_botoes()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    async def _cb_render(self, interaction: discord.Interaction):
        if not await self._verificar_vez(interaction):
            return
        vencedor_id = self._outro(interaction.user.id)
        self.hp[interaction.user.id] = 0
        await self._encerrar(interaction, vencedor_id=vencedor_id, rendeu=True)

    async def _encerrar(self, interaction: discord.Interaction, vencedor_id: int, rendeu: bool = False):
        self.encerrado = True
        self.clear_items()

        perdedor_id = self._outro(vencedor_id)
        user_v      = get_user(vencedor_id)
        user_p      = get_user(perdedor_id)

        xp_ganho    = random.randint(50, 90)
        moedas_rec  = self.aposta if self.aposta > 0 else random.randint(20, 50)

        user_v["xp"]    += xp_ganho
        user_v["poder"] += 8
        user_v["vitorias_duelo"] = user_v.get("vitorias_duelo", 0) + 1
        user_p["derrotas_duelo"] = user_p.get("derrotas_duelo", 0) + 1

        if self.aposta > 0:
            user_v["moedas"] += self.aposta
            user_p["moedas"] = max(0, user_p.get("moedas", 0) - self.aposta)

        nivel_v, _ = calcular_nivel(user_v["xp"])
        user_v["nivel"] = nivel_v
        if user_v.get("faccao"):
            add_pontos_faccao(user_v["faccao"], 10)

        save_user(vencedor_id, user_v)
        save_user(perdedor_id, user_p)

        nome_v = self._nome(vencedor_id)
        nome_p = self._nome(perdedor_id)

        log_formatado = "\n".join(self.log) if self.log else "*Duelo relâmpago!*"

        if rendeu:
            desfecho = f"*{nome_p} ergueu as mãos em rendição. A honra pertence a {nome_v}.*"
        else:
            desfecho = f"*{nome_p} cai na arena. As chamas de Tenshi coroam {nome_v} como vencedor.*"

        embed = discord.Embed(
            title=f"🏆 DUELO ENCERRADO — {nome_v.upper()} VENCE!",
            description=f"*{desfecho}*\n{SEP}\n{log_formatado}\n{SEP}",
            color=0xFFD700
        )
        embed.add_field(
            name=f"👑 Vencedor: {nome_v}",
            value=f"**+{xp_ganho} XP** • **+8 Poder** • **+{moedas_rec} Moedas**",
            inline=False
        )
        embed.add_field(
            name=f"💀 Derrotado: {nome_p}",
            value="*A derrota é a melhor professora. Treine e volte mais forte.*",
            inline=False
        )
        embed.set_footer(text=f"⚔️ As arenas de Tenshi revelam a verdade  •  {RODAPE_IMPERIAL}")
        await interaction.response.edit_message(embed=embed, view=self)


class DesafioView(discord.ui.View):
    def __init__(self, desafiante, alvo, aposta: int, bot, duelo_cog):
        super().__init__(timeout=60)
        self.desafiante = desafiante
        self.alvo       = alvo
        self.aposta     = aposta
        self.bot        = bot
        self.duelo_cog  = duelo_cog
        self.respondido = False

    @discord.ui.button(label="⚔️ Aceitar Desafio", style=discord.ButtonStyle.danger)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alvo.id:
            await interaction.response.send_message("*Este desafio não é para você.*", ephemeral=True)
            return
        if self.respondido:
            return
        self.respondido = True
        self.clear_items()

        view_duelo = DueloView(self.desafiante, self.alvo, self.aposta, self.bot)
        view_duelo._atualizar_botoes()
        embed = view_duelo._build_embed()
        embed.description = f"*{self.alvo.display_name} aceita! O duelo começa!*\n{SEP}"
        await interaction.response.edit_message(embed=embed, view=view_duelo)
        chave = f"{min(self.desafiante.id, self.alvo.id)}-{max(self.desafiante.id, self.alvo.id)}"
        self.duelo_cog.duelos_ativos.discard(chave)

    @discord.ui.button(label="🏃 Recusar", style=discord.ButtonStyle.secondary)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.alvo.id, self.desafiante.id):
            await interaction.response.send_message("*Você não faz parte deste duelo.*", ephemeral=True)
            return
        if self.respondido:
            return
        self.respondido = True
        self.clear_items()
        chave = f"{min(self.desafiante.id, self.alvo.id)}-{max(self.desafiante.id, self.alvo.id)}"
        self.duelo_cog.duelos_ativos.discard(chave)
        await interaction.response.edit_message(
            embed=embed_imperial("💨 Desafio Recusado",
                                 f"*{self.alvo.display_name} virou as costas para o desafio...*\n\n"
                                 f"A covardia tem um preço na corte de Tenshi.", 0x2C2F33),
            view=self
        )


class Duelo:
    def __init__(self, bot):
        self.bot          = bot
        self.duelos_ativos: set = set()
        self.apostas_ativas: dict = {}

    async def handle_duelo(self, message, args):
        if not message.mentions:
            await message.channel.send(embed=embed_imperial(
                "⚔️ Desafio de Duelo",
                f"*Para desafiar um adversário nas arenas imperiais:*\n{SEP}\n\n"
                f"`Tenshi, duelo @usuario [aposta opcional]`\n\n"
                f"*O duelo é turno a turno — cada guerreiro age com botões.*",
                0x8B0000
            ))
            return

        alvo = message.mentions[0]
        if alvo.id == message.author.id:
            await message.channel.send(embed=embed_imperial("❌", "*Você não pode duelar com sua própria sombra...*", 0x6B0000))
            return
        if alvo.bot:
            await message.channel.send(embed=embed_imperial("❌", "*Os bots não pisam nas arenas imperiais.*", 0x6B0000))
            return

        chave = f"{min(message.author.id, alvo.id)}-{max(message.author.id, alvo.id)}"
        if chave in self.duelos_ativos:
            await message.channel.send(embed=embed_imperial("⚠️", "Já existe um duelo ativo entre vocês.", 0xFF8C00))
            return

        aposta = 0
        for a in args:
            c = a.replace(",", "")
            if c.isdigit():
                aposta = int(c)
                break

        if aposta > 0:
            user_d = get_user(message.author.id)
            if user_d["moedas"] < aposta:
                await message.channel.send(embed=embed_imperial("💸", f"Você não tem **{aposta}** moedas para apostar.", 0x6B0000))
                return

        self.duelos_ativos.add(chave)

        user_d = get_user(message.author.id)
        user_a = get_user(alvo.id)

        embed = discord.Embed(
            title="⚔️ DESAFIO DE DUELO IMPERIAL",
            description=(
                f"*As arenas de Tenshi rugem de antecipação...*\n{SEP}\n\n"
                f"**{message.author.display_name}** lança o desafio para **{alvo.display_name}**!\n\n"
                f"💥 Poder: **{user_d.get('poder', 0)}** vs **{user_a.get('poder', 0)}**\n"
                + (f"💰 Aposta em jogo: **{aposta}** moedas\n" if aposta else "") +
                f"\n{SEP}\n*{alvo.mention}, você aceita o desafio?*"
            ),
            color=0x8B0000
        )
        embed.set_footer(text=f"⏱️ Expira em 60 segundos  •  {RODAPE_IMPERIAL}")

        view = DesafioView(message.author, alvo, aposta, self.bot, self)
        msg  = await message.channel.send(f"{alvo.mention}", embed=embed, view=view)

        await asyncio.sleep(60)
        if not view.respondido:
            view.respondido = True
            view.clear_items()
            self.duelos_ativos.discard(chave)
            await msg.edit(embed=embed_imperial(
                "💨 Desafio Expirado",
                f"*{alvo.display_name} não respondeu ao chamado das arenas...*\n"
                f"A honra por hoje pertence a {message.author.display_name}.",
                0x2C2F33
            ), view=view)

    async def handle_aceitar_duelo(self, message):
        await message.channel.send(embed=embed_imperial(
            "ℹ️ Duelos com Botões",
            "*Os duelos de Tenshi agora usam botões interativos!*\n\n"
            "Use `Tenshi, duelo @usuario` para desafiar — o adversário clica para aceitar diretamente.",
            0x2B0A3D
        ))

    async def handle_apostar(self, message, args):
        if not message.mentions or not args:
            await message.channel.send(embed=embed_imperial(
                "💰 Sistema de Apostas",
                f"*Para apostar em duelos ativos:*\n{SEP}\n\nEm desenvolvimento — inclua a aposta diretamente no desafio:\n`Tenshi, duelo @usuario [valor]`",
                0x2B0A3D
            ))
            return
