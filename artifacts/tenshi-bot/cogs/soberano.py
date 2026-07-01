"""
Módulo de Prerrogativas Reais — Módulo 15
30 comandos exclusivos do Imperador Alloy.
Verificação estrita: só IMPERADOR_ID pode usar estes comandos.
"""
import discord
import asyncio
import json
import os
from datetime import datetime
from database import (get_user, save_user, get_all_users,
                      registrar_infracao, get_infrações)
from utils import IMPERADOR_ID, SEP, RODAPE_IMPERIAL
from design import (embed_doc, embed_soberano_decreto, embed_admin_doc,
                    embed_judicial, embed_sucesso, embed_perigo_doc,
                    embed_crime_doc, fmt_moedas,
                    COR_GERAL, COR_DECRETO, COR_JUDICIAL, COR_CRIME,
                    COR_ADMIN, COR_SUCESSO, COR_PERIGO, COR_NEUTRO, rodape_padrao)
from ia_router import ia_soberana, ia_narrativa, ia_relatorio
from cogs.parentesco import aplicar_cargo_exclusivo, aplicar_parentesco, garantir_cargo_grupo

# ─── ESTADO GLOBAL SOBERANO ───────────────────────────────────────────────────
_economia_congelada    = False
_bypass_cooldown_ids:  set = set()
_sys_prompt_override:  str | None = None
_memoria_ia:           list = []   # histórico de contexto da IA

STATUS_LIMITES = {
    "vida": (0, 1000, "❤️"),
    "mana": (0, 1000, "🔮"),
    "forca": (0, 1000, "💪"),
    "agilidade": (0, 1000, "💨"),
    "poder": (0, 100_000, "⚡"),
    "xp": (0, 1_000_000, "✨"),
    "nivel": (1, 100, "📊"),
    "fadiga": (0, 100, "💤"),
    "moedas": (0, 1_000_000, "🪙"),
    "conta_banco": (0, 5_000_000, "🏦"),
    "inteligencia": (0, 1000, "🧠"),
    "sabedoria": (0, 1000, "📖"),
    "carisma": (0, 1000, "🎭"),
    "resistencia": (0, 1000, "🛡️"),
    "destreza": (0, 1000, "🏹"),
    "sorte": (0, 1000, "🍀"),
    "honra": (0, 1000, "⚜️"),
    "reputacao": (0, 1000, "🌟"),
    "lideranca": (0, 1000, "👑"),
    "magia": (0, 1000, "🪄"),
    "defesa": (0, 1000, "🏰"),
    "velocidade": (0, 1000, "⚡"),
}

ATRIBUTOS_FICHA = {"vida", "mana", "forca", "agilidade", "inteligencia", "sabedoria", "carisma", "resistencia", "destreza", "sorte", "honra", "reputacao", "lideranca", "magia", "defesa", "velocidade"}

PRESTIGIOS = {
    "bronze": ("Bronze", "🥉", 0xCD7F32),
    "prata": ("Prata", "🥈", 0xC0C0C0),
    "ouro": ("Ouro", "🥇", 0xFFD700),
    "platina": ("Platina", "💠", 0xE5E4E2),
    "diamante": ("Diamante", "💎", 0x5CE1E6),
    "obsidiana": ("Obsidiana", "🖤", 0x2B2B2B),
    "iridio": ("Irídio", "🌌", 0xE6E6FA),
}

CARGOS_SUPREMOS = (
    ("Fundador", "⚜️"), ("Imperador", "👑"), ("Rei", "♔"),
    ("Líder Supremo", "🌌"), ("Administrador", "🛡️"),
    ("Chefe da Máfia", "🔫"), ("Diretor da Academia", "🎓"), ("Professor Imperial", "📚"),
)

CAMPO_TEXTO_PERFIL = {
    "cabecalho": ("Cabeçalho do perfil", "🖼️", "cabecalho_perfil"),
    "subtitulo": ("Frase de apresentação", "💬", "subtitulo_perfil"),
    "rodape": ("Rodapé personalizado", "🪶", "rodape_perfil"),
    "nome_rp": ("Nome RP", "👤", "ficha.nome"),
    "titulo": ("Título", "🏷️", "titulo"),
    "pegada": ("Pegada visual", "🎭", "pegada"),
    "historia": ("História", "📖", "ficha.historia"),
    "especie": ("Espécie", "🧬", "especie"),
    "faccao": ("Nome da facção", "⚔️", "faccao_nome_custom"),
    "moradia": ("Nome da moradia", "🏠", "moradia_custom"),
    "organizacao": ("Nome da organização", "👨‍👩‍👧", "organizacao_custom"),
    "parentesco": ("Parentesco e cargo", "🤝", "parentesco"),
    "empresa": ("Nome da empresa", "🏢", "empresa_custom"),
    "profissao": ("Profissão", "💼", "emprego_nome"),
    "cargo_familia": ("Cargo na organização", "🛡️", "cargo_familia"),
    "cargo_empresa": ("Cargo na empresa", "📋", "cargo_empresa"),
    "cargo_trabalho": ("Cargo profissional", "🧰", "cargo_trabalho"),
    "local": ("Localização atual", "🗺️", "local_atual"),
    "funcao_academica": ("Função acadêmica", "🎓", "funcao_academica"),
}

REGISTROS_LIMITES = {
    "vitorias_duelo": (0, 100_000, "⚔️", "Vitórias PvP"),
    "derrotas_duelo": (0, 100_000, "💀", "Derrotas PvP"),
    "missoes_completas": (0, 100_000, "📜", "Missões completas"),
    "faccao_pontos": (0, 10_000_000, "🏳️", "Pontos de facção"),
    "salario": (0, 10_000_000, "💼", "Salário"),
    "aulas_ministradas": (0, 100_000, "🎓", "Aulas ministradas"),
    "divida_manual": (0, 100_000_000, "💸", "Dívida adicional"),
}

