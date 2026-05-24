"""
Módulo Temporadas — Funcionalidades 18-20
18. Sistema de Estações do Ano
19. Entrevistas de Emprego com IA
20. Central de Emergências Médicas
"""
import discord
import asyncio
import random
from datetime import datetime, date
from database import get_user, save_user, get_internados, save_internados
from utils import SEP, RODAPE_IMPERIAL, IMPERADOR_ID

COR_IMPERIAL = 0x2C3E50
COR_DOURADO  = 0x9E7815
COR_SUCESSO  = 0x1A5C2E
COR_PERIGO   = 0x7B1F1F
COR_NEUTRO   = 0x3D3D3D

def embed_soberano(titulo: str, descricao: str, cor: int = COR_IMPERIAL) -> discord.Embed:
    e = discord.Embed(title=titulo, description=descricao, color=cor)
    e.set_footer(text=RODAPE_IMPERIAL)
    return e

# ─── ESTAÇÕES ─────────────────────────────────────────────────────────────────
def get_estacao_atual() -> dict:
    mes = date.today().month
    if mes in (3, 4, 5):
        return {"nome": "Primavera", "emoji": "🌸", "efeito": "primavera",
                "descricao": "Treinamentos ao ar livre concedem +10% de XP."}
    elif mes in (6, 7, 8):
        return {"nome": "Verão",     "emoji": "☀️",  "efeito": "verao",
                "descricao": "Piscina concede 3x de recuperação de fadiga."}
    elif mes in (9, 10, 11):
        return {"nome": "Outono",    "emoji": "🍂",  "efeito": "outono",
                "descricao": "Missões têm +20% de recompensa em moedas."}
    else:
        return {"nome": "Inverno",   "emoji": "❄️",  "efeito": "inverno",
                "descricao": "Taxa de condomínio reduzida em 50%. Treinos externos custam +15% fadiga."}

# ─── EMPREGOS COM ENTREVISTA ──────────────────────────────────────────────────
EMPREGOS_ENTREVISTA = {
    "banqueiro": {
        "nome": "Banqueiro Imperial",
        "local": "banco",
        "salario": 120,
        "perguntas": [
            "Qual é a principal função do Banco Imperial dentro da economia de Tenshi?",
            "Um cidadão tenta sacar mais do que possui em conta. Como você procede?",
            "Descreva como o sistema de empréstimos do Banco Imperial protege tanto o credor quanto o devedor.",
        ],
    },
    "medico_hospital": {
        "nome": "Médico do Hospital Imperial",
        "local": "hospital",
        "salario": 140,
        "perguntas": [
            "Quais são os critérios para internar um guerreiro nocauteado no Hospital Imperial?",
            "Um paciente recusa tratamento. Quais são os procedimentos protocolares?",
            "Como você diferencia fadiga comum de dano em batalha durante o diagnóstico inicial?",
        ],
    },
    "policial": {
        "nome": "Agente Policial Imperial",
        "local": "departamento-policial",
        "salario": 100,
        "perguntas": [
            "Cite dois artigos do Código de Conduta do Império e suas penalidades associadas.",
            "Um agente da Máfia é pego em flagrante no Beco. Quais medidas imediatas você toma?",
            "Como você equilibra a aplicação da lei com a presunção de inocência em Tenshi?",
        ],
    },
}

_entrevistas_ativas: dict = {}


