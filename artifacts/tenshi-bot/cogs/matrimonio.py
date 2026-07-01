import unicodedata
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import discord

from database import (
    get_casamentos,
    get_cerimonias,
    get_user,
    save_casamentos,
    save_cerimonias,
    save_user,
)
from confirmacoes import registrar_confirmacao, remover_confirmacao, texto_confirmacao
from lei_imperial import RITO_REAL_PASSOS
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, SEP


COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D
FUSO_CERIMONIA = ZoneInfo("America/Sao_Paulo")
PAPEIS_CORTE = (
    "padrinho_honra",
    "segundo_padrinho",
    "dama_honra",
    "segunda_madrinha",
)
ROTULOS_CORTE = {
    "padrinho_honra": "Padrinho de honra",
    "segundo_padrinho": "Segundo padrinho",
    "dama_honra": "Dama de honra",
    "segunda_madrinha": "Segunda madrinha",
}


def _agora() -> datetime:
    return datetime.now(UTC)


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


def _cid(a: int, b: int) -> str:
    return f"{min(a, b)}_{max(a, b)}"


def _sem_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def _eh_padre(member: discord.Member) -> bool:
    """Um celebrante precisa possuir um cargo clerical; ser admin não basta."""
    termos = ("padre", "sacerdote", "sacerdotisa", "bispo", "cardeal", "pontifice", "paroc")
    return any(any(termo in _sem_acentos(role.name) for termo in termos) for role in getattr(member, "roles", []))


def _tem_autoridade_real(member: discord.Member) -> bool:
    if member.id == IMPERADOR_ID:
        return True
    try:
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True
    except Exception:
        pass
    termos = ("rei", "rainha", "co-soberano", "co soberano")
    return any(any(t in _sem_acentos(role.name) for t in termos) for role in getattr(member, "roles", []))


def _ja_casado(member: discord.Member) -> bool:
    return bool(get_user(member.id).get("conjuge"))


def _carregar_cerimonia(chave: str) -> dict | None:
    return get_cerimonias().get(chave)


def _salvar_cerimonia(chave: str, registro: dict) -> None:
    cerimonias = get_cerimonias()
    cerimonias[chave] = registro
    save_cerimonias(cerimonias)


def _buscar_cerimonia(user_id: int, parceiro_id: int | None = None, somente_aberta: bool = True):
    for chave, registro in get_cerimonias().items():
        noivos = {int(registro["noivo1"]), int(registro["noivo2"])}
        if user_id not in noivos:
            continue
        if parceiro_id is not None and parceiro_id not in noivos:
            continue
        if somente_aberta and registro.get("status") in {"concluida", "cancelada"}:
            continue
        return chave, registro
    return None, None


def _parse_agendamento(data_texto: str, hora_texto: str) -> datetime:
    texto = f"{data_texto.strip()} {hora_texto.strip()}"
    try:
        agendamento = datetime.strptime(texto, "%d/%m/%Y %H:%M").replace(tzinfo=FUSO_CERIMONIA)
    except ValueError as exc:
        raise ValueError("Use data no formato DD/MM/AAAA e hora no formato HH:MM.") from exc
    if agendamento <= datetime.now(FUSO_CERIMONIA):
        raise ValueError("A cerimônia precisa ser agendada para uma data futura.")
    return agendamento


def _corte_completa(registro: dict) -> bool:
    return bool(registro.get("padre") and all(registro.get(papel) for papel in PAPEIS_CORTE))


def _ids_reservados(registro: dict, ignorar: str | None = None) -> set[int]:
    campos = ("noivo1", "noivo2", "padre", *PAPEIS_CORTE)
    return {int(registro[c]) for c in campos if c != ignorar and registro.get(c)}


def _formatar_corte(registro: dict) -> str:
    linhas = [f"**Padre celebrante:** <@{registro['padre']}>" if registro.get("padre") else "**Padre celebrante:** não escolhido"]
    for papel in PAPEIS_CORTE:
        valor = registro.get(papel)
        linhas.append(f"**{ROTULOS_CORTE[papel]}:** <@{valor}>" if valor else f"**{ROTULOS_CORTE[papel]}:** não escolhido")
    return "\n".join(linhas)