COLECOES_PERFIL = {
    "inventario": ("Inventário", "🎒", "inventario"),
    "habilidades": ("Habilidades", "⚡", "ficha.habilidades"),
    "poderes": ("Poderes", "✨", "poderes"),
    "conquistas": ("Conquistas manuais", "🏆", "conquistas"),
    "titulos": ("Títulos colecionáveis", "👑", "titulos"),
    "diplomas": ("Diplomas", "🎓", "diplomas"),
}


def _administrador(member) -> bool:
    if getattr(member, "id", None) == IMPERADOR_ID:
        return True
    perms = getattr(member, "guild_permissions", None)
    return bool(perms and perms.administrator)


def aplicar_perfil_supremo_imperador() -> dict:
    """Garante as permissões do fundador sem sobrescrever atributos editáveis."""
    user = get_user(IMPERADOR_ID)
    user.setdefault("prestigio", "Irídio")
    user.setdefault("prestigio_chave", "iridio")
    user.setdefault("titulo", "Imperador Supremo de Tenshi")
    user["acesso_total"] = True
    user["imortal"] = True
    user["fundador"] = True
    user["admin_imperial"] = True
    user["diretor_academia"] = True
    user["professor"] = True
    user["funcao_academica"] = "Diretor e Professor Imperial"
    user["materias_professor"] = ["todas"]
    user["cargos_supremos"] = [nome for nome, _ in CARGOS_SUPREMOS]
    save_user(IMPERADOR_ID, user)
    return user


async def garantir_cargos_supremos(member: discord.Member) -> None:
    if member.id != IMPERADOR_ID:
        return
    for nome, emoji in CARGOS_SUPREMOS:
        cargo = await garantir_cargo_grupo(member.guild, nome, emoji, "autoridade_imperial")
        if cargo not in member.roles:
            await member.add_roles(cargo, reason="Autoridade absoluta do Fundador de Tenshi")
    user = get_user(member.id)
    chave = user.get("prestigio_chave", "iridio")
    if chave not in PRESTIGIOS:
        chave = "iridio"
    nome, emoji, _ = PRESTIGIOS[chave]
    await aplicar_cargo_exclusivo(member, nome, emoji, "prestigio")


def _ler_caminho(user: dict, caminho: str, padrao=None):
    atual = user
    for parte in caminho.split("."):
        if not isinstance(atual, dict):
            return padrao
        atual = atual.get(parte)
    return padrao if atual is None else atual


def _gravar_caminho(user: dict, caminho: str, valor) -> None:
    partes = caminho.split(".")
    atual = user
    for parte in partes[:-1]:
        atual = atual.setdefault(parte, {})
    if valor is None:
        atual.pop(partes[-1], None)
    else:
        atual[partes[-1]] = valor


class StatusValorModal(discord.ui.Modal, title="Alterar valor numérico"):
    operacao = discord.ui.TextInput(
        label="Operação",
        placeholder="definir, somar, subtrair ou zerar",
        default="definir",
        max_length=12,
    )
    valor = discord.ui.TextInput(label="Quantidade", placeholder="Digite um número", required=False, max_length=12)

    def __init__(self, alvo: discord.Member, atributo: str, admin_id: int, registro: bool = False):
        super().__init__()
        self.alvo = alvo
        self.atributo = atributo
        self.admin_id = admin_id
        self.registro = registro
        limites = REGISTROS_LIMITES[atributo][:3] if registro else STATUS_LIMITES[atributo]
        minimo, maximo, _ = limites
        self.valor.placeholder = f"Valor/quantidade entre {minimo} e {maximo}"

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _administrador(interaction.user):
            await interaction.response.send_message("Somente o administrador que abriu o painel pode concluir.", ephemeral=True)
            return
        operacao = self.operacao.value.strip().casefold()
        operacao = {"set": "definir", "+": "somar", "-": "subtrair", "reset": "zerar"}.get(operacao, operacao)
        if operacao not in {"definir", "somar", "subtrair", "zerar"}:
            await interaction.response.send_message("Use `definir`, `somar`, `subtrair` ou `zerar`.", ephemeral=True)
            return
        if operacao == "zerar":
            quantidade = 0
        else:
            try:
                quantidade = int(self.valor.value.strip())
            except ValueError:
                await interaction.response.send_message("Informe uma quantidade inteira válida.", ephemeral=True)
                return
        if self.registro:
            minimo, maximo, emoji, rotulo = REGISTROS_LIMITES[self.atributo]
            caminho = self.atributo
        else:
            minimo, maximo, emoji = STATUS_LIMITES[self.atributo]
            rotulo = self.atributo.replace("_", " ").title()
            caminho = f"atributos.{self.atributo}" if self.atributo in ATRIBUTOS_FICHA else self.atributo
        user = get_user(self.alvo.id)
        anterior = int(_ler_caminho(user, caminho, 0) or 0)
        if operacao == "definir":
            novo = quantidade
        elif operacao == "somar":
            novo = anterior + quantidade
        elif operacao == "subtrair":
            novo = anterior - quantidade
        else:
            novo = minimo
        if not minimo <= novo <= maximo:
            await interaction.response.send_message(
                f"O resultado de **{rotulo}** deve ficar entre **{minimo}** e **{maximo}**.",
                ephemeral=True,
            )
            return
        _gravar_caminho(user, caminho, novo)
        if self.atributo == "nivel":
            user["nivel_manual"] = novo
        save_user(self.alvo.id, user)
        await interaction.response.send_message(embed=embed_soberano_decreto(
            "Editor Completo — Valor atualizado",
            f"• **Alvo:** {self.alvo.mention}\n"
            f"• **Campo:** {emoji} {rotulo}\n"
            f"• **Operação:** {operacao.title()}\n"
            f"• **Valor anterior:** {anterior}\n"
            f"• **Novo valor:** {novo}\n"
            f"• **Limite permitido:** {minimo}–{maximo}\n"
            f"• **Administrador:** {interaction.user.mention}"
        ))


