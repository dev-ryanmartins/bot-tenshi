"""
Módulo Avançado — Funcionalidades 1-5
1. Trancar/Destrancar casa (lock/unlock mensagens no canal)
2. Garagem e veículos
3. Esportes na quadra (mini-game de dados)
4. Pool party na piscina
5. Sistema de Pets avançado
"""
import discord
import random
import asyncio
from datetime import datetime, timedelta
from database import get_user, save_user, get_vizinhanca, save_vizinhanca
from utils import SEP, RODAPE_IMPERIAL

# ─── Paleta Imperial Sóbria ───────────────────────────────────────────────────
COR_IMPERIAL  = 0x2C3E50
COR_DOURADO   = 0x9E7815
COR_PRETO     = 0x111111
COR_SUCESSO   = 0x1A5C2E
COR_PERIGO    = 0x7B1F1F
COR_NEUTRO    = 0x3D3D3D

def embed_soberano(titulo: str, descricao: str, cor: int = COR_IMPERIAL) -> discord.Embed:
    e = discord.Embed(title=titulo, description=descricao, color=cor)
    e.set_footer(text=RODAPE_IMPERIAL)
    return e

# ─── VEÍCULOS ─────────────────────────────────────────────────────────────────
CATALOGO_VEICULOS = {
    "bicicleta_arcana":   {"nome": "Bicicleta Arcana",        "emoji": "🚲", "preco": 120, "reducao_trem": 0.10, "descricao": "Transporte simples com runas de agilidade."},
    "moto_sombria":       {"nome": "Moto das Sombras",        "emoji": "🏍️", "preco": 500, "reducao_trem": 0.25, "descricao": "Veloz e silenciosa. Usada pelos mensageiros da Máfia."},
    "carro_imperial":     {"nome": "Sedan Imperial",          "emoji": "🚗", "preco": 800, "reducao_trem": 0.30, "descricao": "Conforto e discrição para os nobres da corte."},
    "montaria_fenix":     {"nome": "Montaria Fênix",          "emoji": "🦅", "preco": 1500,"reducao_trem": 0.50, "descricao": "Criatura mística que reduz drasticamente o tempo de viagem."},
    "dragao_cargueiro":   {"nome": "Dragão Cargueiro",        "emoji": "🐉", "preco": 3000,"reducao_trem": 0.70, "descricao": "O veículo mais raro de Tenshi. Velocidade incomparável."},
}

# ─── PETS ────────────────────────────────────────────────────────────────────
CATALOGO_PETS = {
    "cao_guarda":     {"nome": "Cão de Guarda Imperial",  "emoji": "🐕", "preco": 300, "passivo": "defesa",   "bonus": 15, "descricao": "Aumenta a defesa em duelos em 15%."},
    "corvo_espia":    {"nome": "Corvo Espião",             "emoji": "🐦‍⬛","preco": 400, "passivo": "espiao",   "bonus": 10, "descricao": "Revela a espécie do oponente antes do duelo."},
    "gato_sorte":     {"nome": "Gato da Sorte Mística",   "emoji": "🐱", "preco": 250, "passivo": "sorte",    "bonus": 10, "descricao": "+10% de sorte em tarot e runas."},
    "serpente_veneno":{"nome": "Serpente de Veneno",       "emoji": "🐍", "preco": 600, "passivo": "ataque",   "bonus": 20, "descricao": "+20% de poder de ataque em duelos."},
    "lobo_alfa":      {"nome": "Lobo Alfa das Neves",      "emoji": "🐺", "preco": 900, "passivo": "combo",    "bonus": 25, "descricao": "+25% de poder total em duelos. Intimidação passiva."},
    "polvinho_arcano":{"nome": "Polvinho Arcano",          "emoji": "🐙", "preco": 200, "passivo": "mana",     "bonus": 10, "descricao": "+10 de mana regenerado por ação."},
    "raposa_furtiva": {"nome": "Raposa Furtiva",           "emoji": "🦊", "preco": 500, "passivo": "furtividade","bonus":15,"descricao": "+15% de chance de furto no #beco."},
}


