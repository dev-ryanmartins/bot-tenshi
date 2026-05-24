"""
Módulo Social — Funcionalidades 6-9
6. Casamento e Divórcio
7. Lavanderia (limpeza de itens)
8. Laboratório (síntese de itens)
9. Cinema e agendamento
"""
import discord
import asyncio
import random
from datetime import datetime, timedelta
from database import get_user, save_user, get_casamentos, save_casamentos
from utils import SEP, RODAPE_IMPERIAL, IMPERADOR_ID

COR_IMPERIAL = 0x2C3E50
COR_DOURADO  = 0x9E7815
COR_PRETO    = 0x111111
COR_SUCESSO  = 0x1A5C2E
COR_PERIGO   = 0x7B1F1F
COR_NEUTRO   = 0x3D3D3D

def embed_soberano(titulo: str, descricao: str, cor: int = COR_IMPERIAL) -> discord.Embed:
    e = discord.Embed(title=titulo, description=descricao, color=cor)
    e.set_footer(text=RODAPE_IMPERIAL)
    return e


# ─── CASAMENTO ────────────────────────────────────────────────────────────────
class VotosView(discord.ui.View):
    def __init__(self, noivo1: discord.Member, noivo2: discord.Member):
        super().__init__(timeout=300)
        self.noivo1      = noivo1
        self.noivo2      = noivo2
        self.aceites     = set()
        self.recusas     = set()
        self.encerrado   = False

    @discord.ui.button(label="Aceito", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.noivo1.id, self.noivo2.id):
            await interaction.response.send_message("Este protocolo não lhe diz respeito.", ephemeral=True)
            return
        if self.encerrado:
            return
        self.aceites.add(interaction.user.id)
        await interaction.response.send_message(f"*{interaction.user.display_name} confirmou os votos.*", ephemeral=True)
        if len(self.aceites) == 2:
            self.encerrado = True
            await self._oficializar(interaction)

    @discord.ui.button(label="Recuso", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.noivo1.id, self.noivo2.id):
            await interaction.response.send_message("Painel restrito.", ephemeral=True)
            return
        if self.encerrado:
            return
        self.encerrado = True
        self.clear_items()
        await interaction.response.edit_message(
            embed=embed_soberano(
                "Protocolo Encerrado",
                f"*{interaction.user.display_name}* optou por não prosseguir com a cerimônia.\nO protocolo de casamento foi cancelado formalmente.",
                COR_NEUTRO
            ),
            view=self
        )

    async def _oficializar(self, interaction: discord.Interaction):
        self.clear_items()
        casamentos = get_casamentos()
        cid = f"{min(self.noivo1.id, self.noivo2.id)}_{max(self.noivo1.id, self.noivo2.id)}"
        casamentos[cid] = {
            "noivo1": str(self.noivo1.id),
            "noivo2": str(self.noivo2.id),
            "data":   datetime.utcnow().isoformat(),
        }
        save_casamentos(casamentos)
        u1 = get_user(self.noivo1.id)
        u2 = get_user(self.noivo2.id)
        u1["conjuge"]     = str(self.noivo2.id)
        u2["conjuge"]     = str(self.noivo1.id)
        u1["taxa_casa_divisao"] = True
        u2["taxa_casa_divisao"] = True
        # Cônjuge do Imperador recebe acesso executivo
        if self.noivo1.id == IMPERADOR_ID or self.noivo2.id == IMPERADOR_ID:
            conjuge_id = self.noivo2.id if self.noivo1.id == IMPERADOR_ID else self.noivo1.id
            conj_user  = get_user(conjuge_id)
            conj_user["co_soberano"] = True
            save_user(conjuge_id, conj_user)
        save_user(self.noivo1.id, u1)
        save_user(self.noivo2.id, u2)
        embed = discord.Embed(
            title="⚜ Certidão Imperial de União",
            description=(
                f"*Pelo poder conferido pelo Oráculo e pela lei do Império de Tenshi...*\n{SEP}\n\n"
                f"Fica aqui registrada a união oficial entre:\n\n"
                f"**{self.noivo1.display_name}** e **{self.noivo2.display_name}**\n\n"
                f"*Que esta aliança fortaleça o Império e persista além das eras.*\n{SEP}\n\n"
                f"📋 **Data:** {datetime.utcnow().strftime('%d/%m/%Y')}\n"
                f"💰 **Benefício:** Taxa de condomínio dividida entre os cônjuges\n"
                f"🏛️ **Registro:** Arquivado nos Pergaminhos Imortais de Tenshi"
            ),
            color=COR_DOURADO
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await interaction.response.edit_message(embed=embed, view=self)


# ─── LAVANDERIA ───────────────────────────────────────────────────────────────
TAXA_LAVAGEM = 30

class LavanderiaView(discord.ui.View):
    def __init__(self, user_id: int, itens_sujos: list):
        super().__init__(timeout=60)
        self.user_id    = user_id
        self.itens_sujos = itens_sujos
        for item in itens_sujos[:5]:
            b = discord.ui.Button(
                label=f"Lavar: {item.get('nome', item.get('id', '?'))} — {TAXA_LAVAGEM}💰",
                style=discord.ButtonStyle.secondary
            )
            b.callback = self._make_cb(item)
            self.add_item(b)

    def _make_cb(self, item: dict):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("Painel restrito.", ephemeral=True)
                return
            user = get_user(interaction.user.id)
            if user["moedas"] < TAXA_LAVAGEM:
                await interaction.response.send_message(
                    embed=embed_soberano("Saldo Insuficiente", f"Taxa de lavagem: {TAXA_LAVAGEM} moedas.", COR_PERIGO),
                    ephemeral=True
                )
                return
            user["moedas"] -= TAXA_LAVAGEM
            for it in user.get("inventario", []):
                if it.get("id") == item.get("id"):
                    it["sujo"] = False
            save_user(interaction.user.id, user)
            await interaction.response.send_message(
                embed=embed_soberano("Item Limpo", f"**{item.get('nome', item.get('id'))}** foi lavado e restaurado.", COR_SUCESSO),
                ephemeral=True
            )
        return callback


# ─── LABORATÓRIO ─────────────────────────────────────────────────────────────
RECEITAS_SINTETIZAR = {
    "implante_neural":    {"nome": "Implante Neural",      "custo": 400, "bonus": {"poder": 30}, "req_clube": "clube-de-ciências"},
    "pocao_mutagenica":   {"nome": "Poção Mutagênica",     "custo": 300, "bonus": {"poder": 20, "vida": 20}},
    "armadura_runica":    {"nome": "Armadura Rúnica",      "custo": 600, "bonus": {"poder": 50, "defesa": 20}},
    "elixir_velocidade":  {"nome": "Elixir de Velocidade", "custo": 250, "bonus": {"agilidade": 30}},
}


# ─── CINEMA ────────────────────────────────────────────────────────────────────
_sessoes_cinema: dict = {}

class PresencaCinemaView(discord.ui.View):
    def __init__(self, filme: str, horario: datetime, canal_notif):
        super().__init__(timeout=3600)
        self.filme       = filme
        self.horario     = horario
        self.canal_notif = canal_notif
        self.confirmados = []

    @discord.ui.button(label="Confirmar Presença", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [u.id for u in self.confirmados]:
            self.confirmados.append(interaction.user)
        await interaction.response.send_message(
            embed=embed_soberano("Presença Confirmada", f"Sua presença para **{self.filme}** foi registrada.", COR_SUCESSO),
            ephemeral=True
        )

    @discord.ui.button(label="Cancelar Presença", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmados = [u for u in self.confirmados if u.id != interaction.user.id]
        await interaction.response.send_message("Presença cancelada.", ephemeral=True)


# ─── COG PRINCIPAL ────────────────────────────────────────────────────────────
class Social:
    def __init__(self, bot):
        self.bot = bot

    # 6. CASAR
    async def handle_casar(self, message, args):
        if not message.mentions:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Uso: `Tenshi, casar @usuario`", COR_NEUTRO))
            return
        alvo = message.mentions[0]
        if alvo.id == message.author.id:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Você não pode contrair matrimônio consigo mesmo.", COR_NEUTRO))
            return
        u1 = get_user(message.author.id)
        u2 = get_user(alvo.id)
        if u1.get("conjuge") or u2.get("conjuge"):
            await message.channel.send(embed=embed_soberano("Protocolo Inválido", "Um dos participantes já está em união registrada.", COR_PERIGO))
            return
        embed = discord.Embed(
            title="⚜ Protocolo de Casamento Imperial",
            description=(
                f"*O Oráculo de Tenshi foi invocado para presidir esta cerimônia...*\n{SEP}\n\n"
                f"**{message.author.display_name}** declara sua intenção de união com **{alvo.display_name}**.\n\n"
                f"*Que ambos confirmem sua vontade soberana abaixo.*\n\n"
                f"{message.author.mention} e {alvo.mention}, este é um ato irrevogável. Procedam com clareza de propósito."
            ),
            color=COR_DOURADO
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = VotosView(message.author, alvo)
        await message.channel.send(embed=embed, view=view)

    # DIVÓRCIO
    async def handle_divorcio(self, message):
        user = get_user(message.author.id)
        conjuge_id = user.get("conjuge")
        if not conjuge_id:
            await message.channel.send(embed=embed_soberano("Sem Registro", "Não há registro de união para este membro.", COR_NEUTRO))
            return
        custo = int((user.get("moedas", 0) + user.get("conta_banco", 0)) * 0.5)
        if user["moedas"] < custo:
            custo = user["moedas"]
        user["moedas"]  = user.get("moedas", 0) - custo
        user["conjuge"] = None
        user["taxa_casa_divisao"] = False
        user["co_soberano"] = False
        save_user(message.author.id, user)
        conj = get_user(int(conjuge_id))
        conj["conjuge"]   = None
        conj["taxa_casa_divisao"] = False
        conj["co_soberano"] = False
        save_user(int(conjuge_id), conj)
        casamentos = get_casamentos()
        cid1 = f"{min(message.author.id, int(conjuge_id))}_{max(message.author.id, int(conjuge_id))}"
        if cid1 in casamentos:
            del casamentos[cid1]
            save_casamentos(casamentos)
        await message.channel.send(embed=embed_soberano(
            "Registro de Dissolução Matrimonial",
            f"A união entre {message.author.mention} e <@{conjuge_id}> foi dissolvida formalmente.\n\n"
            f"**Custo processual:** {custo} moedas (50% do saldo disponível).\n\n"
            f"*O registro foi removido dos Pergaminhos Imortais.*",
            COR_NEUTRO
        ))

    # 7. LAVANDERIA
    async def handle_lavanderia(self, message):
        user = get_user(message.author.id)
        itens_sujos = [it for it in user.get("inventario", []) if it.get("sujo")]
        if not itens_sujos:
            await message.channel.send(embed=embed_soberano(
                "Lavanderia Imperial",
                "Todos os seus itens estão limpos. Nenhuma lavagem necessária.",
                COR_IMPERIAL
            ))
            return
        embed = discord.Embed(
            title="👕 Lavanderia Imperial",
            description=f"*{len(itens_sujos)} item(s) com eficácia reduzida por uso em batalha ou hospital.*\n\nSelecione os itens para lavar:",
            color=COR_IMPERIAL
        )
        embed.add_field(name="Taxa por Item", value=f"{TAXA_LAVAGEM} moedas", inline=True)
        embed.add_field(name="Saldo Atual",   value=f"{user['moedas']} moedas", inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = LavanderiaView(message.author.id, itens_sujos)
        await message.channel.send(embed=embed, view=view)

    # 8. LABORATÓRIO — SINTETIZAR
    async def handle_sintetizar(self, message, args):
        if not args:
            embed = discord.Embed(title="⚗️ Laboratório Imperial — Receitas", color=COR_IMPERIAL)
            for rid, r in RECEITAS_SINTETIZAR.items():
                embed.add_field(
                    name=f"{r['nome']} — {r['custo']} moedas",
                    value=f"Uso: `Tenshi, sintetizar {rid}`" + (f"\n*Req: {r.get('req_clube','')}*" if r.get("req_clube") else ""),
                    inline=False
                )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return
        item_id = args[0].lower()
        if item_id not in RECEITAS_SINTETIZAR:
            await message.channel.send(embed=embed_soberano("Item Não Encontrado", f"Receita `{item_id}` não catalogada.", COR_NEUTRO))
            return
        receita = RECEITAS_SINTETIZAR[item_id]
        user = get_user(message.author.id)
        if receita.get("req_clube"):
            clubes = user.get("clubes", [])
            if receita["req_clube"] not in clubes:
                await message.channel.send(embed=embed_soberano("Acesso Negado", f"Você precisa ser membro do **{receita['req_clube']}** para sintetizar este item.", COR_PERIGO))
                return
        if user["moedas"] < receita["custo"]:
            await message.channel.send(embed=embed_soberano("Saldo Insuficiente", f"Custo: {receita['custo']} moedas.", COR_PERIGO))
            return
        user["moedas"] -= receita["custo"]
        for attr, val in receita["bonus"].items():
            if attr == "poder":
                user["poder"] = user.get("poder", 100) + val
            elif attr in user.get("atributos", {}):
                user["atributos"][attr] += val
        user.setdefault("inventario", []).append({
            "id": item_id, "nome": receita["nome"],
            "sintetizado": True, "data": datetime.utcnow().isoformat()
        })
        save_user(message.author.id, user)
        embed = discord.Embed(title="⚗️ Síntese Concluída", color=COR_SUCESSO)
        embed.add_field(name="Item", value=receita["nome"], inline=True)
        embed.add_field(name="Custo", value=f"{receita['custo']} moedas", inline=True)
        bonus_txt = "  |  ".join(f"+{v} {k}" for k, v in receita["bonus"].items())
        embed.add_field(name="Bônus Aplicado", value=bonus_txt, inline=False)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    # 9. CINEMA
    async def handle_cartaz(self, message, args):
        if not args:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Uso: `Tenshi, cartaz [nome do filme]`", COR_NEUTRO))
            return
        filme = " ".join(args)
        horario = datetime.utcnow() + timedelta(hours=1)
        embed = discord.Embed(
            title="🎬 Sessão Agendada",
            description=(
                f"**Título:** {filme}\n"
                f"**Data/Hora:** {horario.strftime('%d/%m/%Y — %H:%M')} UTC\n"
                f"**Local:** Canal de Voz — Festa/Call\n\n"
                f"Confirme sua presença abaixo. Você receberá uma notificação 10 minutos antes."
            ),
            color=COR_IMPERIAL
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = PresencaCinemaView(filme, horario, message.channel)
        msg  = await message.channel.send(embed=embed, view=view)
        _sessoes_cinema[msg.id] = {"filme": filme, "horario": horario, "view": view, "canal": message.channel}
        self.bot.loop.create_task(self._notificar_cinema(view, filme, horario, message.channel))

    async def _notificar_cinema(self, view: PresencaCinemaView, filme: str, horario: datetime, canal):
        await asyncio.sleep(max(0, (horario - timedelta(minutes=10) - datetime.utcnow()).total_seconds()))
        if view.confirmados:
            mencoes = " ".join(u.mention for u in view.confirmados)
            await canal.send(
                content=mencoes,
                embed=embed_soberano(
                    "🎬 Sessão em 10 Minutos",
                    f"A sessão de **{filme}** começará em 10 minutos.\n\n*Dirija-se ao canal de voz designado.*",
                    COR_DOURADO
                )
            )

from datetime import datetime
