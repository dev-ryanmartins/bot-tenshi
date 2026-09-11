"""
Módulo Correio — Funcionalidade 17
17. Correio Elegante Anônimo
"""
import discord
import asyncio
from datetime import datetime
from database import get_user, save_user
from utils import SEP, RODAPE_IMPERIAL

COR_IMPERIAL = 0x2C3E50
COR_DOURADO  = 0x9E7815
COR_NEUTRO   = 0x3D3D3D
COR_SUCESSO  = 0x1A5C2E
COR_PERIGO   = 0x7B1F1F

PALAVRAS_BLOQUEADAS = [
    "http://", "https://", ".com", ".gg", "discord.gg", "@everyone", "@here",
    "racismo", "nazismo", "ódio", "matar", "morte a",
]

def embed_soberano(titulo: str, descricao: str, cor: int = COR_IMPERIAL) -> discord.Embed:
    e = discord.Embed(title=titulo, description=descricao, color=cor)
    e.set_footer(text=RODAPE_IMPERIAL)
    return e

def _verificar_conteudo(texto: str) -> tuple[bool, str]:
    t = texto.lower()
    for palavra in PALAVRAS_BLOQUEADAS:
        if palavra in t:
            return False, f"Conteúdo retido por violação de diretriz: termo proibido detectado."
    if len(texto) > 800:
        return False, "Mensagem excede o limite de 800 caracteres."
    return True, "ok"


class RedigirCartaModal(discord.ui.Modal, title="Redigir Correspondência Imperial"):
    mensagem = discord.ui.TextInput(
        label="Conteúdo da correspondência",
        style=discord.TextStyle.paragraph,
        max_length=800,
        required=True,
        placeholder="Escreva sua mensagem aqui..."
    )

    def __init__(self, destinatario: discord.Member, canal_anonimo, canal_logs, remetente_id: int):
        super().__init__()
        self.destinatario  = destinatario
        self.canal_anonimo = canal_anonimo
        self.canal_logs    = canal_logs
        self.remetente_id  = remetente_id

    async def on_submit(self, interaction: discord.Interaction):
        texto = self.mensagem.value
        ok, motivo = _verificar_conteudo(texto)
        if not ok:
            await interaction.response.send_message(
                embed=embed_soberano("Correspondência Retida", motivo, COR_PERIGO),
                ephemeral=True
            )
            return
        # Enviar como carta anônima
        embed_carta = discord.Embed(
            title="Correspondência Imperial",
            description=(
                f"*Uma carta lacrada chegou pelos canais imperiais...*\n{SEP}\n\n"
                f"{texto}\n\n{SEP}\n\n"
                f"**Destinatário:** {self.destinatario.mention}\n"
                f"**Remetente:** *Identidade preservada*"
            ),
            color=COR_DOURADO
        )
        embed_carta.set_footer(text="Correio Anônimo Imperial  •  Tenshi")
        try:
            await self.canal_anonimo.send(
                content=self.destinatario.mention,
                embed=embed_carta
            )
        except Exception:
            await interaction.response.send_message(
                embed=embed_soberano("Erro de Entrega", "Não foi possível enviar ao canal de correio.", COR_PERIGO),
                ephemeral=True
            )
            return
        # Log para staff
        if self.canal_logs:
            embed_log = discord.Embed(
                title="Log de Correio — Confidencial Staff",
                color=COR_NEUTRO
            )
            embed_log.add_field(name="Remetente (ID)",  value=str(self.remetente_id),            inline=True)
            embed_log.add_field(name="Destinatário",    value=self.destinatario.display_name,    inline=True)
            embed_log.add_field(name="Data/Hora",       value=datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC'), inline=True)
            embed_log.add_field(name="Conteúdo",        value=f"```{texto[:500]}```",             inline=False)
            embed_log.add_field(name="Status de Triagem", value="Aprovado — sem violações detectadas", inline=False)
            embed_log.set_footer(text="Sistema de Auditoria  •  Confidencial")
            try:
                await self.canal_logs.send(embed=embed_log)
            except Exception:
                pass
        await interaction.response.send_message(
            embed=embed_soberano("Carta Enviada", "Sua correspondência foi despachada de forma anônima.", COR_SUCESSO),
            ephemeral=True
        )


class CorreioPainelView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        self.guild = guild

    @discord.ui.button(label="Redigir Carta Anônima", style=discord.ButtonStyle.secondary, custom_id="correio_redigir")
    async def redigir(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_anonimo = None
        canal_logs    = None
        for ch in self.guild.text_channels:
            if "correio-anônimo" in ch.name.lower() or "correio-anonimo" in ch.name.lower():
                canal_anonimo = ch
            if "logs-correio" in ch.name.lower():
                canal_logs = ch

        seletor = DestinatarioSelect(canal_anonimo, canal_logs, interaction.user.id, self.guild)
        view = discord.ui.View(timeout=60)
        view.add_item(seletor)
        await interaction.response.send_message(
            embed=embed_soberano(
                "Selecionar Destinatário",
                "Escolha o destinatário da correspondência no menu abaixo.",
                COR_IMPERIAL
            ),
            view=view,
            ephemeral=True
        )


class DestinatarioSelect(discord.ui.UserSelect):
    def __init__(self, canal_anonimo, canal_logs, remetente_id: int, guild: discord.Guild):
        super().__init__(placeholder="Selecione o destinatário...", min_values=1, max_values=1)
        self.canal_anonimo = canal_anonimo
        self.canal_logs    = canal_logs
        self.remetente_id  = remetente_id
        self.guild         = guild

    async def callback(self, interaction: discord.Interaction):
        destinatario = self.values[0]
        if destinatario.id == self.remetente_id:
            await interaction.response.send_message("Você não pode enviar uma carta a si mesmo.", ephemeral=True)
            return
        modal = RedigirCartaModal(destinatario, self.canal_anonimo, self.canal_logs, self.remetente_id)
        await interaction.response.send_modal(modal)


class Correio:
    def __init__(self, bot):
        self.bot = bot

    async def handle_criar_correio(self, message):
        embed = discord.Embed(
            title="Central de Correio Imperial",
            description=(
                f"*Suas mensagens chegam ao destino sem revelar sua identidade.*\n{SEP}\n\n"
                f"**Protocolo de segurança ativo:**\n"
                f"• Triagem automática de conteúdo proibido\n"
                f"• Identidade do remetente preservada\n"
                f"• Log auditado pela staff via #logs-correio\n\n"
                f"Utilize o botão abaixo para redigir sua correspondência."
            ),
            color=COR_DOURADO
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = CorreioPainelView(message.guild)
        await message.channel.send(embed=embed, view=view)