def _registrar_uniao(n1: discord.Member, n2: discord.Member, registro: dict) -> None:
    casamentos = get_casamentos()
    casamentos[_cid(n1.id, n2.id)] = {
        "noivo1": str(n1.id),
        "noivo2": str(n2.id),
        "tipo": registro.get("tipo", "comum"),
        "celebrante": registro.get("padre"),
        "padre": registro.get("padre"),
        "padrinho_honra": registro.get("padrinho_honra"),
        "segundo_padrinho": registro.get("segundo_padrinho"),
        "dama_honra": registro.get("dama_honra"),
        "segunda_madrinha": registro.get("segunda_madrinha"),
        "agendado_para": registro.get("agendado_para"),
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


async def _confirmar_pedido_por_comando(message, autor: discord.Member, alvo: discord.Member, real: bool) -> None:
    if _ja_casado(autor) or _ja_casado(alvo):
        await message.channel.send(embed=_embed("Pedido indisponível", "Um dos envolvidos já possui união registrada.", COR_PERIGO))
        return
    if _buscar_cerimonia(autor.id)[1] or _buscar_cerimonia(alvo.id)[1]:
        await message.channel.send(embed=_embed("Preparação existente", "Um dos envolvidos já possui outra cerimônia em preparação.", COR_NEUTRO))
        return
    chave = _cid(autor.id, alvo.id)
    registro = {
        "noivo1": str(autor.id),
        "noivo2": str(alvo.id),
        "tipo": "real" if real else "comum",
        "status": "configurando_corte",
        "pedido_aceito_em": _agora().isoformat(),
        "padre": None,
        **{papel: None for papel in PAPEIS_CORTE},
        "agendado_para": None,
    }
    _salvar_cerimonia(chave, registro)
    view = ConfiguracaoCerimoniaView(chave, autor, alvo)
    await message.channel.send(embed=view.embed_atual(), view=view)


class ConfiguracaoCerimoniaView(discord.ui.View):
    def __init__(self, chave: str, n1: discord.Member, n2: discord.Member):
        super().__init__(timeout=1800)
        self.chave = chave
        self.n1 = n1
        self.n2 = n2

    def embed_atual(self) -> discord.Embed:
        registro = _carregar_cerimonia(self.chave) or {}
        return _embed(
            "Corte de honra da cerimônia",
            (
                f"O pedido entre {self.n1.mention} e {self.n2.mention} foi aceito. O casamento ainda **não foi realizado**.\n\n"
                "Escolham abaixo um padre e quatro pessoas diferentes para a corte de honra. "
                "Quando a seleção estiver completa, o agendamento será liberado.\n\n"
                f"{_formatar_corte(registro)}"
            ),
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.n1.id, self.n2.id):
            await interaction.response.send_message("Somente o casal pode configurar esta cerimônia.", ephemeral=True)
            return False
        return True

    async def _selecionar(self, interaction: discord.Interaction, campo: str, member: discord.Member):
        registro = _carregar_cerimonia(self.chave)
        if not registro:
            await interaction.response.send_message("A preparação desta cerimônia não foi encontrada.", ephemeral=True)
            return
        if campo == "padre" and not _eh_padre(member):
            await interaction.response.send_message("O celebrante precisa possuir um cargo de Padre ou equivalente clerical.", ephemeral=True)
            return
        if member.bot or member.id in _ids_reservados(registro, ignorar=campo):
            await interaction.response.send_message("Cada função deve ser ocupada por uma pessoa diferente e nenhum noivo pode integrar a corte.", ephemeral=True)
            return
        registro[campo] = str(member.id)
        _salvar_cerimonia(self.chave, registro)
        if _corte_completa(registro):
            registro["status"] = "aguardando_agendamento"
            _salvar_cerimonia(self.chave, registro)
            view = AgendamentoCerimoniaView(self.chave, self.n1, self.n2)
            await interaction.response.edit_message(embed=view.embed_atual(), view=view)
            return
        await interaction.response.edit_message(embed=self.embed_atual(), view=self)

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha o padre celebrante", min_values=1, max_values=1, row=0)
    async def padre(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "padre", select.values[0])

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha o padrinho de honra", min_values=1, max_values=1, row=1)
    async def padrinho_honra(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "padrinho_honra", select.values[0])

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha o segundo padrinho", min_values=1, max_values=1, row=2)
    async def segundo_padrinho(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "segundo_padrinho", select.values[0])

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha a dama de honra", min_values=1, max_values=1, row=3)
    async def dama_honra(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "dama_honra", select.values[0])

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha a segunda madrinha", min_values=1, max_values=1, row=4)
    async def segunda_madrinha(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "segunda_madrinha", select.values[0])


class AgendamentoModal(discord.ui.Modal, title="Agendar cerimônia"):
    data = discord.ui.TextInput(label="Data", placeholder="DD/MM/AAAA", min_length=10, max_length=10)
    hora = discord.ui.TextInput(label="Horário de Brasília", placeholder="HH:MM", min_length=5, max_length=5)

    def __init__(self, chave: str, n1: discord.Member, n2: discord.Member):
        super().__init__()
        self.chave = chave
        self.n1 = n1
        self.n2 = n2

    async def on_submit(self, interaction: discord.Interaction):
        try:
            agendamento = _parse_agendamento(self.data.value, self.hora.value)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        registro = _carregar_cerimonia(self.chave)
        if not registro or not _corte_completa(registro):
            await interaction.response.send_message("Conclua a escolha do padre e da corte de honra primeiro.", ephemeral=True)
            return
        registro["agendado_para"] = agendamento.isoformat()
        registro["status"] = "agendada"
        _salvar_cerimonia(self.chave, registro)
        timestamp = int(agendamento.timestamp())
        await interaction.response.edit_message(
            embed=_embed(
                "Cerimônia agendada",
                (
                    f"A cerimônia de {self.n1.mention} e {self.n2.mention} foi marcada para <t:{timestamp}:F> (<t:{timestamp}:R>).\n\n"
                    f"{_formatar_corte(registro)}\n\n"
                    f"Na data marcada, <@{registro['padre']}> deve usar `Tenshi, iniciar-cerimonia {self.n1.mention} {self.n2.mention}`."
                ),
                COR_SUCESSO,
            ),
            view=None,
        )


class AgendamentoCerimoniaView(discord.ui.View):
    def __init__(self, chave: str, n1: discord.Member, n2: discord.Member):
        super().__init__(timeout=1800)
        self.chave = chave
        self.n1 = n1
        self.n2 = n2

    def embed_atual(self) -> discord.Embed:
        registro = _carregar_cerimonia(self.chave) or {}
        return _embed(
            "Definir data da cerimônia",
            f"A corte de honra está completa. Agora o casal pode decidir a data e o horário.\n\n{_formatar_corte(registro)}",
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.n1.id, self.n2.id):
            await interaction.response.send_message("Somente o casal pode agendar esta cerimônia.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Definir data e horário", style=discord.ButtonStyle.primary)
    async def agendar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AgendamentoModal(self.chave, self.n1, self.n2))