class VisualizarVeiculos(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=90)
        self.user_id = user_id
        for vid, v in CATALOGO_VEICULOS.items():
            b = discord.ui.Button(
                label=f"{v['emoji']} {v['nome']} — {v['preco']}💰",
                style=discord.ButtonStyle.secondary,
                custom_id=f"comprar_veiculo_{vid}"
            )
            b.callback = self._make_cb(vid, v)
            self.add_item(b)

    def _make_cb(self, vid: str, v: dict):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("Painel restrito.", ephemeral=True)
                return
            user = get_user(interaction.user.id)
            if user.get("veiculo"):
                await interaction.response.send_message(
                    embed=embed_soberano("Veículo Registrado", f"Você já possui **{user['veiculo']}**. Venda-o antes de adquirir outro.", COR_NEUTRO),
                    ephemeral=True
                )
                return
            if user["moedas"] < v["preco"]:
                await interaction.response.send_message(
                    embed=embed_soberano("Saldo Insuficiente", f"Necessário: **{v['preco']}** moedas. Disponível: **{user['moedas']}**.", COR_PERIGO),
                    ephemeral=True
                )
                return
            user["moedas"] -= v["preco"]
            user["veiculo"] = vid
            save_user(interaction.user.id, user)
            await interaction.response.send_message(
                embed=embed_soberano(
                    f"{v['emoji']} Veículo Adquirido",
                    f"**{v['nome']}** registrado na garagem imperial.\n\n"
                    f"Redução de cooldown de trem: **{int(v['reducao_trem']*100)}%**\n\n*{v['descricao']}*",
                    COR_SUCESSO
                ),
                ephemeral=True
            )
        return callback


class VisualizarPets(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=90)
        self.user_id = user_id
        for pid, p in CATALOGO_PETS.items():
            b = discord.ui.Button(
                label=f"{p['emoji']} {p['nome']} — {p['preco']}💰",
                style=discord.ButtonStyle.secondary,
                custom_id=f"comprar_pet_{pid}"
            )
            b.callback = self._make_cb(pid, p)
            self.add_item(b)

    def _make_cb(self, pid: str, p: dict):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("Painel restrito.", ephemeral=True)
                return
            user = get_user(interaction.user.id)
            if user.get("pet"):
                await interaction.response.send_message(
                    embed=embed_soberano("Pet Registrado", f"Você já possui **{user['pet']}**.", COR_NEUTRO),
                    ephemeral=True
                )
                return
            if user["moedas"] < p["preco"]:
                await interaction.response.send_message(
                    embed=embed_soberano("Saldo Insuficiente", f"Necessário: **{p['preco']}** moedas.", COR_PERIGO),
                    ephemeral=True
                )
                return
            user["moedas"] -= p["preco"]
            user["pet"] = pid
            save_user(interaction.user.id, user)
            embed = discord.Embed(title=f"{p['emoji']} Pet Adquirido", color=COR_SUCESSO)
            embed.add_field(name="Nome", value=p["nome"], inline=True)
            embed.add_field(name="Passivo", value=p["descricao"], inline=False)
            embed.set_footer(text=RODAPE_IMPERIAL)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        return callback


