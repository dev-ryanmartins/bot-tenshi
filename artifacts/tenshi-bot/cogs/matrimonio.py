import discord
from datetime import UTC, datetime

from database import get_casamentos, get_user, save_casamentos, save_user
from lei_imperial import RITO_REAL_PASSOS
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, SEP


COR_DOURADO = 0x9E7815
COR_IMPERIAL = 0x2C3E50
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


def _agora():
    return datetime.now(UTC).replace(tzinfo=None)


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


def _cid(a: int, b: int) -> str:
    return f"{min(a, b)}_{max(a, b)}"


def _ja_casado(member: discord.Member) -> bool:
    return bool(get_user(member.id).get("conjuge"))


def _registrar_uniao(n1: discord.Member, n2: discord.Member, tipo: str, celebrante_id: int | None = None):
    casamentos = get_casamentos()
    casamentos[_cid(n1.id, n2.id)] = {
        "noivo1": str(n1.id),
        "noivo2": str(n2.id),
        "tipo": tipo,
        "celebrante": str(celebrante_id) if celebrante_id else None,
        "data": _agora().isoformat(),
    }
    save_casamentos(casamentos)

    u1 = get_user(n1.id)
    u2 = get_user(n2.id)
    u1["conjuge"] = str(n2.id)
    u2["conjuge"] = str(n1.id)
    u1["taxa_casa_divisao"] = True
    u2["taxa_casa_divisao"] = True

    if n1.id == IMPERADOR_ID or n2.id == IMPERADOR_ID:
        conjuge_id = n2.id if n1.id == IMPERADOR_ID else n1.id
        conjuge = get_user(conjuge_id)
        conjuge["co_soberano"] = True
        save_user(conjuge_id, conjuge)

    save_user(n1.id, u1)
    save_user(n2.id, u2)


def _tem_autoridade_real(member: discord.Member) -> bool:
    if member.id == IMPERADOR_ID:
        return True
    try:
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True
    except Exception:
        pass
    termos = ("rei", "rainha", "clero", "padre", "celebrante", "guardiao", "guardião")
    return any(any(t in role.name.lower() for t in termos) for role in getattr(member, "roles", []))


class VotosMatrimonioView(discord.ui.View):
    def __init__(self, n1: discord.Member, n2: discord.Member, tipo: str = "comum", celebrante_id: int | None = None):
        super().__init__(timeout=600)
        self.n1 = n1
        self.n2 = n2
        self.tipo = tipo
        self.celebrante_id = celebrante_id
        self.aceites: set[int] = set()
        self.encerrado = False

    @discord.ui.button(label="Aceito a uniao", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.n1.id, self.n2.id):
            await interaction.response.send_message("Este juramento nao lhe pertence.", ephemeral=True)
            return
        if self.encerrado:
            await interaction.response.send_message("O rito ja foi encerrado.", ephemeral=True)
            return
        self.aceites.add(interaction.user.id)
        if len(self.aceites) < 2:
            await interaction.response.send_message("Seu aceite foi registrado nos livros da Casa.", ephemeral=True)
            return

        self.encerrado = True
        self.clear_items()
        _registrar_uniao(self.n1, self.n2, self.tipo, self.celebrante_id)
        titulo = "Certidao Imperial de Uniao" if self.tipo == "comum" else "Certidao Real de Uniao Imperial"
        desc = (
            f"*A Chancelaria Imperial registra a uniao perante o Imperio Tenshi.*\n{SEP}\n\n"
            f"**{self.n1.display_name}** e **{self.n2.display_name}** estao oficialmente unidos.\n\n"
            f"**Data:** {_agora().strftime('%d/%m/%Y')}\n"
            f"**Tipo:** {self.tipo.title()}\n"
            f"**Registro:** Pergaminhos Matrimoniais da Casa Tenshi\n\n"
            f"*Que a honra, a lealdade e a boa-fe sustentem este vinculo.*"
        )
        await interaction.response.edit_message(embed=_embed(titulo, desc, COR_SUCESSO), view=self)

    @discord.ui.button(label="Recuso", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.n1.id, self.n2.id):
            await interaction.response.send_message("Painel restrito.", ephemeral=True)
            return
        self.encerrado = True
        self.clear_items()
        await interaction.response.edit_message(
            embed=_embed("Matrimonio Cancelado", f"{interaction.user.mention} recusou o rito. O protocolo foi encerrado.", COR_NEUTRO),
            view=self,
        )