async def _iniciar_votos_por_comando(message, chave: str, n1: discord.Member, n2: discord.Member, registro: dict) -> None:
    aceites: set[int] = set()

    async def confirmar_voto(resposta):
        atual = _carregar_cerimonia(chave)
        if not atual or atual.get("status") != "em_cerimonia":
            await resposta.channel.send(embed=_embed("Cerimônia encerrada", "Estes votos não estão mais ativos.", COR_NEUTRO))
            return
        aceites.add(resposta.author.id)
        if len(aceites) < 2:
            await resposta.channel.send(embed=_embed("Voto registrado", f"<@{resposta.author.id}> confirmou. Falta o voto do outro noivo.", COR_DOURADO))
            return
        _registrar_uniao(n1, n2, atual)
        atual["status"] = "concluida"
        atual["concluida_em"] = _agora().isoformat()
        _salvar_cerimonia(chave, atual)
        await resposta.channel.send(embed=_embed(
            "Certidão Imperial de União",
            (
                f"**{n1.display_name}** e **{n2.display_name}** estão oficialmente unidos.\n\n"
                f"{_formatar_corte(atual)}\n\n**Data:** {_agora().strftime('%d/%m/%Y')}"
            ),
            COR_SUCESSO,
        ))

    async def cancelar_voto(resposta):
        atual = _carregar_cerimonia(chave) or registro
        atual["status"] = "cancelada"
        _salvar_cerimonia(chave, atual)
        outro_id = n2.id if resposta.author.id == n1.id else n1.id
        remover_confirmacao(outro_id)
        await resposta.channel.send(embed=_embed("Cerimônia cancelada", f"<@{resposta.author.id}> recusou os votos.", COR_NEUTRO))

    acao = f"confirmar os votos de casamento entre {n1.display_name} e {n2.display_name}"
    registrar_confirmacao(n1.id, acao, confirmar_voto, cancelar_voto, minutos=15)
    registrar_confirmacao(n2.id, acao, confirmar_voto, cancelar_voto, minutos=15)
    await message.channel.send(embed=_embed(
        "Cerimônia de Casamento",
        (
            f"O padre {message.author.mention} conduz a união de {n1.mention} e {n2.mention}.\n\n"
            f"{_formatar_corte(registro)}\n\n{SEP}\n"
            f"Cada noivo deve responder separadamente.\n\n{texto_confirmacao(acao)}"
        ),
    ))


