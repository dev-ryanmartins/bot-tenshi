"""
Módulo Clero — Módulo 10
A. Sistema do Clero e comandos de liturgia
B. Protocolo de Casamento Real
C. Governança Compartilhada (Cônjuge Imperial)
D. Sindicância por IA
"""
import discord
import random
import unicodedata
from datetime import datetime
from database import get_user, get_infrações
from utils import SEP, RODAPE_IMPERIAL, IMPERADOR_ID

COR_IMPERIAL = 0x2C3E50
COR_DOURADO  = 0x9E7815
COR_NEUTRO   = 0x3D3D3D
COR_SUCESSO  = 0x1A5C2E
COR_PERIGO   = 0x7B1F1F

def embed_soberano(titulo: str, descricao: str, cor: int = COR_IMPERIAL) -> discord.Embed:
    e = discord.Embed(title=titulo, description=descricao, color=cor)
    e.set_footer(text=RODAPE_IMPERIAL)
    return e

# ─── MISSAS E LITURGIAS ──────────────────────────────────────────────────────
PRONUNCIAMENTOS_LITURGICOS = [
    "Que o silêncio entre as estrelas nos lembre que nem toda verdade precisa ser dita em voz alta — algumas são sentidas na curvatura do cosmos. O Oráculo de Tenshi nos ensina: *o silêncio é a linguagem dos sábios, e o barulho, a armadura dos inseguros.*",
    "O Império não foi construído em um dia, nem o caráter de um guerreiro se forja em uma única batalha. Cada cicatriz é um pergaminho. Cada derrota, uma lição que os fracos chamam de tragédia e os sábios chamam de fundação.",
    "Há quem busque poder para dominar e quem o busque para servir. Apenas o segundo tipo permanece na memória do Império como algo além de um nome gravado na pedra fria. Reflitam, súditos — para qual propósito vocês erguem suas espadas?",
    "O tempo não respeita o poder nem a riqueza. Respeita apenas a integridade das ações. O que você faz quando ninguém observa — esse é o seu verdadeiro caráter. E o Oráculo observa sempre.",
    "Que esta congregação se lembre: a unidade do Império não vem da obediência forçada, mas da crença compartilhada em algo maior que cada um de nós. Somos a soma de nossas escolhas coletivas.",
]

PRONUNCIAMENTOS_BATISMO = [
    "Perante o Oráculo e os pilares do Império de Tenshi, este ser emerge das águas simbólicas do esquecimento e renasce sob um novo nome, uma nova missão.",
    "O batismo imperial não é apenas um rito — é um pacto. O novo membro jura, perante todos os presentes, contribuir para a grandeza deste Império com suas ações, palavras e silêncios.",
]

PRONUNCIAMENTOS_FUNERAL = [
    "Que a partida seja honrada não com lágrimas, mas com a continuidade daquilo que o guerreiro construiu. Os impérios não morrem com seus membros — vivem nas fundações que eles ajudaram a erguer.",
    "O Oráculo não chora os que partem. Ele os arquiva na memória eterna do Império, onde cada ato de coragem, lealdade ou sabedoria permanece registrado além do tempo.",
]