# ─── MINI-GAME ESPORTIVO ──────────────────────────────────────────────────────
class JogoEsportivo(discord.ui.View):
    def __init__(self, desafiante: discord.Member, adversario: discord.Member, esporte: str):
        super().__init__(timeout=120)
        self.desafiante = desafiante
        self.adversario = adversario
        self.esporte    = esporte
        self.apostas    = {}
        self.confirmados= set()

    @discord.ui.button(label="Aceitar Desafio", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.adversario.id:
            await interaction.response.send_message("Este desafio não é direcionado a você.", ephemeral=True)
            return
        self.confirmados.add(interaction.user.id)
        self.clear_items()
        await interaction.response.edit_message(
            embed=embed_soberano(
                f"{'🏀' if self.esporte == 'basquete' else '⚽'} Partida Iniciada",
                f"**{self.desafiante.display_name}** vs **{self.adversario.display_name}**\n\n*Calculando resultado...*",
                COR_IMPERIAL
            ),
            view=self
        )
        await asyncio.sleep(2)
        await self._resolver(interaction)

    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.adversario.id:
            await interaction.response.send_message("Painel restrito.", ephemeral=True)
            return
        self.clear_items()
        await interaction.response.edit_message(
            embed=embed_soberano("Desafio Recusado", f"{interaction.user.display_name} recusou a partida.", COR_NEUTRO),
            view=self
        )

    async def _resolver(self, interaction: discord.Interaction):
        d1 = get_user(self.desafiante.id)
        d2 = get_user(self.adversario.id)
        pts1 = random.randint(60, 100) + d1.get("poder", 100) // 20
        pts2 = random.randint(60, 100) + d2.get("poder", 100) // 20
        vencedor = self.desafiante if pts1 > pts2 else self.adversario
        perdedor = self.adversario if pts1 > pts2 else self.desafiante
        premio   = random.randint(30, 80)
        vuser    = get_user(vencedor.id)
        vuser["moedas"] = vuser.get("moedas", 0) + premio
        vuser["xp"]     = vuser.get("xp", 0) + 15
        save_user(vencedor.id, vuser)
        emoji = "🏀" if self.esporte == "basquete" else "⚽"
        embed = discord.Embed(
            title=f"{emoji} Resultado da Partida",
            color=COR_DOURADO
        )
        embed.add_field(name=self.desafiante.display_name, value=f"**{pts1} pts**", inline=True)
        embed.add_field(name="vs", value="—", inline=True)
        embed.add_field(name=self.adversario.display_name, value=f"**{pts2} pts**", inline=True)
        embed.add_field(
            name="Vencedor",
            value=f"{vencedor.mention} +{premio} moedas  |  +15 XP",
            inline=False
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        try:
            await interaction.followup.send(embed=embed)
        except Exception:
            pass


# ─── POOL PARTY ───────────────────────────────────────────────────────────────
_pool_party_ativo: dict[int, datetime] = {}


# ─── COG PRINCIPAL ────────────────────────────────────────────────────────────
class Avancado:
    def __init__(self, bot):
        self.bot = bot

    # 1. TRANCAR / DESTRANCAR CASA
    async def handle_trancar_casa(self, message):
        user = get_user(message.author.id)
        numero = user.get("casa_condominio")
        if not numero:
            await message.channel.send(embed=embed_soberano("Sem Residência", "Você não possui uma residência no condomínio.", COR_PERIGO))
            return
        canal = await self._get_canal_casa(message.guild, numero)
        if not canal:
            await message.channel.send(embed=embed_soberano("Canal Não Localizado", f"Canal casa-{numero} não encontrado.", COR_PERIGO))
            return
        try:
            await canal.set_permissions(message.guild.default_role, send_messages=False)
        except discord.Forbidden:
            await message.channel.send(embed=embed_soberano("Permissão Negada", "O bot não possui permissão para alterar este canal.", COR_PERIGO))
            return
        embed = discord.Embed(title="🔒 Residência Trancada", color=COR_NEUTRO)
        embed.add_field(name="Canal", value=canal.mention, inline=True)
        embed.add_field(name="Status", value="Mensagens bloqueadas para visitantes", inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_destrancar_casa(self, message):
        user = get_user(message.author.id)
        numero = user.get("casa_condominio")
        if not numero:
            await message.channel.send(embed=embed_soberano("Sem Residência", "Você não possui uma residência no condomínio.", COR_PERIGO))
            return
        canal = await self._get_canal_casa(message.guild, numero)
        if not canal:
            await message.channel.send(embed=embed_soberano("Canal Não Localizado", f"Canal casa-{numero} não encontrado.", COR_PERIGO))
            return
        try:
            await canal.set_permissions(message.guild.default_role, send_messages=None)
        except discord.Forbidden:
            await message.channel.send(embed=embed_soberano("Permissão Negada", "O bot não possui permissão para alterar este canal.", COR_PERIGO))
            return
        embed = discord.Embed(title="🔓 Residência Destrancada", color=COR_SUCESSO)
        embed.add_field(name="Canal", value=canal.mention, inline=True)
        embed.add_field(name="Status", value="Permissões restauradas ao padrão", inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    # 2. GARAGEM E VEÍCULOS
    async def handle_garagem(self, message):
        user = get_user(message.author.id)
        veiculo_id = user.get("veiculo")
        embed = discord.Embed(title="🚗 Garagem Imperial", color=COR_IMPERIAL)
        if veiculo_id and veiculo_id in CATALOGO_VEICULOS:
            v = CATALOGO_VEICULOS[veiculo_id]
            embed.add_field(name="Veículo Registrado", value=f"{v['emoji']} **{v['nome']}**", inline=True)
            embed.add_field(name="Redução de Cooldown", value=f"{int(v['reducao_trem']*100)}%", inline=True)
            embed.add_field(name="Descrição", value=v["descricao"], inline=False)
            embed.description = "*Seu veículo está registrado na garagem do condomínio.*"
        else:
            embed.description = "*Nenhum veículo registrado. Adquira um abaixo.*"
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = VisualizarVeiculos(message.author.id)
        await message.channel.send(embed=embed, view=view)

    async def handle_vender_veiculo(self, message):
        user = get_user(message.author.id)
        vid  = user.get("veiculo")
        if not vid or vid not in CATALOGO_VEICULOS:
            await message.channel.send(embed=embed_soberano("Sem Veículo", "Nenhum veículo registrado para venda.", COR_NEUTRO))
            return
        v = CATALOGO_VEICULOS[vid]
        reembolso = int(v["preco"] * 0.6)
        user["moedas"] = user.get("moedas", 0) + reembolso
        user["veiculo"] = None
        save_user(message.author.id, user)
        await message.channel.send(embed=embed_soberano(
            f"{v['emoji']} Veículo Vendido",
            f"**{v['nome']}** transferido por **{reembolso} moedas** (60% do valor original).",
            COR_SUCESSO
        ))

    # 3. ESPORTES NA QUADRA
    async def handle_esporte(self, message, args, esporte: str):
        if not message.mentions:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", f"Uso: `Tenshi, {esporte} @usuario`", COR_NEUTRO))
            return
        alvo = message.mentions[0]
        if alvo.id == message.author.id:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Você não pode desafiar a si mesmo.", COR_NEUTRO))
            return
        emoji = "🏀" if esporte == "basquete" else "⚽"
        embed = discord.Embed(
            title=f"{emoji} Desafio Esportivo — {esporte.capitalize()}",
            description=(
                f"**{message.author.display_name}** desafia **{alvo.display_name}** para uma partida de {esporte}.\n\n"
                f"{alvo.mention}, você aceita o desafio?"
            ),
            color=COR_IMPERIAL
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = JogoEsportivo(message.author, alvo, esporte)
        await message.channel.send(embed=embed, view=view)

    # 4. POOL PARTY
    async def handle_pool_party(self, message):
        try:
            tem_perm = message.author.guild_permissions.administrator
        except Exception:
            tem_perm = False
        from utils import IMPERADOR_ID
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_soberano("Acesso Negado", "Apenas administradores podem iniciar uma Pool Party.", COR_PERIGO))
            return
        guild_id = message.guild.id
        _pool_party_ativo[guild_id] = datetime.utcnow() + timedelta(hours=2)
        embed = discord.Embed(
            title="🏊 Pool Party Imperial",
            description=(
                "A piscina do condomínio está em modo festivo.\n\n"
                f"**Duração:** 2 horas\n"
                f"**Bônus:** +100% de moedas por interação nos canais da vizinhança\n\n"
                "*Todos os moradores com acesso ao canal recebem o bônus automaticamente.*"
            ),
            color=0x1E90FF
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send("@everyone", embed=embed)
        await asyncio.sleep(7200)
        if guild_id in _pool_party_ativo:
            del _pool_party_ativo[guild_id]
            await message.channel.send(embed=embed_soberano("Pool Party Encerrada", "O período de bônus foi encerrado. Remuneração retorna ao normal.", COR_NEUTRO))

    def is_pool_party_ativa(self, guild_id: int) -> bool:
        fim = _pool_party_ativo.get(guild_id)
        if fim and datetime.utcnow() < fim:
            return True
        if guild_id in _pool_party_ativo:
            del _pool_party_ativo[guild_id]
        return False

    # 5. PETS
    async def handle_petshop(self, message):
        embed = discord.Embed(
            title="🐾 Pet Shop Imperial",
            description="*Adquira um companheiro fiel para sua jornada no Império.*\n\nCada pet concede um bônus passivo exclusivo.",
            color=COR_IMPERIAL
        )
        for pid, p in CATALOGO_PETS.items():
            embed.add_field(
                name=f"{p['emoji']} {p['nome']} — {p['preco']} moedas",
                value=p["descricao"],
                inline=False
            )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = VisualizarPets(message.author.id)
        await message.channel.send(embed=embed, view=view)

    async def handle_meu_pet(self, message):
        user = get_user(message.author.id)
        pid  = user.get("pet")
        if not pid or pid not in CATALOGO_PETS:
            await message.channel.send(embed=embed_soberano("Sem Pet", "Nenhum pet registrado. Use `Tenshi, pet-shop` para adquirir.", COR_NEUTRO))
            return
        p = CATALOGO_PETS[pid]
        embed = discord.Embed(title=f"{p['emoji']} Seu Pet", color=COR_IMPERIAL)
        embed.add_field(name="Nome",    value=p["nome"],    inline=True)
        embed.add_field(name="Passivo", value=p["descricao"], inline=False)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_vender_pet(self, message):
        user = get_user(message.author.id)
        pid  = user.get("pet")
        if not pid or pid not in CATALOGO_PETS:
            await message.channel.send(embed=embed_soberano("Sem Pet", "Nenhum pet para vender.", COR_NEUTRO))
            return
        p = CATALOGO_PETS[pid]
        reembolso = int(p["preco"] * 0.5)
        user["moedas"] = user.get("moedas", 0) + reembolso
        user["pet"]    = None
        save_user(message.author.id, user)
        await message.channel.send(embed=embed_soberano(
            f"{p['emoji']} Pet Vendido",
            f"**{p['nome']}** foi vendido por **{reembolso} moedas**.",
            COR_SUCESSO
        ))

    # ── AUXILIAR ──────────────────────────────────────────────────────────────
    async def _get_canal_casa(self, guild, numero: int):
        if not guild:
            return None
        viz = get_vizinhanca()
        canal_id = viz.get(str(numero), {}).get("id_canal")
        if canal_id:
            c = guild.get_channel(int(canal_id))
            if c:
                return c
        for ch in guild.text_channels:
            if ch.name.lower() == f"casa-{numero}":
                return ch
        return None