class RitoRealView(discord.ui.View):
    def __init__(self, chave: str, rei: discord.Member, rainha: discord.Member, padre: discord.Member, registro: dict):
        super().__init__(timeout=1800)
        self.chave = chave
        self.rei = rei
        self.rainha = rainha
        self.padre = padre
        self.registro = registro
        self.indice = 0
        self.intencoes: set[int] = set()
        self.juramentos: set[int] = set()

    def embed_atual(self) -> discord.Embed:
        passo = RITO_REAL_PASSOS[self.indice]
        obrigacao = ""
        if self.indice == 4:
            obrigacao = "\n\n**Confirmação exigida:** ambos devem declarar livre vontade."
        elif self.indice == 6:
            obrigacao = f"\n\n**Juramento exigido:** {self.rei.mention}."
        elif self.indice == 7:
            obrigacao = f"\n\n**Juramento exigido:** {self.rainha.mention}."
        return _embed(
            f"Rito Solene — {passo['titulo']}",
            (
                f"**Casal:** {self.rei.mention} e {self.rainha.mention}\n"
                f"**Padre celebrante:** {self.padre.mention}\n\n"
                f"{passo['texto']}{obrigacao}\n\n{SEP}\nEtapa {self.indice + 1}/{len(RITO_REAL_PASSOS)}"
            ),
        )

    @discord.ui.button(label="Confirmar voto", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if self.indice == 4 and uid in (self.rei.id, self.rainha.id):
            self.intencoes.add(uid)
            await interaction.response.send_message("Livre vontade registrada.", ephemeral=True)
            return
        if self.indice == 6 and uid == self.rei.id:
            self.juramentos.add(uid)
            await interaction.response.send_message("Juramento registrado.", ephemeral=True)
            return
        if self.indice == 7 and uid == self.rainha.id:
            self.juramentos.add(uid)
            await interaction.response.send_message("Juramento registrado.", ephemeral=True)
            return
        await interaction.response.send_message("Esta etapa não exige seu voto agora.", ephemeral=True)

    @discord.ui.button(label="Avançar rito", style=discord.ButtonStyle.primary)
    async def avancar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.padre.id or not _eh_padre(interaction.user):
            await interaction.response.send_message("Somente o padre escolhido pode avançar o rito.", ephemeral=True)
            return
        if self.indice == 4 and self.intencoes != {self.rei.id, self.rainha.id}:
            await interaction.response.send_message("A declaração dos dois noivos ainda não foi concluída.", ephemeral=True)
            return
        if self.indice == 6 and self.rei.id not in self.juramentos:
            await interaction.response.send_message("O primeiro juramento ainda não foi confirmado.", ephemeral=True)
            return
        if self.indice == 7 and self.rainha.id not in self.juramentos:
            await interaction.response.send_message("O segundo juramento ainda não foi confirmado.", ephemeral=True)
            return
        if self.indice < len(RITO_REAL_PASSOS) - 1:
            self.indice += 1
            await interaction.response.edit_message(embed=self.embed_atual(), view=self)
            return
        self.clear_items()
        _registrar_uniao(self.rei, self.rainha, self.registro)
        self.registro["status"] = "concluida"
        self.registro["concluida_em"] = _agora().isoformat()
        _salvar_cerimonia(self.chave, self.registro)
        await interaction.response.edit_message(
            embed=_embed(
                "Proclamação da União Real",
                f"**{self.rei.display_name}** e **{self.rainha.display_name}** foram unidos por {self.padre.mention}.\n\n{_formatar_corte(self.registro)}",
                COR_SUCESSO,
            ),
            view=self,
        )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.padre.id or not _eh_padre(interaction.user):
            await interaction.response.send_message("Somente o padre escolhido pode cancelar o rito.", ephemeral=True)
            return
        self.registro["status"] = "cancelada"
        _salvar_cerimonia(self.chave, self.registro)
        self.clear_items()
        await interaction.response.edit_message(embed=_embed("Rito cancelado", "A cerimônia foi encerrada sem registro.", COR_NEUTRO), view=self)


class Matrimonio:
    def __init__(self, bot):
        self.bot = bot

    async def _enviar_pedido(self, message, args, real: bool):
        if not message.mentions:
            comando = "pedido-real" if real else "pedido"
            await message.channel.send(embed=_embed("Parâmetro inválido", f"Use: `Tenshi, {comando} @usuario [mensagem]`", COR_NEUTRO))
            return
        alvo = message.mentions[0]
        if alvo.bot or alvo.id == message.author.id:
            await message.channel.send(embed=_embed("Pedido inválido", "Escolha uma pessoa válida.", COR_PERIGO))
            return
        if _ja_casado(message.author) or _ja_casado(alvo):
            await message.channel.send(embed=_embed("Registro existente", "Um dos envolvidos já é casado.", COR_PERIGO))
            return
        if _buscar_cerimonia(message.author.id)[1] or _buscar_cerimonia(alvo.id)[1]:
            await message.channel.send(embed=_embed("Preparação existente", "Um dos envolvidos já possui outra cerimônia em preparação.", COR_NEUTRO))
            return
        chave = _cid(message.author.id, alvo.id)
        existente = _carregar_cerimonia(chave)
        if existente and existente.get("status") not in {"cancelada", "concluida"}:
            await message.channel.send(embed=_embed("Pedido existente", "Este casal já possui uma cerimônia em preparação.", COR_NEUTRO))
            return
        texto = " ".join(a for a in args if not a.startswith("<@")).strip()
        extra = f"\n\n**Palavras do pedido:**\n*{texto[:900]}*" if texto else ""
        tipo = "real" if real else "comum"
        acao = f"aceitar o pedido de casamento {tipo} de {message.author.display_name}"

        async def confirmar(resposta):
            await _confirmar_pedido_por_comando(resposta, message.author, alvo, real)

        async def cancelar(resposta):
            await resposta.channel.send(embed=_embed("Pedido recusado", f"{alvo.mention} recusou o pedido de casamento.", COR_NEUTRO))

        registrar_confirmacao(alvo.id, acao, confirmar, cancelar)
        await message.channel.send(
            embed=_embed(
                "Pedido Real de Casamento" if real else "Pedido de Casamento",
                (
                    f"{message.author.mention} pede {alvo.mention} em casamento.\n\n"
                    f"Este é apenas o **pedido {tipo}**: aceitar inicia a preparação, não realiza a união.\n\n"
                    f"{texto_confirmacao(acao)}"
                    f"{extra}"
                ),
            ),
        )

    async def handle_pedido_comum(self, message, args):
        await self._enviar_pedido(message, args, real=False)

    async def handle_pedido_real(self, message, args):
        if not _tem_autoridade_real(message.author):
            await message.channel.send(embed=_embed("Acesso restrito", "O pedido real exige autoridade da Casa Real.", COR_PERIGO))
            return
        await self._enviar_pedido(message, args, real=True)

    async def handle_configurar_cerimonia(self, message, args):
        parceiro = message.mentions[0] if message.mentions else None
        chave, registro = _buscar_cerimonia(message.author.id, parceiro.id if parceiro else None)
        if not registro:
            await message.channel.send(embed=_embed("Sem preparação", "Aceite primeiro um pedido de casamento.", COR_NEUTRO))
            return
        n1 = message.guild.get_member(int(registro["noivo1"]))
        n2 = message.guild.get_member(int(registro["noivo2"]))
        if not n1 or not n2:
            await message.channel.send(embed=_embed("Casal indisponível", "Um dos noivos não está mais no servidor.", COR_PERIGO))
            return
        if registro.get("status") == "agendada":
            agendamento = datetime.fromisoformat(registro["agendado_para"])
            timestamp = int(agendamento.timestamp())
            await message.channel.send(embed=_embed("Cerimônia agendada", f"Data: <t:{timestamp}:F>\n\n{_formatar_corte(registro)}", COR_SUCESSO))
            return
        if registro.get("status") == "em_cerimonia":
            await message.channel.send(embed=_embed("Cerimônia em andamento", "O padre já iniciou os votos deste casamento.", COR_NEUTRO))
            return
        if _corte_completa(registro):
            view = AgendamentoCerimoniaView(chave, n1, n2)
        else:
            view = ConfiguracaoCerimoniaView(chave, n1, n2)
        await message.channel.send(embed=view.embed_atual(), view=view)

    async def handle_iniciar_cerimonia(self, message, args, exigir_real: bool = False):
        if len(message.mentions) < 2:
            await message.channel.send(embed=_embed("Parâmetro inválido", "Use: `Tenshi, iniciar-cerimonia @noivo1 @noivo2`", COR_NEUTRO))
            return
        n1, n2 = message.mentions[:2]
        chave = _cid(n1.id, n2.id)
        registro = _carregar_cerimonia(chave)
        if not registro or registro.get("status") not in {"agendada", "em_cerimonia"}:
            await message.channel.send(embed=_embed("Cerimônia indisponível", "O casal não possui cerimônia completamente configurada e agendada.", COR_NEUTRO))
            return
        if exigir_real and registro.get("tipo") != "real":
            await message.channel.send(embed=_embed("Rito incorreto", "Este pedido não é um casamento real.", COR_PERIGO))
            return
        if message.author.id != int(registro["padre"]) or not _eh_padre(message.author):
            await message.channel.send(embed=_embed("Celebrante inválido", "Somente o padre escolhido pelo casal pode iniciar a cerimônia.", COR_PERIGO))
            return
        agendamento = datetime.fromisoformat(registro["agendado_para"])
        if _agora() < agendamento.astimezone(UTC):
            timestamp = int(agendamento.timestamp())
            await message.channel.send(embed=_embed("Ainda não é o horário", f"A cerimônia está marcada para <t:{timestamp}:F>.", COR_NEUTRO))
            return
        registro["status"] = "em_cerimonia"
        _salvar_cerimonia(chave, registro)
        if registro.get("tipo") == "real":
            view = RitoRealView(chave, n1, n2, message.author, registro)
            await message.channel.send(embed=view.embed_atual(), view=view)
            return
        await _iniciar_votos_por_comando(message, chave, n1, n2, registro)

    async def handle_rito_real(self, message, args):
        await self.handle_iniciar_cerimonia(message, args, exigir_real=True)

    async def handle_registro_casamento(self, message, args):
        alvo = message.mentions[0] if message.mentions else message.author
        user = get_user(alvo.id)
        conjuge_id = user.get("conjuge")
        if not conjuge_id:
            await message.channel.send(embed=_embed("Sem registro", f"{alvo.mention} não possui casamento registrado.", COR_NEUTRO))
            return
        registro = get_casamentos().get(_cid(alvo.id, int(conjuge_id)), {})
        corte = _formatar_corte(registro) if registro.get("padre") else "**Padre celebrante:** registro antigo"
        await message.channel.send(
            embed=_embed(
                "Registro Matrimonial Imperial",
                (
                    f"**Membro:** {alvo.mention}\n"
                    f"**Cônjuge:** <@{conjuge_id}>\n"
                    f"**Tipo:** {registro.get('tipo', 'comum').title()}\n"
                    f"**Data:** {registro.get('data', 'sem data')}\n"
                    f"{corte}\n"
                    f"**Co-soberania:** {'Sim' if user.get('co_soberano') else 'Não'}"
                ),
            )
        )
