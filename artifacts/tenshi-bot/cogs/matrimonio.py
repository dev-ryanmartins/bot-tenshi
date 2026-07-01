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
from ia_router import ia_rapida
from lei_imperial import RITO_REAL_PASSOS
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, SEP

COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D
FUSO_CERIMONIA = ZoneInfo("America/Sao_Paulo")
CELEBRANTE_IA = "Tenshi IA"
PAPEIS_CORTE = (
    "padrinho_honra",
    "segundo_padrinho",
    "terceiro_padrinho",
    "dama_honra",
    "segunda_madrinha",
    "terceira_madrinha",
)
ROTULOS_CORTE = {
    "padrinho_honra": "Padrinho de honra",
    "segundo_padrinho": "Segundo padrinho",
    "terceiro_padrinho": "Terceiro padrinho",
    "dama_honra": "Dama de honra",
    "segunda_madrinha": "Segunda madrinha",
    "terceira_madrinha": "Terceira madrinha",
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


def _tem_autoridade_real(member: discord.Member) -> bool:
    if member.id == IMPERADOR_ID:
        return True
    try:
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True
    except Exception:
        pass
    termos = ("rei", "rainha", "co-soberano", "co soberano")
    return any(any(termo in _sem_acentos(role.name) for termo in termos) for role in getattr(member, "roles", []))


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
    try:
        agendamento = datetime.strptime(
            f"{data_texto.strip()} {hora_texto.strip()}", "%d/%m/%Y %H:%M"
        ).replace(tzinfo=FUSO_CERIMONIA)
    except ValueError as exc:
        raise ValueError("Use data no formato DD/MM/AAAA e hora no formato HH:MM.") from exc
    if agendamento <= datetime.now(FUSO_CERIMONIA):
        raise ValueError("A cerimônia precisa ser agendada para uma data futura.")
    return agendamento


def _corte_completa(registro: dict) -> bool:
    # Permite cerimônia com pelo menos alguns papéis preenchidos (não exige todos)
    papeis_preenchidos = sum(1 for papel in PAPEIS_CORTE if registro.get(papel))
    return papeis_preenchidos >= 3  # Mínimo de 3 pessoas na corte


def _configuracao_completa(registro: dict) -> bool:
    return _corte_completa(registro) and bool(registro.get("ritualista"))


def _ids_reservados(registro: dict, ignorar: str | None = None) -> set[int]:
    campos = ("noivo1", "noivo2", "ritualista", *PAPEIS_CORTE)
    return {int(registro[campo]) for campo in campos if campo != ignorar and registro.get(campo)}


def _formatar_corte(registro: dict) -> str:
    linhas = [f"**Celebrante:** 🤖 {CELEBRANTE_IA}"]
    ritualista = registro.get("ritualista")
    linhas.append(f"**Ritualista:** <@{ritualista}>" if ritualista else "**Ritualista:** não escolhido")
    for papel in PAPEIS_CORTE:
        valor = registro.get(papel)
        linhas.append(f"**{ROTULOS_CORTE[papel]}:** <@{valor}>" if valor else f"**{ROTULOS_CORTE[papel]}:** não escolhido")
    return "\n".join(linhas)


def _novo_registro(autor: discord.Member, alvo: discord.Member, real: bool) -> dict:
    return {
        "noivo1": str(autor.id),
        "noivo2": str(alvo.id),
        "tipo": "real" if real else "comum",
        "status": "configurando_corte",
        "pedido_aceito_em": _agora().isoformat(),
        "celebrante": "tenshi_ia",
        "ritualista": None,
        **{papel: None for papel in PAPEIS_CORTE},
        "agendado_para": None,
    }


def _registrar_uniao(n1: discord.Member, n2: discord.Member, registro: dict) -> None:
    casamentos = get_casamentos()
    casamentos[_cid(n1.id, n2.id)] = {
        "noivo1": str(n1.id),
        "noivo2": str(n2.id),
        "tipo": registro.get("tipo", "comum"),
        "celebrante": "tenshi_ia",
        "ritualista": registro.get("ritualista"),
        **{papel: registro.get(papel) for papel in PAPEIS_CORTE},
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


async def _gerar_cerimonia_ia(n1: discord.Member, n2: discord.Member, registro: dict) -> str:
    sistema = (
        "Você é Tenshi, inteligência cerimonial do Império. Celebre um casamento de RPG em PT-BR, "
        "com solenidade, afeto e no máximo 220 palavras. Faça uma abertura, reconheça o Ritualista e a "
        "corte de honra, apresente votos breves e termine pedindo que os noivos escolham Sim, aceito ou Não aceito. "
        "Não invente fatos íntimos e não declare a união concluída antes dos dois aceites."
    )
    usuario = (
        f"Noivos: {n1.display_name} e {n2.display_name}. Tipo: {registro.get('tipo', 'comum')}. "
        f"Ritualista ID: {registro.get('ritualista')}. Celebre agora como a própria Tenshi IA."
    )
    try:
        texto = await ia_rapida(sistema, usuario, max_tokens=420)
        if texto:
            return texto[:3500]
    except Exception:
        pass
    return (
        f"Perante o Império de Tenshi, reunimos **{n1.display_name}** e **{n2.display_name}**. "
        "O Ritualista abre o círculo simbólico enquanto a corte de honra testemunha esta escolha.\n\n"
        "Eu, Tenshi, conduzo esta celebração e recordo que nenhuma união existe sem vontade livre. "
        "Que respeito, lealdade e cuidado acompanhem o caminho que desejam construir.\n\n"
        "Noivos, confirmem agora: vocês aceitam esta união?"
    )


class PedidoCasamentoView(discord.ui.View):
    def __init__(self, autor: discord.Member, alvo: discord.Member, real: bool = False):
        super().__init__(timeout=900)
        self.autor = autor
        self.alvo = alvo
        self.real = real

    @discord.ui.button(label="Sim, aceito", emoji="💍", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alvo.id:
            await interaction.response.send_message("Somente a pessoa pedida pode responder.", ephemeral=True)
            return
        if _ja_casado(self.autor) or _ja_casado(self.alvo):
            await interaction.response.send_message("Um dos envolvidos já possui união registrada.", ephemeral=True)
            return
        if _buscar_cerimonia(self.autor.id)[1] or _buscar_cerimonia(self.alvo.id)[1]:
            await interaction.response.send_message("Um dos envolvidos já possui outra cerimônia em preparação.", ephemeral=True)
            return
        chave = _cid(self.autor.id, self.alvo.id)
        _salvar_cerimonia(chave, _novo_registro(self.autor, self.alvo, self.real))
        view = ConfiguracaoCerimoniaView(chave, self.autor, self.alvo)
        await interaction.response.edit_message(embed=view.embed_atual(), view=view)

    @discord.ui.button(label="Não aceito", emoji="✖️", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alvo.id:
            await interaction.response.send_message("Somente a pessoa pedida pode responder.", ephemeral=True)
            return
        self.clear_items()
        await interaction.response.edit_message(
            embed=_embed("Pedido recusado", f"{self.alvo.mention} não aceitou o pedido de casamento.", COR_NEUTRO),
            view=self,
        )


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
            f"A celebração será conduzida pela própria **{CELEBRANTE_IA}**. Escolham a corte de honra (opcional): três padrinhos e até três madrinhas, "
            "todos diferentes. Pule os que não desejarem. Depois será aberta a escolha do Ritualista.\n\n"
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
        if member.bot or member.id in _ids_reservados(registro, ignorar=campo):
            await interaction.response.send_message(
                "Cada função deve ser ocupada por uma pessoa diferente e nenhum noivo pode integrar a corte.",
                ephemeral=True,
            )
            return
        registro[campo] = str(member.id)
        _salvar_cerimonia(self.chave, registro)
        await interaction.response.edit_message(embed=self.embed_atual(), view=self)

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha o padrinho de honra", row=0)
    async def padrinho_honra(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "padrinho_honra", select.values[0])

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha o segundo padrinho", row=1)
    async def segundo_padrinho(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "segundo_padrinho", select.values[0])

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha o terceiro padrinho", row=2)
    async def terceiro_padrinho(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "terceiro_padrinho", select.values[0])

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha a dama de honra", row=3)
    async def dama_honra(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "dama_honra", select.values[0])

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha a segunda madrinha", row=4)
    async def segunda_madrinha(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "segunda_madrinha", select.values[0])

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha a terceira madrinha (opcional)", row=5)
    async def terceira_madrinha(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "terceira_madrinha", select.values[0])

    @discord.ui.button(label="Continuar com corte atual", style=discord.ButtonStyle.secondary, row=6)
    async def continuar_corte(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.n1.id, self.n2.id):
            await interaction.response.send_message("Somente o casal pode continuar.", ephemeral=True)
            return
        registro = _carregar_cerimonia(self.chave)
        if not registro or not _corte_completa(registro):
            await interaction.response.send_message("Escolha pelo menos 3 pessoas para a corte de honra.", ephemeral=True)
            return
        registro["status"] = "escolhendo_ritualista"
        _salvar_cerimonia(self.chave, registro)
        view = RitualistaCerimoniaView(self.chave, self.n1, self.n2)
        await interaction.response.edit_message(embed=view.embed_atual(), view=view)

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha a terceira madrinha (opcional)", row=5)
    async def terceira_madrinha(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await self._selecionar(interaction, "terceira_madrinha", select.values[0])


class RitualistaCerimoniaView(discord.ui.View):
    def __init__(self, chave: str, n1: discord.Member, n2: discord.Member):
        super().__init__(timeout=1800)
        self.chave = chave
        self.n1 = n1
        self.n2 = n2

    def embed_atual(self) -> discord.Embed:
        registro = _carregar_cerimonia(self.chave) or {}
        return _embed(
            "Escolha do Ritualista",
            (
                f"A corte de honra está completa. Agora escolham quem abrirá e conduzirá o **Ritual de Tenshi**.\n\n"
                f"O Ritualista organiza o círculo e avança as etapas; a celebração e a narrativa pertencem à **{CELEBRANTE_IA}**.\n\n"
                f"{_formatar_corte(registro)}"
            ),
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.n1.id, self.n2.id):
            await interaction.response.send_message("Somente o casal pode escolher o Ritualista.", ephemeral=True)
            return False
        return True

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Escolha o Ritualista de Tenshi", row=0)
    async def ritualista(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        registro = _carregar_cerimonia(self.chave)
        member = select.values[0]
        if not registro:
            await interaction.response.send_message("A preparação desta cerimônia não foi encontrada.", ephemeral=True)
            return
        if member.bot or member.id in _ids_reservados(registro, ignorar="ritualista"):
            await interaction.response.send_message("O Ritualista deve ser uma pessoa diferente dos noivos e da corte.", ephemeral=True)
            return
        registro["ritualista"] = str(member.id)
        registro["status"] = "aguardando_agendamento"
        _salvar_cerimonia(self.chave, registro)
        view = AgendamentoCerimoniaView(self.chave, self.n1, self.n2)
        await interaction.response.edit_message(embed=view.embed_atual(), view=view)


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
        if not registro or not _configuracao_completa(registro):
            await interaction.response.send_message("Conclua a corte de honra e escolha o Ritualista primeiro.", ephemeral=True)
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
                    f"Na data marcada, <@{registro['ritualista']}> deve usar "
                    f"`Tenshi, iniciar-cerimonia {self.n1.mention} {self.n2.mention}`."
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
            f"A corte e o Ritualista estão definidos. Agora decidam data e horário.\n\n{_formatar_corte(registro)}",
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.n1.id, self.n2.id):
            await interaction.response.send_message("Somente o casal pode agendar esta cerimônia.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Definir data e horário", style=discord.ButtonStyle.primary)
    async def agendar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AgendamentoModal(self.chave, self.n1, self.n2))


class VotosMatrimonioView(discord.ui.View):
    def __init__(self, chave: str, n1: discord.Member, n2: discord.Member, registro: dict):
        super().__init__(timeout=1200)
        self.chave = chave
        self.n1 = n1
        self.n2 = n2
        self.registro = registro
        self.aceites: set[int] = set()

    @discord.ui.button(label="Sim, aceito", emoji="💍", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.n1.id, self.n2.id):
            await interaction.response.send_message("Somente os noivos podem responder aos votos.", ephemeral=True)
            return
        self.aceites.add(interaction.user.id)
        if len(self.aceites) < 2:
            await interaction.response.send_message("Seu aceite foi registrado. Falta o voto do outro noivo.", ephemeral=True)
            return
        self.clear_items()
        _registrar_uniao(self.n1, self.n2, self.registro)
        self.registro["status"] = "concluida"
        self.registro["concluida_em"] = _agora().isoformat()
        _salvar_cerimonia(self.chave, self.registro)
        await interaction.response.edit_message(
            embed=_embed(
                "Certidão Imperial de União — Tenshi IA",
                (
                    f"A própria **{CELEBRANTE_IA}** reconhece a livre união de "
                    f"**{self.n1.display_name}** e **{self.n2.display_name}**.\n\n"
                    f"{_formatar_corte(self.registro)}\n\n**Data:** {_agora().strftime('%d/%m/%Y')}"
                ),
                COR_SUCESSO,
            ),
            view=self,
        )

    @discord.ui.button(label="Não aceito", emoji="✖️", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.n1.id, self.n2.id):
            await interaction.response.send_message("Somente os noivos podem responder aos votos.", ephemeral=True)
            return
        self.registro["status"] = "cancelada"
        _salvar_cerimonia(self.chave, self.registro)
        self.clear_items()
        await interaction.response.edit_message(
            embed=_embed("Cerimônia encerrada", f"{interaction.user.mention} não aceitou a união.", COR_NEUTRO),
            view=self,
        )


class RitoRealView(discord.ui.View):
    def __init__(self, chave: str, rei: discord.Member, rainha: discord.Member, ritualista: discord.Member, registro: dict, introducao: str):
        super().__init__(timeout=1800)
        self.chave = chave
        self.rei = rei
        self.rainha = rainha
        self.ritualista = ritualista
        self.registro = registro
        self.introducao = introducao
        self.indice = 0
        self.intencoes: set[int] = set()
        self.juramentos: set[int] = set()

    def embed_atual(self) -> discord.Embed:
        passo = RITO_REAL_PASSOS[self.indice]
        obrigacao = ""
        if self.indice == 4:
            obrigacao = "\n\n**Confirmação exigida:** ambos devem clicar em Sim, aceito."
        elif self.indice == 6:
            obrigacao = f"\n\n**Juramento exigido:** {self.rei.mention}."
        elif self.indice == 7:
            obrigacao = f"\n\n**Juramento exigido:** {self.rainha.mention}."
        introducao = f"{self.introducao}\n\n{SEP}\n" if self.indice == 0 else ""
        return _embed(
            f"Rito Solene de Tenshi — {passo['titulo']}",
            (
                f"**Celebrante:** 🤖 {CELEBRANTE_IA}\n"
                f"**Ritualista:** {self.ritualista.mention}\n"
                f"**Casal:** {self.rei.mention} e {self.rainha.mention}\n\n"
                f"{introducao}{passo['texto']}{obrigacao}\n\n{SEP}\nEtapa {self.indice + 1}/{len(RITO_REAL_PASSOS)}"
            ),
        )

    @discord.ui.button(label="Sim, aceito", emoji="💍", style=discord.ButtonStyle.success)
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
        await interaction.response.send_message("Esta etapa não exige seu aceite agora.", ephemeral=True)

    @discord.ui.button(label="Avançar Ritual de Tenshi", emoji="🔮", style=discord.ButtonStyle.primary)
    async def avancar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ritualista.id:
            await interaction.response.send_message("Somente o Ritualista escolhido pode avançar o ritual.", ephemeral=True)
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
                "Proclamação da União Real — Tenshi IA",
                (
                    f"A **{CELEBRANTE_IA}** proclama a união de **{self.rei.display_name}** e "
                    f"**{self.rainha.display_name}**, com o Ritual de Tenshi conduzido por {self.ritualista.mention}.\n\n"
                    f"{_formatar_corte(self.registro)}"
                ),
                COR_SUCESSO,
            ),
            view=self,
        )

    @discord.ui.button(label="Não aceito", emoji="✖️", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        permitidos = {self.rei.id, self.rainha.id, self.ritualista.id}
        if interaction.user.id not in permitidos:
            await interaction.response.send_message("Você não participa deste rito.", ephemeral=True)
            return
        self.registro["status"] = "cancelada"
        _salvar_cerimonia(self.chave, self.registro)
        self.clear_items()
        await interaction.response.edit_message(
            embed=_embed("Rito encerrado", f"{interaction.user.mention} encerrou o ritual sem união.", COR_NEUTRO),
            view=self,
        )


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
        texto = " ".join(a for a in args if not a.startswith("<@")).strip()
        extra = f"\n\n**Palavras do pedido:**\n*{texto[:900]}*" if texto else ""
        tipo = "real" if real else "comum"
        await message.channel.send(
            embed=_embed(
                "Pedido Real de Casamento" if real else "Pedido de Casamento",
                (
                    f"{message.author.mention} pede {alvo.mention} em casamento.\n\n"
                    f"Este é apenas o **pedido {tipo}**: aceitar inicia a preparação, não realiza a união."
                    f"{extra}"
                ),
            ),
            view=PedidoCasamentoView(message.author, alvo, real=real),
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
            await message.channel.send(embed=_embed(
                "Cerimônia agendada", f"Data: <t:{int(agendamento.timestamp())}:F>\n\n{_formatar_corte(registro)}", COR_SUCESSO
            ))
            return
        if registro.get("status") == "em_cerimonia":
            await message.channel.send(embed=_embed("Cerimônia em andamento", "A Tenshi IA já iniciou esta celebração.", COR_NEUTRO))
            return
        if _configuracao_completa(registro):
            view = AgendamentoCerimoniaView(chave, n1, n2)
        elif _corte_completa(registro):
            view = RitualistaCerimoniaView(chave, n1, n2)
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
            await message.channel.send(embed=_embed("Cerimônia indisponível", "O casal não possui cerimônia configurada e agendada.", COR_NEUTRO))
            return
        if exigir_real and registro.get("tipo") != "real":
            await message.channel.send(embed=_embed("Rito incorreto", "Este pedido não é um casamento real.", COR_PERIGO))
            return
        if message.author.id != int(registro["ritualista"]):
            await message.channel.send(embed=_embed("Ritualista necessário", "Somente o Ritualista escolhido pode iniciar o Ritual de Tenshi.", COR_PERIGO))
            return
        agendamento = datetime.fromisoformat(registro["agendado_para"])
        if _agora() < agendamento.astimezone(UTC):
            await message.channel.send(embed=_embed("Ainda não é o horário", f"A cerimônia está marcada para <t:{int(agendamento.timestamp())}:F>.", COR_NEUTRO))
            return
        registro["status"] = "em_cerimonia"
        _salvar_cerimonia(chave, registro)
        texto_ia = await _gerar_cerimonia_ia(n1, n2, registro)
        if registro.get("tipo") == "real":
            view = RitoRealView(chave, n1, n2, message.author, registro, texto_ia)
            await message.channel.send(embed=view.embed_atual(), view=view)
            return
        view = VotosMatrimonioView(chave, n1, n2, registro)
        await message.channel.send(
            embed=_embed(
                "Celebração de Casamento — Tenshi IA",
                f"{texto_ia}\n\n{SEP}\n{_formatar_corte(registro)}",
            ),
            view=view,
        )

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
        await message.channel.send(embed=_embed(
            "Registro Matrimonial Imperial",
            (
                f"**Membro:** {alvo.mention}\n"
                f"**Cônjuge:** <@{conjuge_id}>\n"
                f"**Tipo:** {registro.get('tipo', 'comum').title()}\n"
                f"**Data:** {registro.get('data', 'sem data')}\n"
                f"{_formatar_corte(registro)}\n"
                f"**Co-soberania:** {'Sim' if user.get('co_soberano') else 'Não'}"
            ),
        ))

    async def handle_cancelar_casamento_usuario(self, message, args):
        """
        Comando: tenshi, cancelar-casamento
        Permite ao usuário cancelar seu próprio casamento ou cerimônia em preparação.
        """
        user = get_user(message.author.id)
        conjuge_id = user.get("conjuge")
        
        # Verificar se há cerimônia em preparação
        chave_cerimonia, registro_cerimonia = _buscar_cerimonia(message.author.id, somente_aberta=True)
        
        # Se não há cerimônia em preparação e não há casamento registrado
        if not registro_cerimonia and not conjuge_id:
            await message.channel.send(embed=_embed(
                "Sem vínculo",
                f"{message.author.mention} não possui casamento registrado ou cerimônia em preparação para cancelar.",
                COR_NEUTRO
            ))
            return
        
        # Se há cerimônia em preparação
        if registro_cerimonia:
            noivo1_id = int(registro_cerimonia["noivo1"])
            noivo2_id = int(registro_cerimonia["noivo2"])
            
            registro_cerimonia["status"] = "cancelada"
            registro_cerimonia["cancelada_em"] = _agora().isoformat()
            _salvar_cerimonia(chave_cerimonia, registro_cerimonia)
            
            outro_noivo_id = noivo2_id if message.author.id == noivo1_id else noivo1_id
            
            await message.channel.send(embed=_embed(
                "Cerimônia cancelada",
                f"{message.author.mention} cancelou a cerimônia de casamento com <@{outro_noivo_id}>.\n\n"
                f"O processo foi interrompido e ambos os envolvidos foram desbloqueados.",
                COR_SUCESSO
            ))
            return
        
        # Se há casamento registrado
        if conjuge_id:
            conjuge_id_int = int(conjuge_id)
            chave_casamento = _cid(message.author.id, conjuge_id_int)
            
            # Remover o casamento
            casamentos = get_casamentos()
            if chave_casamento in casamentos:
                del casamentos[chave_casamento]
                save_casamentos(casamentos)
            
            # Limpar dados de ambos os cônjuges
            user["conjuge"] = None
            user["co_soberano"] = False
            user["taxa_casa_divisao"] = False
            save_user(message.author.id, user)
            
            conjuge = get_user(conjuge_id_int)
            conjuge["conjuge"] = None
            conjuge["co_soberano"] = False
            conjuge["taxa_casa_divisao"] = False
            save_user(conjuge_id_int, conjuge)
            
            await message.channel.send(embed=_embed(
                "Casamento dissolvido",
                f"O vínculo matrimonial entre {message.author.mention} e <@{conjuge_id_int}> foi dissoluto por petição.\n\n"
                f"**Efeitos:**\n"
                f"• Cônjuge removido do perfil\n"
                f"• Co-soberania revogada\n"
                f"• Divisão de renda de casa encerrada",
                COR_PERIGO
            ))
            return

    async def handle_cancelar_casamento_admin(self, message, args):
        """
        Comando: tenshi, anular-casamento @usuario1 @usuario2
        Comando admin para cancelar qualquer casamento ou cerimônia.
        """
        if not _tem_autoridade_real(message.author):
            await message.channel.send(embed=_embed(
                "Acesso restrito",
                "Apenas autoridades da Casa Real podem anular casamentos.",
                COR_PERIGO
            ))
            return
        
        if len(message.mentions) < 1:
            await message.channel.send(embed=_embed(
                "Uso inválido",
                "Use: `Tenshi, anular-casamento @usuario1 [@usuario2]`\n\n"
                "Se apenas 1 usuário for mencionado, sua cerimônia será cancelada.\n"
                "Se 2 forem mencionados, o casamento entre eles será dissolvido.",
                COR_NEUTRO
            ))
            return
        
        usuario1 = message.mentions[0]
        usuario2 = message.mentions[1] if len(message.mentions) > 1 else None
        
        # Caso 1: Cancelar cerimônia de 1 usuário
        if not usuario2:
            chave_cerimonia, registro_cerimonia = _buscar_cerimonia(usuario1.id, somente_aberta=True)
            
            if not registro_cerimonia:
                await message.channel.send(embed=_embed(
                    "Sem cerimônia",
                    f"{usuario1.mention} não possui cerimônia em preparação.",
                    COR_NEUTRO
                ))
                return
            
            noivo1_id = int(registro_cerimonia["noivo1"])
            noivo2_id = int(registro_cerimonia["noivo2"])
            outro_noivo_id = noivo2_id if usuario1.id == noivo1_id else noivo1_id
            
            registro_cerimonia["status"] = "cancelada"
            registro_cerimonia["cancelada_em"] = _agora().isoformat()
            registro_cerimonia["anulada_por"] = str(message.author.id)
            _salvar_cerimonia(chave_cerimonia, registro_cerimonia)
            
            await message.channel.send(embed=_embed(
                "Cerimônia anulada por ordem imperial",
                f"{message.author.mention} cancelou a cerimônia de casamento entre "
                f"{usuario1.mention} e <@{outro_noivo_id}>.\n\n"
                f"**Motivo:** Decisão administrativa\n"
                f"**Carimbo:** {_agora().strftime('%d/%m/%Y às %H:%M:%S')}",
                COR_PERIGO
            ))
            return
        
        # Caso 2: Anular casamento entre 2 usuários
        chave_casamento = _cid(usuario1.id, usuario2.id)
        
        # Verificar se há cerimônia em preparação primeiro
        chave_cerimonia, registro_cerimonia = _buscar_cerimonia(usuario1.id, usuario2.id, somente_aberta=True)
        if registro_cerimonia:
            registro_cerimonia["status"] = "cancelada"
            registro_cerimonia["cancelada_em"] = _agora().isoformat()
            registro_cerimonia["anulada_por"] = str(message.author.id)
            _salvar_cerimonia(chave_cerimonia, registro_cerimonia)
            
            await message.channel.send(embed=_embed(
                "Cerimônia anulada por ordem imperial",
                f"{message.author.mention} cancelou a cerimônia entre {usuario1.mention} e {usuario2.mention}.\n\n"
                f"**Motivo:** Decisão administrativa\n"
                f"**Carimbo:** {_agora().strftime('%d/%m/%Y às %H:%M:%S')}",
                COR_PERIGO
            ))
            return
        
        # Verificar se há casamento registrado
        casamentos = get_casamentos()
        if chave_casamento not in casamentos:
            await message.channel.send(embed=_embed(
                "Sem casamento registrado",
                f"Não há vínculo matrimonial ativo entre {usuario1.mention} e {usuario2.mention}.",
                COR_NEUTRO
            ))
            return
        
        # Anular o casamento
        del casamentos[chave_casamento]
        save_casamentos(casamentos)
        
        # Limpar dados de ambos os usuários
        user1 = get_user(usuario1.id)
        user2 = get_user(usuario2.id)
        
        user1["conjuge"] = None
        user1["co_soberano"] = False
        user1["taxa_casa_divisao"] = False
        user2["conjuge"] = None
        user2["co_soberano"] = False
        user2["taxa_casa_divisao"] = False
        
        save_user(usuario1.id, user1)
        save_user(usuario2.id, user2)
        
        await message.channel.send(embed=_embed(
            "Casamento anulado por ordem imperial",
            f"{message.author.mention} anulou o vínculo matrimonial entre {usuario1.mention} e {usuario2.mention}.\n\n"
            f"**Efeitos imediatos:**\n"
            f"• Casamento dissolvido\n"
            f"• Co-soberania revogada (se aplicável)\n"
            f"• Divisão de renda de casa encerrada\n"
            f"**Carimbo:** {_agora().strftime('%d/%m/%Y às %H:%M:%S')}",
            COR_PERIGO
        ))
