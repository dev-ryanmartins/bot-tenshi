"""
Módulo Crime — Funcionalidades 10-11
10. Beco e sistema de furtos
11. Boletim de ocorrência e investigação
"""
import discord
import random
import asyncio
from datetime import datetime, timedelta
from database import get_user, save_user, registrar_infracao, get_infrações
from utils import SEP, RODAPE_IMPERIAL, IMPERADOR_ID

COR_PRETO   = 0x111111
COR_PERIGO  = 0x7B1F1F
COR_NEUTRO  = 0x3D3D3D
COR_SUCESSO = 0x1A5C2E
COR_DOURADO = 0x9E7815

HORA_BECO_INICIO = 0   # 00:00 UTC
HORA_BECO_FIM    = 4   # 04:00 UTC (madrugada)
COOLDOWN_FURTO   = 45 * 60  # 45 minutos

def embed_soberano(titulo: str, descricao: str, cor: int = COR_PRETO) -> discord.Embed:
    e = discord.Embed(title=titulo, description=descricao, color=cor)
    e.set_footer(text=RODAPE_IMPERIAL)
    return e

def _hora_beco() -> bool:
    h = datetime.utcnow().hour
    return h >= HORA_BECO_INICIO and h < HORA_BECO_FIM


class ConfirmarFurtoView(discord.ui.View):
    def __init__(self, ladrão: discord.Member, vitima: discord.Member, canal_policia, canal_jornal):
        super().__init__(timeout=30)
        self.ladrão       = ladrão
        self.vitima       = vitima
        self.canal_policia = canal_policia
        self.canal_jornal  = canal_jornal
        self.resolvido    = False

    @discord.ui.button(label="Executar Assalto", style=discord.ButtonStyle.danger)
    async def executar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ladrão.id:
            await interaction.response.send_message("Painel restrito.", ephemeral=True)
            return
        if self.resolvido:
            return
        self.resolvido = True
        self.clear_items()
        l_user = get_user(self.ladrão.id)
        v_user = get_user(self.vitima.id)
        agilidade_l  = l_user.get("atributos", {}).get("agilidade", 100)
        defesa_v     = v_user.get("poder", 100)
        pet_l        = l_user.get("pet", "")
        bonus_pet    = 15 if pet_l == "raposa_furtiva" else 0
        chance       = min(85, max(15, (agilidade_l - defesa_v // 5) + bonus_pet))
        sucesso      = random.randint(1, 100) <= chance
        if sucesso:
            valor = random.randint(20, min(150, v_user.get("moedas", 0)))
            if valor > 0:
                v_user["moedas"] = max(0, v_user.get("moedas", 0) - valor)
                l_user["moedas"] = l_user.get("moedas", 0) + valor
                save_user(self.vitima.id, v_user)
                save_user(self.ladrão.id, l_user)
            embed = discord.Embed(
                title="Assalto — Operação Concluída",
                description=(
                    f"O assalto foi executado com precisão.\n{SEP}\n\n"
                    f"**Alvo:** {self.vitima.display_name}\n"
                    f"**Valor subtraído:** {valor} moedas\n\n"
                    f"*O executor desapareceu nas sombras do beco.*"
                ),
                color=COR_PRETO
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await interaction.response.edit_message(embed=embed, view=self)
            registrar_infracao(self.ladrão.id, "assalto_beco", f"Assalto bem-sucedido contra {self.vitima.id}")
        else:
            embed = discord.Embed(
                title="Assalto — Operação Fracassada",
                description=(
                    f"O assalto foi detectado. {self.ladrão.mention} foi capturado.\n{SEP}\n\n"
                    f"**Consequência:** Transferência compulsória para o Departamento Policial.\n"
                    f"**Bloqueio:** Comandos suspensos por 30 minutos."
                ),
                color=COR_PERIGO
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await interaction.response.edit_message(embed=embed, view=self)
            l_user["bloqueado_ate"] = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
            save_user(self.ladrão.id, l_user)
            if self.canal_policia:
                await self.canal_policia.send(embed=embed_soberano(
                    "Ocorrência Registrada",
                    f"{self.ladrão.mention} foi encaminhado ao Departamento Policial após tentativa de assalto malsucedida contra {self.vitima.mention}.",
                    COR_PERIGO
                ))
            if self.canal_jornal:
                await asyncio.sleep(3)
                await self._gerar_boletim(self.canal_jornal)
            registrar_infracao(self.ladrão.id, "tentativa_assalto", f"Tentativa fracassada contra {self.vitima.id}")

    @discord.ui.button(label="Abortar", style=discord.ButtonStyle.secondary)
    async def abortar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ladrão.id:
            await interaction.response.send_message("Painel restrito.", ephemeral=True)
            return
        self.resolvido = True
        self.clear_items()
        await interaction.response.edit_message(
            embed=embed_soberano("Operação Abortada", "O assalto foi cancelado antes da execução.", COR_NEUTRO),
            view=self
        )

    async def _gerar_boletim(self, canal):
        data_str = datetime.utcnow().strftime('%d/%m/%Y às %H:%M UTC')
        embed = discord.Embed(
            title="Jornal Policial de Tenshi",
            description=(
                f"*Edição de {data_str}*\n{SEP}\n\n"
                f"**TENTATIVA DE ASSALTO NO BECO**\n\n"
                f"*Nas primeiras horas da madrugada, autoridades imperiais registraram uma tentativa de assalto no setor conhecido como 'O Beco'.*\n\n"
                f"O suspeito, identificado como **{self.ladrão.display_name}** (ID: {self.ladrão.id}), tentou subtrair valores em moeda imperial de **{self.vitima.display_name}**, "
                f"porém foi neutralizado pela guarda de segurança antes de consumar o crime.\n\n"
                f"O indivíduo foi conduzido ao Departamento Policial para averiguações. Antecedentes em análise.\n\n"
                f"*Esta matéria foi gerada automaticamente pelo sistema de segurança do Império.*"
            ),
            color=COR_PRETO
        )
        embed.set_footer(text="Jornal Policial do Império Tenshi  •  Confidencial")
        try:
            await canal.send(embed=embed)
        except Exception:
            pass


class Crime:
    def __init__(self, bot):
        self.bot = bot

    # 10. ASSALTAR NO BECO
    async def handle_assaltar(self, message, args):
        if not _hora_beco():
            await message.channel.send(embed=embed_soberano(
                "Operação Indisponível",
                "O Beco só opera entre 00:00 e 04:00 UTC. Retorne na madrugada.",
                COR_NEUTRO
            ))
            return
        canal_nome = message.channel.name.lower() if message.channel else ""
        if "beco" not in canal_nome:
            await message.channel.send(embed=embed_soberano("Canal Inválido", "Esta operação só pode ser conduzida no canal #beco.", COR_NEUTRO))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Uso: `Tenshi, assaltar @usuario`", COR_NEUTRO))
            return
        vitima = message.mentions[0]
        if vitima.id == message.author.id:
            await message.channel.send(embed=embed_soberano("Parâmetro Inválido", "Operação inválida.", COR_NEUTRO))
            return
        ladrão_user = get_user(message.author.id)
        ultimo = ladrão_user.get("ultimo_furto")
        if ultimo:
            diff = (datetime.utcnow() - datetime.fromisoformat(ultimo)).total_seconds()
            if diff < COOLDOWN_FURTO:
                restante = int((COOLDOWN_FURTO - diff) / 60)
                await message.channel.send(embed=embed_soberano(
                    "Cooldown Ativo",
                    f"Ação retida. Tempo de recuperação ativo: **{restante}m**.",
                    COR_NEUTRO
                ))
                return
        ladrão_user["ultimo_furto"] = datetime.utcnow().isoformat()
        save_user(message.author.id, ladrão_user)
        canal_policia = self._get_canal_por_nome(message.guild, "departamento-policial")
        canal_jornal  = self._get_canal_por_nome(message.guild, "jornal-policial")
        embed = discord.Embed(
            title="Preparação de Assalto",
            description=(
                f"*O executor se posiciona nas sombras...*\n{SEP}\n\n"
                f"**Alvo:** {vitima.display_name}\n"
                f"**Local:** {message.channel.mention}\n\n"
                f"*Confirme a execução ou aborte a operação.*"
            ),
            color=COR_PRETO
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = ConfirmarFurtoView(message.author, vitima, canal_policia, canal_jornal)
        await message.channel.send(embed=embed, view=view)

    # 11. MERCADO NEGRO NOTURNO (Tenshi, mercado-negro-beco)
    async def handle_mercado_beco(self, message):
        if not _hora_beco():
            await message.channel.send(embed=embed_soberano(
                "Mercado Fechado",
                "O Mercado Negro do Beco opera exclusivamente entre 00:00 e 04:00 UTC.",
                COR_NEUTRO
            ))
            return
        canal_nome = message.channel.name.lower() if message.channel else ""
        if "beco" not in canal_nome:
            await message.channel.send(embed=embed_soberano("Canal Inválido", "Acesse o canal #beco.", COR_NEUTRO))
            return
        itens_secretos = [
            {"id": "veneno_arcano",  "nome": "Veneno Arcano",  "preco": 200, "efeito": "Reduz 30 de poder do adversário por 2 duelos"},
            {"id": "chave_mestra",   "nome": "Chave Mestra",   "preco": 350, "efeito": "Permite 1 espionagem de canal por 30 min"},
            {"id": "informacao_rara","nome": "Informação Rara", "preco": 500, "efeito": "Revela localização atual de outro jogador"},
        ]
        embed = discord.Embed(
            title="Mercado Negro — Operações Noturnas",
            description=f"*Acesso autorizado. Identidade não registrada.*\n{SEP}",
            color=COR_PRETO
        )
        for item in itens_secretos:
            embed.add_field(
                name=f"{item['nome']} — {item['preco']} moedas",
                value=item["efeito"],
                inline=False
            )
        embed.set_footer(text="Este painel se autodestroirá em 60 segundos.")
        msg = await message.channel.send(embed=embed)
        await asyncio.sleep(60)
        try:
            await msg.delete()
        except Exception:
            pass

    def _get_canal_por_nome(self, guild, nome: str):
        if not guild:
            return None
        for ch in guild.text_channels:
            if nome in ch.name.lower():
                return ch
        return None