class EntrevistaView(discord.ui.View):
    def __init__(self, candidato_id: int, cargo_id: str, perguntas: list):
        super().__init__(timeout=300)
        self.candidato_id = candidato_id
        self.cargo_id     = cargo_id
        self.perguntas    = perguntas
        self.respostas    = []
        self.etapa        = 0
        self.encerrada    = False

    @discord.ui.button(label="Responder Pergunta", style=discord.ButtonStyle.secondary)
    async def responder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.candidato_id:
            await interaction.response.send_message("Esta entrevista não é sua.", ephemeral=True)
            return
        if self.encerrada or self.etapa >= len(self.perguntas):
            await interaction.response.send_message("Entrevista encerrada.", ephemeral=True)
            return
        modal = RespostaEntrevistaModal(self.perguntas[self.etapa], self)
        await interaction.response.send_modal(modal)

    async def avancar(self, interaction: discord.Interaction, resposta: str):
        self.respostas.append(resposta)
        self.etapa += 1
        if self.etapa >= len(self.perguntas):
            self.encerrada = True
            await self._avaliar(interaction)
        else:
            prox = self.perguntas[self.etapa]
            await interaction.followup.send(
                embed=embed_soberano(
                    f"Pergunta {self.etapa + 1} de {len(self.perguntas)}",
                    prox, COR_IMPERIAL
                ),
                view=self,
                ephemeral=True
            )

    async def _avaliar(self, interaction: discord.Interaction):
        cargo = EMPREGOS_ENTREVISTA[self.cargo_id]
        min_chars = sum(len(r) for r in self.respostas)
        aprovado = min_chars >= 80
        if aprovado:
            user = get_user(self.candidato_id)
            user.setdefault("empregos_aprovados", [])
            if self.cargo_id not in user["empregos_aprovados"]:
                user["empregos_aprovados"].append(self.cargo_id)
            user["salario"] = max(user.get("salario", 0), cargo["salario"])
            save_user(self.candidato_id, user)
            await interaction.followup.send(
                embed=embed_soberano(
                    "Entrevista Concluída — Aprovado",
                    f"O Diretor avaliou suas respostas e considera o candidato **apto** para o cargo de **{cargo['nome']}**.\n\n"
                    f"**Salário:** {cargo['salario']} moedas/trabalho\n\n"
                    f"*A contratação foi registrada no banco de dados imperial.*",
                    COR_SUCESSO
                ),
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                embed=embed_soberano(
                    "Entrevista Concluída — Reprovado",
                    f"O Diretor considera as respostas insuficientes para a vaga de **{cargo['nome']}**.\n\n"
                    f"*Estude mais sobre as normas e diretrizes do Império antes de candidatar-se novamente.*",
                    COR_PERIGO
                ),
                ephemeral=True
            )
        if self.candidato_id in _entrevistas_ativas:
            del _entrevistas_ativas[self.candidato_id]


class RespostaEntrevistaModal(discord.ui.Modal, title="Resposta — Entrevista Imperial"):
    resposta = discord.ui.TextInput(
        label="Sua resposta",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True
    )

    def __init__(self, pergunta: str, view: EntrevistaView):
        super().__init__()
        self.view_ref = view
        self.resposta.placeholder = pergunta[:100]

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.view_ref.avancar(interaction, self.resposta.value)


