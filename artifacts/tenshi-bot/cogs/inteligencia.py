"""
Módulo Inteligência — Módulo 11
A. Espionagem e Contrabando
B. Monitoramento de Chamadas de Voz
C. Sistema de Festas Automatizado
D. Jornalismo Investigativo / Pérolas do RP
E. Correio — integração de logs (ver correio.py)
"""
import discord
import asyncio
import random
from datetime import datetime, timedelta
from database import get_user, save_user, get_vizinhanca, save_vizinhanca
from utils import SEP, RODAPE_IMPERIAL, IMPERADOR_ID

COR_IMPERIAL = 0x2C3E50
COR_PRETO    = 0x111111
COR_DOURADO  = 0x9E7815
COR_NEUTRO   = 0x3D3D3D
COR_SUCESSO  = 0x1A5C2E
COR_PERIGO   = 0x7B1F1F

def embed_soberano(titulo: str, descricao: str, cor: int = COR_IMPERIAL) -> discord.Embed:
    e = discord.Embed(title=titulo, description=descricao, color=cor)
    e.set_footer(text=RODAPE_IMPERIAL)
    return e

CUSTO_SUBORNO  = 500
CUSTO_GRAMPO   = 300
DURACAO_ESPIAO = 3600  # 1 hora

_espionagens_ativas: dict = {}
_grampos_ativos:     dict = {}
_voice_times:        dict = {}

# ─── VERDADE OU DESAFIO ───────────────────────────────────────────────────────
VERDADES = [
    "Qual é o seu maior arrependimento no Império de Tenshi?",
    "Você já traiu a confiança de alguém neste servidor? Descreva sem citar nomes.",
    "Se pudesse mudar algo na história do Império, o que seria?",
    "Qual membro deste servidor você mais admira e por quê?",
    "Qual foi a missão ou evento do Império que mais te marcou?",
]
DESAFIOS = [
    "Escreva um haiku sobre o Imperador Alloy em 5-7-5 sílabas.",
    "Descreva seu personagem em exatamente 3 palavras.",
    "Invente um novo cargo imperial e suas responsabilidades em 2 linhas.",
    "Escreva a frase de abertura do seu testamento imperial.",
    "Desafio: mude sua bio por 1 hora para algo relacionado ao Império.",
]


class VerdadeOuDesafioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verdade", style=discord.ButtonStyle.secondary, custom_id="vdd_verdade")
    async def verdade(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = random.choice(VERDADES)
        await interaction.response.send_message(
            embed=embed_soberano("Verdade", q, COR_IMPERIAL),
            ephemeral=False
        )

    @discord.ui.button(label="Desafio", style=discord.ButtonStyle.danger, custom_id="vdd_desafio")
    async def desafio(self, interaction: discord.Interaction, button: discord.ui.Button):
        d = random.choice(DESAFIOS)
        await interaction.response.send_message(
            embed=embed_soberano("Desafio", d, COR_PERIGO),
            ephemeral=False
        )


class Inteligencia:
    def __init__(self, bot):
        self.bot = bot
        self._voz_iniciada = False

    def cog_load(self):
        if not self._voz_iniciada:
            self._voz_iniciada = True
            self.bot.loop.create_task(self._loop_voz_passivo())

    # A. SUBORNAR PORTEIRO — espionar canal de casa por 1h
    async def handle_subornar_porteiro(self, message, args):
        if not args:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Uso: `Tenshi, subornar-porteiro Casa-X`", COR_NEUTRO))
            return
        try:
            numero = int("".join(c for c in args[0] if c.isdigit()))
        except Exception:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Informe o número da casa corretamente. Ex: `Casa-5`", COR_NEUTRO))
            return
        user = get_user(message.author.id)
        if user["moedas"] < CUSTO_SUBORNO:
            await message.channel.send(embed=embed_soberano("Saldo Insuficiente", f"Suborno exige {CUSTO_SUBORNO} moedas.", COR_PERIGO))
            return
        viz = get_vizinhanca()
        dados_casa = viz.get(str(numero), {})
        canal_id   = dados_casa.get("id_canal")
        canal      = None
        if canal_id and message.guild:
            canal = message.guild.get_channel(int(canal_id))
        if not canal and message.guild:
            for ch in message.guild.text_channels:
                if ch.name.lower() == f"casa-{numero}":
                    canal = ch
                    break
        if not canal:
            await message.channel.send(embed=embed_soberano("Canal Não Localizado", f"Canal casa-{numero} não encontrado.", COR_NEUTRO))
            return
        membro = message.guild.get_member(message.author.id)
        user["moedas"] -= CUSTO_SUBORNO
        save_user(message.author.id, user)
        try:
            await canal.set_permissions(membro, read_messages=True, send_messages=False)
        except Exception:
            await message.channel.send(embed=embed_soberano("Erro de Permissão", "Não foi possível liberar o acesso.", COR_PERIGO))
            return
        _espionagens_ativas[f"{message.author.id}_{numero}"] = datetime.utcnow() + timedelta(seconds=DURACAO_ESPIAO)
        await message.channel.send(embed=embed_soberano(
            "Acesso Temporário Liberado",
            f"Acesso de leitura ao canal casa-{numero} liberado por 1 hora.\n\n**Custo:** {CUSTO_SUBORNO} moedas.",
            COR_PRETO
        ))
        await asyncio.sleep(DURACAO_ESPIAO)
        try:
            await canal.set_permissions(membro, overwrite=None)
        except Exception:
            pass
        key = f"{message.author.id}_{numero}"
        if key in _espionagens_ativas:
            del _espionagens_ativas[key]

    # A. GRAMPEAR CALL
    async def handle_grampear_call(self, message):
        user = get_user(message.author.id)
        if user["moedas"] < CUSTO_GRAMPO:
            await message.channel.send(embed=embed_soberano("Saldo Insuficiente", f"Grampo exige {CUSTO_GRAMPO} moedas.", COR_PERIGO))
            return
        user["moedas"] -= CUSTO_GRAMPO
        save_user(message.author.id, user)
        if not message.guild:
            return
        relatorio = []
        for vc in message.guild.voice_channels:
            membros = [m.display_name for m in vc.members if not m.bot]
            if membros:
                relatorio.append(f"**{vc.name}:** {', '.join(membros)}")
        embed = discord.Embed(
            title="Relatório de Chamadas — Grampo Imperial",
            description=f"*Snapshot registrado em {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}*\n{SEP}\n\n" + ("\n".join(relatorio) or "*Nenhum canal de voz com membros ativos.*"),
            color=COR_PRETO
        )
        embed.set_footer(text="Inteligência Imperial  •  Confidencial")
        await message.author.send(embed=embed)
        await message.channel.send(embed=embed_soberano("Grampo Executado", "Relatório de chamadas enviado para sua DM.", COR_SUCESSO))

    # C. FESTAS
    async def handle_iniciar_festa(self, message, args):
        try:
            adm = message.author.guild_permissions.administrator
        except Exception:
            adm = False
        if not adm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_soberano("Acesso Negado", "Apenas administradores podem iniciar festas.", COR_PERIGO))
            return
        tipo = args[0].lower() if args else "balada"
        tipos_config = {
            "balada":     {"emoji": "🎉", "cor": 0x9B59B6, "duracao": 3, "canal": "balada"},
            "pijama":     {"emoji": "🧸", "cor": 0xF1948A, "duracao": 2, "canal": "festa-do-pijama"},
            "aniversario":{"emoji": "🎂", "cor": COR_DOURADO, "duracao": 2, "canal": "festa-de-aniversário"},
        }
        cfg = tipos_config.get(tipo, tipos_config["balada"])
        # Abrir chamadas de voz relevantes
        if message.guild:
            for vc in message.guild.voice_channels:
                if cfg["canal"] in vc.name.lower() or "balada" in vc.name.lower():
                    try:
                        await vc.set_permissions(message.guild.default_role, view_channel=True, connect=True)
                    except Exception:
                        pass
        embed = discord.Embed(
            title=f"{cfg['emoji']} Festa Imperial — {tipo.capitalize()}",
            description=(
                f"*A administração imperial decretou início de festividades.*\n{SEP}\n\n"
                f"**Tipo:** {tipo.capitalize()}\n"
                f"**Duração estimada:** {cfg['duracao']} horas\n"
                f"**Chamadas abertas:** Sim\n\n"
                f"*Dirija-se aos canais de voz relevantes para participar.*"
            ),
            color=cfg["cor"]
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send("@everyone", embed=embed)
        # Lançar rodadas de V ou D
        canal_vdd = None
        for ch in message.guild.text_channels:
            if "vdd-ou-desafio" in ch.name.lower():
                canal_vdd = ch
                break
        if canal_vdd:
            await canal_vdd.send(
                embed=embed_soberano(
                    f"{cfg['emoji']} Verdade ou Desafio — Festa {tipo.capitalize()}",
                    "*Uma rodada especial foi aberta para os festeiros. Clique abaixo para participar.*",
                    cfg["cor"]
                ),
                view=VerdadeOuDesafioView()
            )

    # D. REGISTRAR PÉROLA DO RP
    async def handle_registrar_perola(self, message, args):
        user_data = get_user(message.author.id)
        try:
            adm = message.author.guild_permissions.administrator
        except Exception:
            adm = False
        if not adm and message.author.id != IMPERADOR_ID and not user_data.get("co_soberano"):
            await message.channel.send(embed=embed_soberano("Acesso Restrito", "Apenas staff pode registrar pérolas do RP.", COR_PERIGO))
            return
        if not args:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Uso: `Tenshi, registrar-perola [ID_Mensagem]`", COR_NEUTRO))
            return
        try:
            msg_id = int(args[0])
        except ValueError:
            await message.channel.send(embed=embed_soberano("ID Inválido", "Forneça um ID de mensagem válido.", COR_NEUTRO))
            return
        try:
            msg_original = await message.channel.fetch_message(msg_id)
        except Exception:
            await message.channel.send(embed=embed_soberano("Mensagem Não Encontrada", "O ID fornecido não corresponde a uma mensagem neste canal.", COR_NEUTRO))
            return
        canal_perolas = None
        for ch in message.guild.text_channels:
            if "pérolas-do-rp" in ch.name.lower() or "perolas-do-rp" in ch.name.lower():
                canal_perolas = ch
                break
        if not canal_perolas:
            await message.channel.send(embed=embed_soberano("Canal Não Encontrado", "Canal #pérolas-do-rp não localizado.", COR_NEUTRO))
            return
        embed = discord.Embed(
            title="⭐ Pérola do RP — Registro Permanente",
            color=COR_DOURADO
        )
        embed.add_field(name="Autor",   value=msg_original.author.mention,                 inline=True)
        embed.add_field(name="Canal",   value=msg_original.channel.mention,                inline=True)
        embed.add_field(name="Data",    value=msg_original.created_at.strftime('%d/%m/%Y'), inline=True)
        embed.add_field(name="Conteúdo",value=f"```{msg_original.content[:500]}```",        inline=False)
        embed.add_field(name="Arquivado por", value=message.author.mention,                inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await canal_perolas.send(embed=embed)
        await message.channel.send(embed=embed_soberano("Pérola Arquivada", "A mensagem foi preservada no canal #pérolas-do-rp.", COR_SUCESSO))

    # D. VERDADE OU DESAFIO (comando manual)
    async def handle_vdd(self, message):
        embed = embed_soberano(
            "Verdade ou Desafio — Imperial",
            "*Selecione sua opção. Coragem é esperada de todo súdito do Império.*",
            COR_IMPERIAL
        )
        await message.channel.send(embed=embed, view=VerdadeOuDesafioView())

    # B. LOOP DE VOZ — bônus passivos
    async def _loop_voz_passivo(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            for guild in self.bot.guilds:
                for vc in guild.voice_channels:
                    nome = vc.name.lower()
                    for membro in vc.members:
                        if membro.bot:
                            continue
                        uid = str(membro.id)
                        if uid not in _voice_times:
                            _voice_times[uid] = {}
                        if nome not in _voice_times[uid]:
                            _voice_times[uid][nome] = agora.isoformat()
                        entrada = datetime.fromisoformat(_voice_times[uid][nome])
                        minutos = (agora - entrada).total_seconds() / 60
                        user = get_user(membro.id)
                        modificado = False
                        if "mudinhos" in nome and minutos >= 10:
                            red = int(user.get("fadiga", 0) * 0.05)
                            if red > 0:
                                user["fadiga"] = max(0, user["fadiga"] - red)
                                _voice_times[uid][nome] = agora.isoformat()
                                modificado = True
                        elif ("conversas" in nome or "jogos" in nome) and minutos >= 60:
                            bonus = int(user.get("poder", 100) * 0.05)
                            user["poder"] = user.get("poder", 100) + bonus
                            _voice_times[uid][nome] = agora.isoformat()
                            modificado = True
                        if modificado:
                            save_user(membro.id, user)
            await asyncio.sleep(600)  # Verificar a cada 10 minutos