class PedidoCasamentoView(discord.ui.View):
    def __init__(self, autor: discord.Member, alvo: discord.Member, real: bool = False):
        super().__init__(timeout=900)
        self.autor = autor
        self.alvo = alvo
        self.real = real

    @discord.ui.button(label="Aceitar pedido", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alvo.id:
            await interaction.response.send_message("Somente a pessoa pedida pode aceitar.", ephemeral=True)
            return
        if _ja_casado(self.autor) or _ja_casado(self.alvo):
            await interaction.response.send_message("Um dos envolvidos ja possui uniao registrada.", ephemeral=True)
            return
        self.clear_items()
        if self.real:
            view = RitoRealView(self.autor, self.alvo, interaction.user)
            await interaction.response.edit_message(embed=view.embed_atual(), view=view)
            return

        embed = _embed(
            "Votos de Matrimônio Imperial",
            (
                f"*O pedido foi aceito. A Casa Tenshi exige vontade livre de ambos.*\n{SEP}\n\n"
                f"{self.autor.mention} e {self.alvo.mention}, confirmem abaixo que aceitam esta uniao "
                f"por honra, lealdade e boa-fe."
            ),
            COR_DOURADO,
        )
        await interaction.response.edit_message(embed=embed, view=VotosMatrimonioView(self.autor, self.alvo))

    @discord.ui.button(label="Recusar pedido", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alvo.id:
            await interaction.response.send_message("Somente a pessoa pedida pode recusar.", ephemeral=True)
            return
        self.clear_items()
        await interaction.response.edit_message(
            embed=_embed("Pedido Encerrado", f"{self.alvo.mention} recusou o pedido com respeito formal.", COR_NEUTRO),
            view=self,
        )


class RitoRealView(discord.ui.View):
    def __init__(self, rei: discord.Member, rainha: discord.Member, celebrante: discord.Member):
        super().__init__(timeout=1800)
        self.rei = rei
        self.rainha = rainha
        self.celebrante = celebrante
        self.indice = 0
        self.intencoes: set[int] = set()
        self.juramentos: set[int] = set()
        self.encerrado = False

    def embed_atual(self) -> discord.Embed:
        passo = RITO_REAL_PASSOS[self.indice]
        obrigacao = ""
        if self.indice == 4:
            obrigacao = "\n\n**Confirmacao exigida:** Rei e Rainha devem declarar livre vontade."
        elif self.indice == 6:
            obrigacao = f"\n\n**Juramento exigido:** {self.rei.mention} deve confirmar o juramento do Rei."
        elif self.indice == 7:
            obrigacao = f"\n\n**Juramento exigido:** {self.rainha.mention} deve confirmar o juramento da Rainha."
        desc = (
            f"**Rei:** {self.rei.mention}\n"
            f"**Rainha:** {self.rainha.mention}\n"
            f"**Celebrante:** {self.celebrante.mention}\n\n"
            f"{passo['texto']}{obrigacao}\n\n{SEP}\n"
            f"Etapa {self.indice + 1}/{len(RITO_REAL_PASSOS)}"
        )
        return _embed(f"Rito Solene do Matrimonio Imperial - {passo['titulo']}", desc, COR_DOURADO)

    def _pode_avancar(self, user: discord.Member) -> bool:
        return user.id == self.celebrante.id or _tem_autoridade_real(user)

    @discord.ui.button(label="Confirmar voto", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if self.indice == 4 and uid in (self.rei.id, self.rainha.id):
            self.intencoes.add(uid)
            await interaction.response.send_message("Livre vontade registrada.", ephemeral=True)
            return
        if self.indice == 6 and uid == self.rei.id:
            self.juramentos.add(uid)
            await interaction.response.send_message("Juramento do Rei registrado.", ephemeral=True)
            return
        if self.indice == 7 and uid == self.rainha.id:
            self.juramentos.add(uid)
            await interaction.response.send_message("Juramento da Rainha registrado.", ephemeral=True)
            return
        await interaction.response.send_message("Esta etapa nao exige seu voto neste momento.", ephemeral=True)

    @discord.ui.button(label="Avancar rito", style=discord.ButtonStyle.primary)
    async def avancar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._pode_avancar(interaction.user):
            await interaction.response.send_message("Somente o Celebrante ou autoridade imperial pode avancar o rito.", ephemeral=True)
            return
        if self.indice == 4 and self.intencoes != {self.rei.id, self.rainha.id}:
            await interaction.response.send_message("A declaracao livre dos dois noivos ainda nao foi concluida.", ephemeral=True)
            return
        if self.indice == 6 and self.rei.id not in self.juramentos:
            await interaction.response.send_message("O Juramento do Rei ainda nao foi confirmado.", ephemeral=True)
            return
        if self.indice == 7 and self.rainha.id not in self.juramentos:
            await interaction.response.send_message("O Juramento da Rainha ainda nao foi confirmado.", ephemeral=True)
            return
        if self.indice < len(RITO_REAL_PASSOS) - 1:
            self.indice += 1
            await interaction.response.edit_message(embed=self.embed_atual(), view=self)
            return

        self.encerrado = True
        self.clear_items()
        _registrar_uniao(self.rei, self.rainha, "real", self.celebrante.id)
        desc = (
            f"*Esta concluido o Rito Solene do Matrimonio Imperial Tenshi.*\n{SEP}\n\n"
            f"**{self.rei.display_name}** e **{self.rainha.display_name}** foram unidos como Casa Real "
            f"perante a Familia Imperial e o Imperio.\n\n"
            f"**Efeito administrativo:** registro matrimonial real, status de co-soberania quando aplicavel "
            f"e arquivamento nos Pergaminhos Matrimoniais.\n\n"
            f"*Longa vida ao Rei e a Rainha.*"
        )
        await interaction.response.edit_message(embed=_embed("Proclamacao da Uniao Real", desc, COR_SUCESSO), view=self)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._pode_avancar(interaction.user):
            await interaction.response.send_message("Somente autoridade imperial pode cancelar o rito.", ephemeral=True)
            return
        self.clear_items()
        await interaction.response.edit_message(embed=_embed("Rito Cancelado", "O protocolo matrimonial real foi encerrado sem registro.", COR_NEUTRO), view=self)


class Matrimonio:
    def __init__(self, bot):
        self.bot = bot

    async def handle_pedido_comum(self, message, args):
        if not message.mentions:
            await message.channel.send(embed=_embed("Parametro Invalido", "Use: `Tenshi, pedido @usuario [mensagem]`", COR_NEUTRO))
            return
        alvo = message.mentions[0]
        if alvo.bot or alvo.id == message.author.id:
            await message.channel.send(embed=_embed("Pedido Invalido", "Escolha uma pessoa valida para o pedido.", COR_PERIGO))
            return
        if _ja_casado(message.author) or _ja_casado(alvo):
            await message.channel.send(embed=_embed("Registro Existente", "Um dos envolvidos ja possui uniao registrada.", COR_PERIGO))
            return
        texto = " ".join(a for a in args if not a.startswith("<@")).strip()
        extra = f"\n\n**Palavras do pedido:**\n*{texto[:900]}*" if texto else ""
        embed = _embed(
            "Pedido de Casamento Imperial",
            (
                f"{message.author.mention} apresenta um pedido formal a {alvo.mention}.\n\n"
                f"*Este pedido comum exige aceite livre e confirmacao dos votos antes do registro.*"
                f"{extra}"
            ),
            COR_DOURADO,
        )
        await message.channel.send(embed=embed, view=PedidoCasamentoView(message.author, alvo, real=False))

    async def handle_pedido_real(self, message, args):
        if message.author.id != IMPERADOR_ID and not _tem_autoridade_real(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "Pedido real exige Rei/Imperador ou autoridade matrimonial.", COR_PERIGO))
            return
        if not message.mentions:
            await message.channel.send(embed=_embed("Parametro Invalido", "Use: `Tenshi, pedido-real @usuario [mensagem]`", COR_NEUTRO))
            return
        alvo = message.mentions[0]
        if alvo.bot or alvo.id == message.author.id:
            await message.channel.send(embed=_embed("Pedido Invalido", "Escolha uma pessoa valida para o pedido real.", COR_PERIGO))
            return
        if _ja_casado(message.author) or _ja_casado(alvo):
            await message.channel.send(embed=_embed("Registro Existente", "Um dos envolvidos ja possui uniao registrada.", COR_PERIGO))
            return
        texto = " ".join(a for a in args if not a.startswith("<@")).strip()
        extra = f"\n\n**Declaracao Real:**\n*{texto[:1000]}*" if texto else ""
        embed = _embed(
            "Pedido Real de Matrimônio",
            (
                f"{message.author.mention} convoca a Casa Tenshi e apresenta pedido real a {alvo.mention}.\n\n"
                f"*Se aceito, inicia-se o Rito Solene do Matrimonio Imperial Tenshi, com etapas formais, "
                f"juramentos e proclamacao final.*{extra}"
            ),
            COR_DOURADO,
        )
        await message.channel.send(embed=embed, view=PedidoCasamentoView(message.author, alvo, real=True))

    async def handle_rito_real(self, message, args):
        if not _tem_autoridade_real(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "O rito real exige Celebrante, Clero, Rei, Rainha, admin ou Imperador.", COR_PERIGO))
            return
        if len(message.mentions) < 2:
            await message.channel.send(embed=_embed("Parametro Invalido", "Use: `Tenshi, rito-real @rei @rainha`", COR_NEUTRO))
            return
        rei, rainha = message.mentions[:2]
        if rei.id == rainha.id or rei.bot or rainha.bot:
            await message.channel.send(embed=_embed("Rito Invalido", "Informe duas pessoas validas.", COR_PERIGO))
            return
        if _ja_casado(rei) or _ja_casado(rainha):
            await message.channel.send(embed=_embed("Registro Existente", "Um dos envolvidos ja possui uniao registrada.", COR_PERIGO))
            return
        view = RitoRealView(rei, rainha, message.author)
        await message.channel.send(embed=view.embed_atual(), view=view)

    async def handle_registro_casamento(self, message, args):
        alvo = message.mentions[0] if message.mentions else message.author
        user = get_user(alvo.id)
        conjuge_id = user.get("conjuge")
        if not conjuge_id:
            await message.channel.send(embed=_embed("Sem Registro", f"{alvo.mention} nao possui casamento registrado.", COR_NEUTRO))
            return
        casamentos = get_casamentos()
        registro = casamentos.get(_cid(alvo.id, int(conjuge_id)), {})
        await message.channel.send(embed=_embed(
            "Registro Matrimonial Imperial",
            (
                f"**Membro:** {alvo.mention}\n"
                f"**Conjuge:** <@{conjuge_id}>\n"
                f"**Tipo:** {registro.get('tipo', 'comum').title()}\n"
                f"**Data:** {registro.get('data', 'sem data')}\n"
                f"**Co-soberania:** {'Sim' if user.get('co_soberano') else 'Nao'}"
            ),
            COR_DOURADO,
        ))