# ─── EMERGÊNCIAS MÉDICAS ──────────────────────────────────────────────────────
class SocorrerView(discord.ui.View):
    def __init__(self, paciente: discord.Member, canal_corredores):
        super().__init__(timeout=600)
        self.paciente       = paciente
        self.canal_corredores = canal_corredores
        self.socorrido      = False

    @discord.ui.button(label="Socorrer Paciente", style=discord.ButtonStyle.success)
    async def socorrer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.socorrido:
            await interaction.response.send_message("Este paciente já foi atendido.", ephemeral=True)
            return
        user = get_user(interaction.user.id)
        empregos_ok = user.get("empregos_aprovados", [])
        cargo_emp   = user.get("emprego_atual") or user.get("cargo_empresa", "")
        is_medico   = ("medico" in str(cargo_emp).lower() or
                       "enfermeiro" in str(cargo_emp).lower() or
                       "medico_hospital" in empregos_ok or
                       "enfermeiro" in empregos_ok)
        try:
            tem_perm = interaction.user.guild_permissions.administrator
        except Exception:
            tem_perm = False
        if not is_medico and not tem_perm and interaction.user.id != IMPERADOR_ID:
            await interaction.response.send_message(
                embed=embed_soberano("Acesso Negado", "Apenas médicos ou enfermeiros podem executar este protocolo.", COR_PERIGO),
                ephemeral=True
            )
            return
        self.socorrido = True
        self.clear_items()
        p_user = get_user(self.paciente.id)
        p_user["nocauteado"]    = False
        p_user["bloqueado_ate"] = None
        p_user["fadiga"]        = max(0, p_user.get("fadiga", 0) - 30)
        internados = get_internados()
        uid = str(self.paciente.id)
        if uid in internados:
            del internados[uid]
        save_internados(internados)
        save_user(self.paciente.id, p_user)
        bonus_med = random.randint(20, 50)
        user["moedas"] = user.get("moedas", 0) + bonus_med
        save_user(interaction.user.id, user)
        await interaction.response.edit_message(
            embed=embed_soberano(
                "Protocolo de Atendimento Concluído",
                f"**Paciente:** {self.paciente.mention}\n"
                f"**Médico responsável:** {interaction.user.mention}\n\n"
                f"O paciente foi estabilizado e encaminhado aos corredores para recuperação.\n\n"
                f"**Bônus profissional:** +{bonus_med} moedas",
                COR_SUCESSO
            ),
            view=self
        )
        if self.canal_corredores:
            try:
                await self.canal_corredores.send(
                    content=self.paciente.mention,
                    embed=embed_soberano(
                        "Alta da Emergência",
                        f"Você foi atendido por {interaction.user.mention} e transferido para recuperação.\n\n"
                        f"Seus comandos foram restaurados. Descanse nos corredores do hospital.",
                        COR_SUCESSO
                    )
                )
            except Exception:
                pass