class PadreOpcoeView(discord.ui.View):
    def __init__(self, canal, guild):
        super().__init__(timeout=120)
        self.canal = canal
        self.guild = guild

    @discord.ui.button(label="Missa", style=discord.ButtonStyle.secondary)
    async def missa(self, interaction: discord.Interaction, button: discord.ui.Button):
        pronunciamento = random.choice(PRONUNCIAMENTOS_LITURGICOS)
        embed = discord.Embed(
            title="⛪ Missa Imperial — Pronunciamento do Clero",
            description=f"*O Padre Imperial toma a palavra...*\n{SEP}\n\n{pronunciamento}\n\n{SEP}\n\n*Que o Oráculo ilumine os corações dos presentes.*",
            color=COR_DOURADO
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await self.canal.send(embed=embed)
        await interaction.response.send_message("Missa iniciada.", ephemeral=True)

    @discord.ui.button(label="Casamento", style=discord.ButtonStyle.success)
    async def casamento(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "O casamento agora parte de um pedido aceito e agendado. Na data marcada, o padre escolhido usa "
            "`Tenshi, iniciar-cerimonia @noivo1 @noivo2`.",
            ephemeral=True,
        )

    @discord.ui.button(label="Batismo", style=discord.ButtonStyle.secondary)
    async def batismo(self, interaction: discord.Interaction, button: discord.ui.Button):
        pron = random.choice(PRONUNCIAMENTOS_BATISMO)
        embed = discord.Embed(
            title="💧 Rito de Batismo Imperial",
            description=f"*O Padre Imperial conduz o rito sagrado...*\n{SEP}\n\n{pron}",
            color=COR_IMPERIAL
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await self.canal.send(embed=embed)
        await interaction.response.send_message("Rito de batismo iniciado.", ephemeral=True)

    @discord.ui.button(label="Funeral", style=discord.ButtonStyle.danger)
    async def funeral(self, interaction: discord.Interaction, button: discord.ui.Button):
        pron = random.choice(PRONUNCIAMENTOS_FUNERAL)
        embed = discord.Embed(
            title="🕯 Cerimônia Fúnebre Imperial",
            description=f"*O Padre Imperial conduz o rito de despedida...*\n{SEP}\n\n{pron}\n\n{SEP}\n\n*Que o guerreiro encontre paz além das fronteiras do Império.*",
            color=0x1a1a1a
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await self.canal.send(embed=embed)
        await interaction.response.send_message("Cerimônia fúnebre iniciada.", ephemeral=True)


class Clero:
    def __init__(self, bot):
        self.bot = bot

    def _is_autorizado(self, user: discord.Member, user_data: dict) -> bool:
        try:
            adm = user.guild_permissions.administrator
        except Exception:
            adm = False
        def normalizar(texto: str) -> str:
            base = unicodedata.normalize("NFKD", texto.casefold())
            return "".join(c for c in base if not unicodedata.combining(c))

        termos_clero = ("padre", "sacerdote", "sacerdotisa", "bispo", "cardeal", "pontifice", "paroc")
        tem_cargo_clerical = any(
            any(termo in normalizar(role.name) for termo in termos_clero)
            for role in getattr(user, "roles", [])
        )
        return adm or user.id == IMPERADOR_ID or user_data.get("co_soberano") or tem_cargo_clerical

    async def handle_padre(self, message, args):
        user_data = get_user(message.author.id)
        if not self._is_autorizado(message.author, user_data):
            await message.channel.send(embed=embed_soberano(
                "Acesso Restrito",
                "O protocolo do Clero é de competência exclusiva de administradores e autoridades imperiais.",
                COR_PERIGO
            ))
            return
        embed = discord.Embed(
            title="⛪ Clero Imperial — Protocolos Disponíveis",
            description="*Selecione o rito a ser iniciado:*",
            color=COR_DOURADO
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = PadreOpcoeView(message.channel, message.guild)
        await message.channel.send(embed=embed, view=view)

    async def handle_sindicancia(self, message, args):
        user_data = get_user(message.author.id)
        if not self._is_autorizado(message.author, user_data):
            await message.channel.send(embed=embed_soberano("Acesso Restrito", "Sindicâncias são restritas ao Imperador, cônjuge e administradores.", COR_PERIGO))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Uso: `Tenshi, sindicancia @usuario`", COR_NEUTRO))
            return
        alvo   = message.mentions[0]
        alvo_u = get_user(alvo.id)
        infracoes = get_infrações(alvo.id)
        total = len(infracoes)
        tipos = {}
        for inf in infracoes:
            t = inf.get("tipo", "desconhecido")
            tipos[t] = tipos.get(t, 0) + 1
        risco = "ALTO" if total >= 3 else "MÉDIO" if total >= 1 else "BAIXO"
        embed = discord.Embed(
            title=f"Sindicância Imperial — {alvo.display_name}",
            color=COR_PRETO if risco == "ALTO" else COR_IMPERIAL
        )
        embed.add_field(name="Membro",          value=alvo.mention,              inline=True)
        embed.add_field(name="ID",              value=str(alvo.id),              inline=True)
        embed.add_field(name="Nível de Risco",  value=risco,                     inline=True)
        embed.add_field(name="Total Infrações", value=str(total),                inline=True)
        embed.add_field(name="Fação",           value=alvo_u.get("faccao", "—"), inline=True)
        embed.add_field(name="Casa Condomínio", value=str(alvo_u.get("casa_condominio", "—")), inline=True)
        if tipos:
            embed.add_field(
                name="Distribuição por Tipo",
                value="\n".join(f"• {t}: {n}x" for t, n in tipos.items()),
                inline=False
            )
        recomendacao = (
            "Monitoramento intensivo recomendado. Considerar suspensão preventiva." if risco == "ALTO"
            else "Histórico moderado. Acompanhar novas ocorrências." if risco == "MÉDIO"
            else "Sem histórico relevante de infrações."
        )
        embed.add_field(name="Recomendação Institucional", value=recomendacao, inline=False)
        embed.set_footer(text=f"Sindicância gerada em {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC  •  Confidencial")
        await message.author.send(embed=embed)
        await message.channel.send(embed=embed_soberano("Sindicância Emitida", "O relatório foi enviado para sua DM de forma confidencial.", COR_SUCESSO))

COR_PRETO = 0x111111