class StatusAtributoSelect(discord.ui.Select):
    def __init__(self, alvo: discord.Member, admin_id: int):
        self.alvo = alvo
        self.admin_id = admin_id
        options = [
            discord.SelectOption(
                label=atributo.replace("_", " ").title(), value=atributo, emoji=emoji,
                description=f"Valor permitido: {minimo} a {maximo}",
            )
            for atributo, (minimo, maximo, emoji) in STATUS_LIMITES.items()
        ]
        super().__init__(placeholder="2 • Atributos, progressão e finanças", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _administrador(interaction.user):
            await interaction.response.send_message("Este painel pertence a outro administrador.", ephemeral=True)
            return
        await interaction.response.send_modal(StatusValorModal(self.alvo, self.values[0], self.admin_id))


class CampoTextoModal(discord.ui.Modal, title="Editar informação do perfil"):
    def __init__(self, alvo: discord.Member, campo: str, admin_id: int):
        super().__init__()
        self.alvo = alvo
        self.campo = campo
        self.admin_id = admin_id
        rotulo, _, caminho = CAMPO_TEXTO_PERFIL[campo]
        atual = str(_ler_caminho(get_user(alvo.id), caminho, "") or "")
        self.acao = discord.ui.TextInput(
            label="Ação",
            placeholder="definir ou limpar",
            default="definir",
            max_length=10,
        )
        self.valor = discord.ui.TextInput(
            label=rotulo,
            placeholder="Digite a nova nomenclatura ou informação",
            default=atual[:1000] or None,
            required=False,
            max_length=1000,
            style=discord.TextStyle.paragraph if campo == "historia" else discord.TextStyle.short,
        )
        self.emoji = discord.ui.TextInput(
            label="Emoji do cargo (somente parentesco)",
            placeholder="Ex.: 👑, 🤝, 👨‍👩‍👧",
            required=False,
            max_length=20,
        )
        self.add_item(self.acao)
        self.add_item(self.valor)
        self.add_item(self.emoji)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _administrador(interaction.user):
            await interaction.response.send_message("Somente quem abriu o editor pode concluir.", ephemeral=True)
            return
        acao = self.acao.value.strip().casefold()
        if acao not in {"definir", "limpar"}:
            await interaction.response.send_message("A ação deve ser `definir` ou `limpar`.", ephemeral=True)
            return
        valor = self.valor.value.strip() if acao == "definir" else ""
        if acao == "definir" and not valor:
            await interaction.response.send_message("Digite o novo conteúdo ou use a ação `limpar`.", ephemeral=True)
            return
        rotulo, emoji_campo, caminho = CAMPO_TEXTO_PERFIL[self.campo]
        if self.campo == "pegada" and valor.casefold() not in {"imperial", "familia", "mafia", "enterprise"}:
            await interaction.response.send_message("Pegadas válidas: `imperial`, `familia`, `mafia`, `enterprise`.", ephemeral=True)
            return
        if self.campo == "parentesco":
            nome = valor or "Membro"
            emoji = self.emoji.value.strip() or ("👤" if not valor else "🤝")
            await interaction.response.defer(ephemeral=True)
            try:
                cargo = await aplicar_parentesco(self.alvo, nome, emoji, interaction.user.id, "editor_status")
                await interaction.followup.send(
                    f"{emoji} **{rotulo}** de {self.alvo.mention} alterado para **{nome}** ({cargo.mention}).",
                    ephemeral=True,
                )
            except discord.Forbidden:
                await interaction.followup.send("Registro salvo, mas não consegui aplicar o cargo pela hierarquia.", ephemeral=True)
            return
        user = get_user(self.alvo.id)
        anterior = _ler_caminho(user, caminho, "—")
        _gravar_caminho(user, caminho, valor.casefold() if self.campo == "pegada" else (valor or None))
        if self.campo == "profissao":
            _gravar_caminho(user, "ficha.profissao", valor or None)
        save_user(self.alvo.id, user)
        await interaction.response.send_message(embed=embed_soberano_decreto(
            "Editor Completo — Informação atualizada",
            f"• **Alvo:** {self.alvo.mention}\n• **Campo:** {emoji_campo} {rotulo}\n"
            f"• **Antes:** {anterior or '—'}\n• **Agora:** {valor or '—'}\n• **Ação:** {acao.title()}"
        ), ephemeral=True)


class CampoPerfilSelect(discord.ui.Select):
    def __init__(self, alvo: discord.Member, admin_id: int):
        self.alvo, self.admin_id = alvo, admin_id
        options = [
            discord.SelectOption(label=rotulo, value=campo, emoji=emoji, description="Renomear, definir ou limpar")
            for campo, (rotulo, emoji, _) in CAMPO_TEXTO_PERFIL.items()
        ]
        super().__init__(placeholder="1 • Identidade, nomes e vínculos", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _administrador(interaction.user):
            await interaction.response.send_message("Este editor pertence a outro administrador.", ephemeral=True)
            return
        await interaction.response.send_modal(CampoTextoModal(self.alvo, self.values[0], self.admin_id))


class RegistroNumericoSelect(discord.ui.Select):
    def __init__(self, alvo: discord.Member, admin_id: int):
        self.alvo, self.admin_id = alvo, admin_id
        options = [
            discord.SelectOption(label=rotulo, value=campo, emoji=emoji, description=f"Permitido: {minimo}–{maximo}")
            for campo, (minimo, maximo, emoji, rotulo) in REGISTROS_LIMITES.items()
        ]
        super().__init__(placeholder="3 • PvP, missões e registros", options=options, row=2)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _administrador(interaction.user):
            await interaction.response.send_message("Este editor pertence a outro administrador.", ephemeral=True)
            return
        await interaction.response.send_modal(StatusValorModal(self.alvo, self.values[0], self.admin_id, registro=True))


class ColecaoModal(discord.ui.Modal, title="Editar coleção do perfil"):
    acao = discord.ui.TextInput(
        label="Ação",
        placeholder="adicionar, remover ou limpar",
        default="adicionar",
        max_length=10,
    )
    item = discord.ui.TextInput(
        label="Item, habilidade, poder ou conquista",
        placeholder="Digite exatamente o conteúdo desejado",
        required=False,
        max_length=200,
    )

    def __init__(self, alvo: discord.Member, colecao: str, admin_id: int):
        super().__init__()
        self.alvo, self.colecao, self.admin_id = alvo, colecao, admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _administrador(interaction.user):
            await interaction.response.send_message("Somente quem abriu o editor pode concluir.", ephemeral=True)
            return
        acao = self.acao.value.strip().casefold()
        if acao not in {"adicionar", "remover", "limpar"}:
            await interaction.response.send_message("Use `adicionar`, `remover` ou `limpar`.", ephemeral=True)
            return
        item = self.item.value.strip()
        if acao != "limpar" and not item:
            await interaction.response.send_message("Informe o conteúdo que será alterado.", ephemeral=True)
            return
        rotulo, emoji, caminho = COLECOES_PERFIL[self.colecao]
        user = get_user(self.alvo.id)
        atual = list(_ler_caminho(user, caminho, []) or [])
        if acao == "adicionar":
            if item.casefold() not in {str(valor).casefold() for valor in atual}:
                atual.append(item)
        elif acao == "remover":
            atual = [valor for valor in atual if str(valor).casefold() != item.casefold()]
        else:
            atual = []
        _gravar_caminho(user, caminho, atual)
        save_user(self.alvo.id, user)
        await interaction.response.send_message(embed=embed_soberano_decreto(
            "Editor Completo — Coleção atualizada",
            f"• **Alvo:** {self.alvo.mention}\n• **Coleção:** {emoji} {rotulo}\n"
            f"• **Ação:** {acao.title()}\n• **Conteúdo:** {item or 'Todos os registros'}\n• **Total:** {len(atual)}"
        ), ephemeral=True)


class ColecaoSelect(discord.ui.Select):
    def __init__(self, alvo: discord.Member, admin_id: int):
        self.alvo, self.admin_id = alvo, admin_id
        options = [
            discord.SelectOption(label=rotulo, value=campo, emoji=emoji, description="Adicionar, remover ou limpar")
            for campo, (rotulo, emoji, _) in COLECOES_PERFIL.items()
        ]
        super().__init__(placeholder="4 • Inventário, habilidades e conquistas", options=options, row=3)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _administrador(interaction.user):
            await interaction.response.send_message("Este editor pertence a outro administrador.", ephemeral=True)
            return
        await interaction.response.send_modal(ColecaoModal(self.alvo, self.values[0], self.admin_id))


class PrestigioSelect(discord.ui.Select):
    def __init__(self, alvo: discord.Member, admin_id: int):
        self.alvo = alvo
        self.admin_id = admin_id
        options = [
            discord.SelectOption(label=nome, value=chave, emoji=emoji, description=f"Classe de prestígio {nome}")
            for chave, (nome, emoji, _) in PRESTIGIOS.items()
        ]
        super().__init__(placeholder="5 • Prestígio e classe social", options=options, row=4)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _administrador(interaction.user):
            await interaction.response.send_message("Este painel pertence a outro administrador.", ephemeral=True)
            return
        chave = self.values[0]
        nome, emoji, cor = PRESTIGIOS[chave]
        await interaction.response.defer(ephemeral=True)
        user = get_user(self.alvo.id)
        user["prestigio"] = nome
        user["prestigio_chave"] = chave
        user["prestigio_atribuido_por"] = str(interaction.user.id)
        save_user(self.alvo.id, user)
        try:
            cargo = await aplicar_cargo_exclusivo(self.alvo, nome, emoji, "prestigio")
            try:
                cargo = await cargo.edit(color=discord.Color(cor), reason=f"Classe de prestígio {nome}") or cargo
            except discord.HTTPException:
                pass
            await interaction.followup.send(f"{self.alvo.mention} recebeu **{emoji} {nome}** ({cargo.mention}).", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("Prestígio salvo, mas não consegui aplicar o cargo por hierarquia.", ephemeral=True)


class StatusPainelView(discord.ui.View):
    def __init__(self, alvo: discord.Member, admin_id: int):
        super().__init__(timeout=300)
        self.add_item(CampoPerfilSelect(alvo, admin_id))
        self.add_item(StatusAtributoSelect(alvo, admin_id))
        self.add_item(RegistroNumericoSelect(alvo, admin_id))
        self.add_item(ColecaoSelect(alvo, admin_id))
        self.add_item(PrestigioSelect(alvo, admin_id))

def economia_congelada() -> bool:
    return _economia_congelada

def is_bypass_cooldown(user_id: int) -> bool:
    return user_id in _bypass_cooldown_ids


def _log_tentativa_invasao(uid: int, cmd: str):
    """Registrar tentativa de uso de comando soberano por não-autorizado."""
    registrar_infracao(uid, "tentativa_invasao_soberana", f"Tentou usar: {cmd}", "Sistema_Segurança")


class Soberano:
    def __init__(self, bot):
        self.bot = bot

    def _verificar(self, message, cmd: str) -> bool:
        """Retorna True se autorizado. Registra tentativa se não."""
        user_data = get_user(message.author.id)
        ok = (message.author.id == IMPERADOR_ID or user_data.get("co_soberano"))
        if not ok:
            self.bot.loop.create_task(self._log_seg(message, cmd))
        return ok

    async def _log_seg(self, message, cmd: str):
        _log_tentativa_invasao(message.author.id, cmd)
        canal_logs = self._canal(message.guild, "logs-guarda")
        if canal_logs:
            e = embed_admin_doc(
                "Alerta de Segurança — Acesso Negado",
                f"• **Usuário:** {message.author.mention} (ID: {message.author.id})\n"
                f"• **Comando tentado:** `{cmd}`\n"
                f"• **Localização RP:** {getattr(message.channel, 'name', '?')}\n"
                f"• **Protocolo:** Tentativa registrada e arquivada."
            )
            await canal_logs.send(embed=e)

    def _canal(self, guild, nome: str):
        if not guild:
            return None
        for ch in guild.text_channels:
            if nome.lower() in ch.name.lower():
                return ch
        return None

    # ─── A) CONTROLE MONETÁRIO ────────────────────────────────────────────────

    async def cmd_emitir_moeda(self, message, args):
        if not self._verificar(message, "emitir-moeda"): return
        if not args:
            await message.author.send(embed_doc("Uso", "`Tenshi, emitir-moeda [quantia]`", COR_ADMIN))
            return
        try: qtd = int(args[0].replace(".", ""))
        except: await message.author.send("> ⚠️ **Operação Recusada.** Quantia inválida."); return
        user = get_user(IMPERADOR_ID)
        user["moedas"] = user.get("moedas", 0) + qtd
        save_user(IMPERADOR_ID, user)
        e = embed_soberano_decreto(
            "Emissão Monetária Imperial",
            f"• **Quantia emitida:** {fmt_moedas(qtd)}\n"
            f"• **Destino:** Tesouro Real do Soberano\n"
            f"• **Autor:** <@{IMPERADOR_ID}>"
        )
        await message.channel.send(embed=e)

    async def cmd_confiscar_fortuna(self, message, args):
        if not self._verificar(message, "confiscar-fortuna"): return
        if not message.mentions:
            await message.author.send("> ⚠️ **Operação Recusada.** Mencione o alvo."); return
        alvo = message.mentions[0]
        a_user = get_user(alvo.id)
        total  = a_user.get("moedas", 0) + a_user.get("conta_banco", 0)
        a_user["moedas"] = 0; a_user["conta_banco"] = 0
        save_user(alvo.id, a_user)
        i_user = get_user(IMPERADOR_ID)
        i_user["moedas"] = i_user.get("moedas", 0) + total
        save_user(IMPERADOR_ID, i_user)
        await message.channel.send(embed=embed_soberano_decreto(
            "Decreto de Confisco de Fortuna",
            f"• **Alvo:** {alvo.mention}\n"
            f"• **Total confiscado:** {fmt_moedas(total)}\n"
            f"• **Destino:** Tesouro Real"
        ))

    async def cmd_congelar_banco(self, message, args):
        if not self._verificar(message, "congelar-banco"): return
        if not message.mentions:
            await message.author.send("> ⚠️ **Operação Recusada.** Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id); u["banco_congelado"] = True; save_user(alvo.id, u)
        await message.channel.send(embed=embed_judicial(
            "Conta Bancária Congelada",
            f"• **Titular:** {alvo.mention}\n"
            f"• **Status:** Contas bloqueadas — saques, depósitos e transferências suspensos.\n"
            f"• **Autoridade:** Decreto Soberano"
        ))

    async def cmd_perdoar_divida(self, message, args):
        if not self._verificar(message, "perdoar-divida"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id); u["divida"] = 0; u["juros_acumulados"] = 0; save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Perdão Imperial de Dívida",
            f"• **Beneficiário:** {alvo.mention}\n• **Saldo devedor zerado** por decreto soberano."
        ))

    async def cmd_isencao_fiscal(self, message, args):
        if not self._verificar(message, "isencao-fiscal"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id); u["isento_fiscal"] = True; save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Isenção Fiscal Imperial",
            f"• **Beneficiário:** {alvo.mention}\n• Imunidade tributária permanente concedida."
        ))

    # ─── B) MANIPULAÇÃO DO RPG ────────────────────────────────────────────────

    async def cmd_set_status(self, message, args):
        if not _administrador(message.author):
            await message.channel.send(embed=embed_perigo_doc(
                "Acesso Restrito", "Somente administradores do servidor podem alterar status."
            ))
            return
        alvo = message.mentions[0] if message.mentions else message.author
        user = get_user(alvo.id)
        embed = embed_admin_doc(
            "🛠️ Editor Completo do Personagem",
            f"### {alvo.mention}\n"
            f"👤 **Nome RP:** {_ler_caminho(user, 'ficha.nome', alvo.display_name)}\n"
            f"🏷️ **Título:** {user.get('titulo') or '—'}\n"
            f"💠 **Prestígio:** {user.get('prestigio', 'Bronze')}\n"
            f"📊 **Nível:** {user.get('nivel_manual') or user.get('nivel', 1)} • "
            f"✨ **XP:** {user.get('xp', 0)} • 💥 **Poder:** {user.get('poder', 0)}\n\n"
            "**Escolha uma área nos menus:**\n"
            "`1` Identidade, nomenclaturas, vínculos e textos\n"
            "`2` Atributos, nível, XP, dinheiro e banco\n"
            "`3` PvP, missões, salário e registros\n"
            "`4` Inventário, habilidades, poderes e conquistas\n"
            "`5` Prestígio e cargo visual\n\n"
            "Nos campos numéricos use **definir**, **somar**, **subtrair** ou **zerar**. "
            "Nos textos use **definir** ou **limpar**. Sem menção, você edita o próprio perfil."
        )
        embed.set_thumbnail(url=alvo.display_avatar.url)
        await message.channel.send(embed=embed, view=StatusPainelView(alvo, message.author.id))

    async def cmd_apagar_ficha(self, message, args):
        if not self._verificar(message, "apagar-ficha"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        from database import _save, DB_FILE, _load
        dados = _load(DB_FILE)
        if str(alvo.id) in dados:
            del dados[str(alvo.id)]
            _save(DB_FILE, dados)
        await message.channel.send(embed=embed_judicial(
            "Apagamento de Ficha Imperial",
            f"• **Membro:** {alvo.mention}\n• Ficha, inventário e histórico removidos do banco de dados."
        ))

    async def cmd_conceder_item(self, message, args):
        if not self._verificar(message, "conceder-item"): return
        if not message.mentions or len(args) < 2:
            await message.author.send("> ⚠️ Uso: `Tenshi, conceder-item @user [Item] [qtd]`"); return
        alvo = message.mentions[0]
        item_nome = " ".join(args[1:-1]) if len(args) > 2 else args[1]
        qtd = int(args[-1]) if len(args) > 2 and args[-1].isdigit() else 1
        u = get_user(alvo.id)
        for _ in range(qtd):
            u.setdefault("inventario", []).append({
                "id": item_nome.lower().replace(" ", "_"), "nome": item_nome,
                "origem": "decreto_imperial", "data": datetime.utcnow().isoformat()
            })
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Concessão Imperial de Item",
            f"• **Destinatário:** {alvo.mention}\n• **Item:** {item_nome}  ×{qtd}"
        ))

    async def cmd_purificar_status(self, message, args):
        if not self._verificar(message, "purificar-status"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id)
        for campo in ("envenenado", "quarentena", "nocauteado", "bloqueado_ate", "ferido"):
            u[campo] = False if isinstance(u.get(campo), bool) else None
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Purificação de Status Imperial",
            f"• **Alvo:** {alvo.mention}\n• Todas as condições negativas removidas."
        ))

    async def cmd_imortalidade(self, message, args):
        if not self._verificar(message, "imortalidade"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]; toggle = args[1].lower() if len(args) > 1 else "on"
        u = get_user(alvo.id); u["imortal"] = toggle != "off"; save_user(alvo.id, u)
        status = "ATIVADA" if u["imortal"] else "REVOGADA"
        await message.channel.send(embed=embed_soberano_decreto(
            f"Imortalidade {status}",
            f"• **Membro:** {alvo.mention}\n• Flag de imortalidade: **{status}**"
        ))

    # ─── C) DECRETOS DE ESTADO ────────────────────────────────────────────────

    async def cmd_estado_de_sitio(self, message, args):
        if not self._verificar(message, "estado-de-sitio"): return
        if not message.guild: return
        bloqueados = 0
        for cat in message.guild.categories:
            n = cat.name.lower()
            if any(k in n for k in ("condomínio", "cidade", "mafia", "beco", "empresa")):
                try:
                    await cat.set_permissions(message.guild.default_role,
                                               send_messages=False, read_messages=False)
                    bloqueados += 1
                except Exception: pass
        await message.channel.send(embed=embed_soberano_decreto(
            "Decreto de Estado de Sítio",
            f"• **Categorias isoladas:** {bloqueados}\n"
            f"• Acesso público suspenso por ordem imperial.\n"
            f"• Canais de portões e GERAL permanecem operacionais."
        ))

    async def cmd_dissolver_mafia(self, message, args):
        if not self._verificar(message, "dissolver-mafia"): return
        if not message.guild: return
        removidos = 0
        for membro in message.guild.members:
            for cargo in membro.roles:
                if "máfia" in cargo.name.lower() or "mafia" in cargo.name.lower():
                    try: await membro.remove_roles(cargo); removidos += 1
                    except Exception: pass
        await message.channel.send(embed=embed_soberano_decreto(
            "Dissolução Compulsória da Máfia",
            f"• **Cargos removidos:** {removidos} membros afastados\n"
            f"• Categoria do subterrâneo: trancada por decreto."
        ))

    async def cmd_estatizar_casa(self, message, args):
        if not self._verificar(message, "estatizar-casa"): return
        if not args:
            await message.author.send("> ⚠️ Uso: `Tenshi, estatizar-casa [Casa-X]`"); return
        try: numero = int("".join(c for c in args[0] if c.isdigit()))
        except: await message.author.send("> ⚠️ Número inválido."); return
        from database import get_vizinhanca, save_vizinhanca, get_user, save_user
        viz = get_vizinhanca(); chave = str(numero)
        casa = viz.get(chave, {})
        dono_id = casa.get("id_dono")
        if dono_id:
            u = get_user(int(dono_id)); u["casa_condominio"] = None; save_user(int(dono_id), u)
        viz[chave] = {**casa, "id_dono": None, "lista_moradores": [], "status_aluguel": "disponivel"}
        save_vizinhanca(viz)
        await message.channel.send(embed=embed_soberano_decreto(
            f"Estatização de Imóvel — Casa-{numero}",
            f"• **Propriedade:** Casa-{numero} retornada ao controle do Trono.\n• Sem reembolso ao ex-proprietário."
        ))

    async def cmd_silenciar_geral(self, message, args):
        if not self._verificar(message, "silenciar-geral"): return
        if not message.guild: return
        for ch in message.guild.text_channels:
            if "geral" in ch.name.lower():
                try:
                    await ch.set_permissions(message.guild.default_role, send_messages=False)
                except Exception: pass
        await message.channel.send(embed=embed_soberano_decreto(
            "Silêncio Imperial no GERAL",
            "• Canal #GERAL trancado para todos os cargos, exceto Soberano e Cônjuge."
        ))

    async def cmd_anistia_geral(self, message, args):
        if not self._verificar(message, "anistia-geral"): return
        from database import _save, INFRACOES_FILE
        _save(INFRACOES_FILE, {})
        await message.channel.send(embed=embed_soberano_decreto(
            "Anistia Geral Imperial",
            "• Todos os warns, históricos criminais e registros de infração foram apagados por decreto soberano."
        ))

    # ─── D) ALTA JUSTIÇA ──────────────────────────────────────────────────────

    async def cmd_exilio_supremo(self, message, args):
        if not self._verificar(message, "exilio-supremo"): return
        if not message.mentions:
            await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        motivo = " ".join(args[1:]) if len(args) > 1 else "Decreto soberano"
        canal_pun = self._canal(message.guild, "punições")
        try: await alvo.ban(reason=f"Exílio Supremo: {motivo}")
        except Exception: pass
        if canal_pun:
            await canal_pun.send(embed=embed_judicial(
                "COMUNICADO DE EXÍLIO SUPREMO",
                f"• **Membro:** {alvo.display_name} (ID: {alvo.id})\n"
                f"• **Motivo:** {motivo}\n"
                f"• **Autoridade:** Decreto Soberano — irrevogável.\n"
                f"• **Histórico de mensagens:** Purgado."
            ))
        await message.channel.send(embed=embed_soberano_decreto(
            "Exílio Supremo Aplicado",
            f"• {alvo.display_name} banido permanentemente. Decreto arquivado."
        ))

    async def cmd_perdao_judicial(self, message, args):
        if not self._verificar(message, "perdao-judicial"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id)
        u["bloqueado_ate"] = None; u["nocauteado"] = False; u["exilado"] = False
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Perdão Judicial Imperial",
            f"• **Beneficiário:** {alvo.mention}\n• Status de isolamento e masmorra revogados imediatamente."
        ))

    async def cmd_revogar_diploma(self, message, args):
        if not self._verificar(message, "revogar-diploma"): return
        if not message.mentions or len(args) < 2:
            await message.author.send("> ⚠️ Uso: `Tenshi, revogar-diploma @user [Materia]`"); return
        alvo = message.mentions[0]; materia = " ".join(args[1:])
        u = get_user(alvo.id)
        diplomas = u.get("diplomas", [])
        u["diplomas"] = [d for d in diplomas if materia.lower() not in str(d).lower()]
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_judicial(
            "Revogação de Diploma",
            f"• **Membro:** {alvo.mention}\n• **Matéria revogada:** {materia}"
        ))

    async def cmd_cassar_conjuge(self, message, args):
        if not self._verificar(message, "cassar-conjuge"): return
        u = get_user(IMPERADOR_ID)
        conjuge_id = u.get("conjuge")
        if not conjuge_id:
            await message.channel.send("> ⚠️ Nenhum casamento imperial registrado."); return
        u["conjuge"] = None; u["taxa_casa_divisao"] = False; save_user(IMPERADOR_ID, u)
        c = get_user(int(conjuge_id))
        c["conjuge"] = None; c["co_soberano"] = False; c["taxa_casa_divisao"] = False
        save_user(int(conjuge_id), c)
        await message.channel.send(embed=embed_soberano_decreto(
            "Dissolução de Casamento Real — Decreto Sumário",
            f"• Casamento imperial dissolvido por ordem de emergência.\n"
            f"• Co-soberania do ex-cônjuge revogada."
        ))

    # ─── E) IA E CONTROLE DE CONTEÚDO ────────────────────────────────────────

    async def cmd_atualizar_diretriz(self, message, args):
        if not self._verificar(message, "atualizar-diretriz"): return
        if not args:
            await message.author.send("> ⚠️ Fornença o texto da nova diretriz."); return
        global _sys_prompt_override
        _sys_prompt_override = " ".join(args)
        await message.author.send(embed=embed_admin_doc(
            "Diretriz da IA Atualizada",
            f"• Novo system prompt configurado:\n```\n{_sys_prompt_override[:300]}\n```"
        ))
        await message.channel.send(embed=embed_soberano_decreto(
            "Diretriz da IA Atualizada",
            "• Sistema de IA recalibrado por ordem imperial."
        ))

    async def cmd_apagar_memoria_ia(self, message, args):
        if not self._verificar(message, "apagar-memoria-ia"): return
        global _memoria_ia
        _memoria_ia = []
        await message.channel.send(embed=embed_soberano_decreto(
            "Memória da IA Limpa",
            "• Histórico de contexto recente apagado. Fluxo de conversa resetado."
        ))

    async def cmd_interceptar_correio(self, message, args):
        if not self._verificar(message, "interceptar-correio"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        from database import _load
        correio_data = _load("data/correio_logs.json")
        msgs = correio_data.get(str(alvo.id), [])
        if not msgs:
            await message.author.send(f"Nenhuma correspondência registrada de {alvo.display_name} nas últimas 24h.")
            return
        e = embed_admin_doc("Interceptação de Correio — Confidencial",
            f"• **Alvo:** {alvo.display_name}\n• **Total de mensagens:** {len(msgs)}\n")
        for i, m in enumerate(msgs[-5:], 1):
            e.add_field(name=f"Carta #{i}", value=m.get("conteudo", "?")[:200], inline=False)
        await message.author.send(embed=e)

    async def cmd_forcar_cronica(self, message, args):
        if not self._verificar(message, "forçar-cronica"): return
        if len(args) < 2:
            await message.author.send("> ⚠️ Uso: `Tenshi, forçar-cronica [nicho] [tema]`"); return
        nicho = args[0]; tema = " ".join(args[1:])
        canal_nicho = self._canal(message.guild, nicho) or message.channel
        from cogs.loremaster import _gerar, SYS_LORE
        narrativa = await _gerar(
            f"Gere uma crônica urgente para o nicho '{nicho}' sobre o tema: {tema}. "
            f"Diretriz do Imperador Alloy: incorpore este tema de forma que direcione o RP.",
            SYS_LORE
        )
        e = embed_soberano_decreto(f"Crônica Forçada — {nicho.capitalize()}", narrativa)
        await canal_nicho.send(embed=e)
        await message.channel.send(embed=embed_sucesso("Crônica Enviada", f"Canal-alvo: {canal_nicho.mention}"))

    # ─── F) ENGENHARIA E MANUTENÇÃO ───────────────────────────────────────────

    async def cmd_desligar(self, message, args):
        if not self._verificar(message, "desligar"): return
        await message.channel.send(embed=embed_soberano_decreto(
            "Encerramento Seguro Iniciado",
            "• O sistema será desligado em 3 segundos por ordem imperial."
        ))
        await asyncio.sleep(3)
        await self.bot.close()

    async def cmd_forcar_pagamento(self, message, args):
        if not self._verificar(message, "forçar-pagamento"): return
        todos = get_all_users()
        pagamentos = 0
        for uid, u_data in todos.items():
            salario = u_data.get("salario", 0)
            if salario > 0:
                u_data["moedas"] = u_data.get("moedas", 0) + salario
                from database import save_user as sv
                sv(int(uid), u_data)
                pagamentos += 1
        await message.channel.send(embed=embed_soberano_decreto(
            "Folha de Pagamento Antecipada",
            f"• **Pagamentos processados:** {pagamentos} funcionários\n"
            f"• Salários depositados com efeito imediato."
        ))

    async def cmd_exportar_banco(self, message, args):
        if not self._verificar(message, "exportar-banco"): return
        import json as _json
        from database import _load, DB_FILE
        dados = _load(DB_FILE)
        texto = _json.dumps(dados, ensure_ascii=False, indent=2)
        with open("/tmp/backup_imperial.json", "w", encoding="utf-8") as f:
            f.write(texto)
        try:
            await message.author.send(
                content="Backup imperial gerado:",
                file=discord.File("/tmp/backup_imperial.json", filename="backup_imperial.json")
            )
            await message.channel.send(embed=embed_soberano_decreto(
                "Backup Exportado",
                "• Arquivo .json enviado via DM para o Soberano."
            ))
        except Exception:
            await message.channel.send("> ⚠️ Não foi possível enviar o arquivo via DM.")

    async def cmd_bypass_cooldown(self, message, args):
        if not self._verificar(message, "bypass-cooldown"): return
        if message.author.id in _bypass_cooldown_ids:
            _bypass_cooldown_ids.discard(message.author.id)
            status = "DESATIVADO"
        else:
            _bypass_cooldown_ids.add(message.author.id)
            status = "ATIVADO"
        await message.channel.send(embed=embed_soberano_decreto(
            f"Bypass de Cooldown {status}",
            f"• Todos os cooldowns para o Soberano estão agora **{status}S**."
        ))

    async def cmd_congelar_economia(self, message, args):
        if not self._verificar(message, "congelar-economia"): return
        global _economia_congelada
        _economia_congelada = not _economia_congelada
        status = "CONGELADA" if _economia_congelada else "RESTABELECIDA"
        await message.channel.send(embed=embed_soberano_decreto(
            f"Economia Imperial — {status}",
            f"• Transferências, compras e salários: **{'SUSPENSOS' if _economia_congelada else 'ATIVOS'}**"
        ))

    async def cmd_censo_imperial(self, message, args):
        if not self._verificar(message, "censo-imperial"): return
        todos = get_all_users()
        total = len(todos)
        if total == 0:
            await message.channel.send("> Nenhum cidadão registrado."); return
        soma_nivel = sum(u.get("nivel", 1) for u in todos.values())
        soma_poder = sum(u.get("poder", 0) for u in todos.values())
        soma_moedas = sum(u.get("moedas", 0) for u in todos.values())
        racas: dict = {}
        for u in todos.values():
            r = u.get("especie", "indefinida")
            racas[r] = racas.get(r, 0) + 1
        raca_txt = "\n".join(f"  • {r}: {n}" for r, n in sorted(racas.items(), key=lambda x: -x[1])[:5])
        from database import get_vizinhanca
        viz = get_vizinhanca()
        casas_ocup = sum(1 for v in viz.values() if v.get("id_dono"))
        e = embed_soberano_decreto("Censo Imperial de Tenshi",
            f"• **Total de cidadãos:** {total}\n"
            f"• **Nível médio:** {soma_nivel/total:.1f}\n"
            f"• **Poder médio:** {soma_poder/total:.0f}\n"
            f"• **Total em circulação:** {fmt_moedas(soma_moedas)}\n"
            f"• **Casas ocupadas:** {casas_ocup}/18\n\n"
            f"**Espécies mais jogadas:**\n{raca_txt}"
        )
        await message.channel.send(embed=e)

    async def cmd_reset_era(self, message, args):
        if not self._verificar(message, "reset-era"): return
        todos = get_all_users()
        arquivados = 0
        for uid, u_data in todos.items():
            conquistas   = u_data.get("conquistas", [])
            titulos      = u_data.get("titulos", [])
            diplomas     = u_data.get("diplomas", [])
            from database import _template_usuario
            novo = _template_usuario()
            novo["conquistas"] = conquistas
            novo["titulos"]    = titulos
            novo["diplomas"]   = diplomas
            from database import save_user as sv
            sv(int(uid), novo)
            arquivados += 1
        canal_hist = self._canal(message.guild, "lore-historico")
        if canal_hist:
            await canal_hist.send(embed=embed_soberano_decreto(
                f"Era Encerrada — Arquivo Histórico",
                f"• A era anterior foi arquivada. {arquivados} fichas foram resetadas.\n"
                f"• Conquistas e títulos de prestígio foram preservados."
            ))
        await message.channel.send(embed=embed_soberano_decreto(
            "Reset de Era Completo",
            f"• {arquivados} cidadãos resetados.\n• Nova temporada iniciada."
        ))

    async def cmd_irradiar(self, message, args):
        if not self._verificar(message, "irradiar"): return
        if not args:
            await message.author.send("> ⚠️ Forneça a mensagem."); return
        texto = " ".join(args)
        e = embed_soberano_decreto("Transmissão Nacional Obrigatória", texto)
        e.set_footer(text="Autenticação Soberana  •  ID Verificado do Trono")
        enviado = 0
        if message.guild:
            for cat in message.guild.categories:
                for ch in cat.text_channels:
                    if ch.permissions_for(message.guild.me).send_messages:
                        try:
                            await ch.send(embed=e); enviado += 1
                            await asyncio.sleep(0.5)
                        except Exception: pass
                        break
        await message.channel.send(embed=embed_sucesso(
            "Transmissão Concluída",
            f"• Comunicado enviado em {enviado} categorias."
        ))

    async def cmd_interdicao(self, message, args):
        if not self._verificar(message, "interdição"): return
        if not args:
            await message.author.send("> ⚠️ Forneça o nome do canal."); return
        nome = " ".join(args).lower()
        canal_alvo = None
        if message.guild:
            for ch in message.guild.text_channels:
                if nome in ch.name.lower():
                    canal_alvo = ch; break
        if not canal_alvo:
            await message.channel.send("> ⚠️ Canal não localizado."); return
        try:
            await canal_alvo.set_permissions(message.guild.default_role, send_messages=False)
            await canal_alvo.send(embed=embed_judicial(
                "Perímetro Isolado por Decreto Imperial",
                f"• Este canal foi trancado por ordem soberana.\n"
                f"• Toda comunicação aqui está suspensa até nova diretriz."
            ))
        except Exception as ex:
            await message.channel.send(f"> ⚠️ Permissão negada: {ex}")
            return
        await message.channel.send(embed=embed_soberano_decreto(
            "Interdição de Canal Aplicada",
            f"• **Canal:** {canal_alvo.mention} — escrita bloqueada."
        ))

    def get_sys_prompt_override(self) -> str | None:
        return _sys_prompt_override