class Temporadas:
    def __init__(self, bot):
        self.bot = bot
        self._estacao_iniciada = False

    def cog_load(self):
        if not self._estacao_iniciada:
            self._estacao_iniciada = True
            self.bot.loop.create_task(self._loop_estacoes())

    # 18. ESTAÇÕES
    async def handle_estacoes(self, message):
        estacao = get_estacao_atual()
        embed = discord.Embed(
            title=f"{estacao['emoji']} Estação Atual — {estacao['nome']}",
            color=COR_IMPERIAL
        )
        embed.add_field(name="Período", value=f"Mês {date.today().month}", inline=True)
        embed.add_field(name="Efeito Global", value=estacao["descricao"], inline=False)
        taxa = 25 if estacao["efeito"] == "inverno" else 50
        embed.add_field(name="Taxa de Condomínio", value=f"{taxa} moedas/semana", inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    def get_taxa_condominio(self) -> int:
        estacao = get_estacao_atual()
        return 25 if estacao["efeito"] == "inverno" else 50

    # 19. ENTREVISTA DE EMPREGO
    async def handle_entrevista(self, message, args):
        if not args:
            embed = discord.Embed(
                title="Central de Entrevistas Imperiais",
                description=f"Cargos disponíveis:\n{SEP}",
                color=COR_IMPERIAL
            )
            for cid, c in EMPREGOS_ENTREVISTA.items():
                embed.add_field(
                    name=f"{c['nome']}",
                    value=f"Salário: {c['salario']} moedas\n`Tenshi, entrevista {cid}`",
                    inline=True
                )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return
        cargo_id = args[0].lower()
        if cargo_id not in EMPREGOS_ENTREVISTA:
            await message.channel.send(embed=embed_soberano("Cargo Não Encontrado", f"Cargo `{cargo_id}` não encontrado.", COR_NEUTRO))
            return
        if message.author.id in _entrevistas_ativas:
            await message.channel.send(embed=embed_soberano("Entrevista em Andamento", "Você já possui uma entrevista ativa.", COR_NEUTRO))
            return
        cargo = EMPREGOS_ENTREVISTA[cargo_id]
        _entrevistas_ativas[message.author.id] = cargo_id
        perguntas = cargo["perguntas"]
        view = EntrevistaView(message.author.id, cargo_id, perguntas)
        embed = discord.Embed(
            title=f"Entrevista — {cargo['nome']}",
            description=(
                f"*O Diretor do {cargo['local'].capitalize()} Imperial recebe você formalmente.*\n{SEP}\n\n"
                f"A entrevista consiste em **{len(perguntas)} perguntas**. Responda com clareza e conhecimento das normas imperiais.\n\n"
                f"**Pergunta 1 de {len(perguntas)}:**\n{perguntas[0]}"
            ),
            color=COR_IMPERIAL
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.author.send(embed=embed, view=view)
        await message.channel.send(embed=embed_soberano("Entrevista Iniciada", "A entrevista foi enviada para sua DM. Responda por lá.", COR_SUCESSO))

    # 20. EMERGÊNCIAS MÉDICAS
    async def handle_socorrer(self, message, args):
        if not message.mentions:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Uso: `Tenshi, socorrer @usuario`", COR_NEUTRO))
            return
        paciente_membro = message.mentions[0]
        p_user = get_user(paciente_membro.id)
        if not p_user.get("nocauteado"):
            await message.channel.send(embed=embed_soberano(
                "Paciente Estável",
                f"{paciente_membro.display_name} não está em estado crítico.",
                COR_NEUTRO
            ))
            return
        canal_corredores = None
        if message.guild:
            for ch in message.guild.text_channels:
                if "corredor" in ch.name.lower() and "hospital" in (ch.category.name.lower() if ch.category else ""):
                    canal_corredores = ch
                    break
        view = SocorrerView(paciente_membro, canal_corredores)
        embed = discord.Embed(
            title="Protocolo de Atendimento de Emergência",
            description=(
                f"**Paciente:** {paciente_membro.mention}\n"
                f"**Status:** Nocauteado / Incapacitado\n"
                f"**Local:** {message.channel.mention}\n\n"
                f"Um profissional de saúde deve confirmar o atendimento abaixo."
            ),
            color=COR_PERIGO
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed, view=view)

    async def notificar_nocaute(self, guild, vitima: discord.Member):
        canal_ambulancia = None
        for ch in guild.text_channels:
            if "chegada-ambul" in ch.name.lower() or "ambulancia" in ch.name.lower():
                canal_ambulancia = ch
                break
        if not canal_ambulancia:
            return
        p_user = get_user(vitima.id)
        p_user["nocauteado"] = True
        save_user(vitima.id, p_user)
        internados = get_internados()
        internados[str(vitima.id)] = {
            "nome": vitima.display_name,
            "data": datetime.utcnow().isoformat(),
        }
        save_internados(internados)
        embed = discord.Embed(
            title="⚠ CHAMADA DE EMERGÊNCIA",
            description=(
                f"*SIRENE ATIVA — UNIDADE REQUERIDA*\n{SEP}\n\n"
                f"**Paciente:** {vitima.mention}\n"
                f"**Status:** Nocauteado em combate\n"
                f"**Protocolo:** Aguardando atendimento médico\n\n"
                f"*Um médico ou enfermeiro deve usar `Tenshi, socorrer @{vitima.display_name}` para iniciar o atendimento.*"
            ),
            color=COR_PERIGO
        )
        embed.set_footer(text="Central de Emergências  •  Hospital Imperial")
        try:
            await canal_ambulancia.send(content=f"@here", embed=embed)
        except Exception:
            pass

    async def _loop_estacoes(self):
        await self.bot.wait_until_ready()
        ultima_estacao = None
        while not self.bot.is_closed():
            estacao = get_estacao_atual()
            if estacao["nome"] != ultima_estacao:
                ultima_estacao = estacao["nome"]
                for guild in self.bot.guilds:
                    for ch in guild.text_channels:
                        if "estações-do-ano" in ch.name.lower() or "estacoes-do-ano" in ch.name.lower():
                            try:
                                await ch.send(embed=discord.Embed(
                                    title=f"{estacao['emoji']} Nova Estação — {estacao['nome']}",
                                    description=estacao["descricao"],
                                    color=COR_IMPERIAL
                                ))
                            except Exception:
                                pass
                            break
            await asyncio.sleep(86400)

from datetime import datetime
