import discord
import os
import re
from typing import Any, Iterable

DISCORD_CONTENT_LIMIT = 2000
EMBED_TITLE_LIMIT = 256
EMBED_DESCRIPTION_LIMIT = 4096
EMBED_FOOTER_LIMIT = 2048
EMBED_AUTHOR_LIMIT = 256
EMBED_FIELD_NAME_LIMIT = 256
EMBED_FIELD_VALUE_LIMIT = 1024
EMBED_FIELD_LIMIT = 25
EMBED_TOTAL_LIMIT = 6000
EMBEDS_PER_MESSAGE_LIMIT = 10
EMBED_PAGE_DESCRIPTION_LIMIT = 1800

_ORIGINAL_MESSAGEABLE_SEND = None
_ORIGINAL_WEBHOOK_SEND = None
_ORIGINAL_INTERACTION_RESPONSE_SEND = None


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _trim_at_word(text: Any, limit: int) -> str:
    text = _as_text(text)
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]

    cut = max(
        text.rfind(" ", 0, limit - 1),
        text.rfind("\n", 0, limit - 1),
        text.rfind("\t", 0, limit - 1),
    )
    if cut < max(16, int(limit * 0.55)):
        cut = limit - 1
    return text[:cut].rstrip() + "…"


def _split_long_line(line: str, limit: int) -> list[str]:
    if len(line) <= limit:
        return [line]

    parts: list[str] = []
    remaining = line
    while len(remaining) > limit:
        cut = max(
            remaining.rfind(" ", 0, limit),
            remaining.rfind("\t", 0, limit),
            remaining.rfind("/", 0, limit),
            remaining.rfind("-", 0, limit),
        )
        if cut < max(16, int(limit * 0.55)):
            cut = limit
        parts.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        parts.append(remaining)
    return parts


def split_text(text: Any, limit: int = EMBED_DESCRIPTION_LIMIT) -> list[str]:
    """Divide texto grande sem quebrar palavras e tenta preservar blocos Markdown."""
    text = _as_text(text)
    if not text:
        return [""]
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    in_code_block = False
    code_lang = ""
    fence_re = re.compile(r"^\s*```(\w+)?")

    def flush():
        nonlocal current
        if current:
            chunks.append(current.rstrip())
            current = ""

    for raw_line in text.splitlines(keepends=True):
        line_parts = _split_long_line(raw_line, max(1, limit - 16))
        for part in line_parts:
            fence = fence_re.match(part)
            extra_close = 4 if in_code_block else 0
            if current and len(current) + len(part) + extra_close > limit:
                if in_code_block and not current.rstrip().endswith("```"):
                    current = current.rstrip() + "\n```"
                flush()
                if in_code_block:
                    current = f"```{code_lang}\n" if code_lang else "```\n"

            if len(part) > limit:
                for small in _split_long_line(part, limit):
                    if current and len(current) + len(small) > limit:
                        flush()
                    current += small
                    if len(current) >= limit:
                        flush()
                continue

            current += part

            if fence:
                marker = part.strip()
                if marker.startswith("```"):
                    if in_code_block:
                        in_code_block = False
                        code_lang = ""
                    else:
                        in_code_block = True
                        code_lang = fence.group(1) or ""

    flush()
    return chunks or [""]


def split_message_content(content: Any, limit: int = DISCORD_CONTENT_LIMIT) -> list[str]:
    return split_text(content, limit)


def _embed_text_length(embed: discord.Embed) -> int:
    total = len(_as_text(embed.title)) + len(_as_text(embed.description))
    total += len(_as_text(embed.footer.text)) if embed.footer else 0
    total += len(_as_text(embed.author.name)) if embed.author else 0
    for field in embed.fields:
        total += len(_as_text(field.name)) + len(_as_text(field.value))
    return total


def _embed_shell(embed: discord.Embed) -> discord.Embed:
    data = embed.to_dict()
    data.pop("description", None)
    data.pop("fields", None)
    clone = discord.Embed.from_dict(data)

    if clone.title:
        clone.title = _trim_at_word(clone.title, EMBED_TITLE_LIMIT)

    footer_text = _as_text(clone.footer.text) if clone.footer else ""
    if footer_text:
        clone.set_footer(
            text=_trim_at_word(footer_text, EMBED_FOOTER_LIMIT),
            icon_url=getattr(clone.footer, "icon_url", None),
        )

    author_name = _as_text(clone.author.name) if clone.author else ""
    if author_name:
        clone.set_author(
            name=_trim_at_word(author_name, EMBED_AUTHOR_LIMIT),
            url=getattr(clone.author, "url", None),
            icon_url=getattr(clone.author, "icon_url", None),
        )

    return clone


def _field_parts(field) -> list[tuple[str, str, bool]]:
    raw_name = _as_text(field.name) or "\u200b"
    value = _as_text(field.value) or "\u200b"
    name_chunks = split_text(raw_name, EMBED_FIELD_NAME_LIMIT)
    name = name_chunks[0] or "\u200b"
    if len(name_chunks) > 1:
        overflow_name = "\n".join(name_chunks[1:])
        value = f"Nome completo do campo: {overflow_name}\n{value}"
    chunks = split_text(value, EMBED_FIELD_VALUE_LIMIT)
    parts: list[tuple[str, str, bool]] = []
    for idx, chunk in enumerate(chunks):
        field_name = name
        if idx:
            suffix = f" (continuação {idx + 1})"
            field_name = _trim_at_word(f"{name}{suffix}", EMBED_FIELD_NAME_LIMIT)
        parts.append((field_name, chunk or "\u200b", bool(field.inline)))
    return parts


def split_embed(embed: discord.Embed) -> list[discord.Embed]:
    """Valida e divide um embed para respeitar todos os limites do Discord."""
    shell = _embed_shell(embed)
    overhead = _embed_text_length(shell)
    description_limit = max(512, min(EMBED_PAGE_DESCRIPTION_LIMIT, EMBED_TOTAL_LIMIT - overhead))
    description_chunks = split_text(embed.description or "", description_limit)
    field_parts: list[tuple[str, str, bool]] = []
    for field in embed.fields:
        field_parts.extend(_field_parts(field))

    embeds: list[discord.Embed] = []
    for chunk in description_chunks:
        clone = _embed_shell(embed)
        clone.description = chunk or None
        embeds.append(clone)

    if not embeds:
        embeds.append(_embed_shell(embed))

    current = embeds[-1]
    for name, value, inline in field_parts:
        field_size = len(name) + len(value)
        would_overflow = (
            len(current.fields) >= EMBED_FIELD_LIMIT
            or _embed_text_length(current) + field_size > EMBED_TOTAL_LIMIT
        )
        if would_overflow:
            current = _embed_shell(embed)
            embeds.append(current)
        current.add_field(name=name, value=value, inline=inline)

    safe_embeds: list[discord.Embed] = []
    for item in embeds:
        if len(item.fields) > EMBED_FIELD_LIMIT:
            item._fields = item._fields[:EMBED_FIELD_LIMIT]
        if item.description and len(item.description) > EMBED_DESCRIPTION_LIMIT:
            for desc in split_text(item.description, EMBED_DESCRIPTION_LIMIT):
                clone = _embed_shell(item)
                clone.description = desc
                safe_embeds.append(clone)
        else:
            safe_embeds.append(item)
    return safe_embeds


class EmbedContinuacaoView(discord.ui.View):
    """Mostra textos longos em uma única mensagem, com navegação por botões."""

    def __init__(self, paginas: list[discord.Embed]):
        super().__init__(timeout=300)
        self.paginas = paginas
        self.atual = 0
        self._atualizar_botoes()

    def _atualizar_botoes(self):
        self.voltar.disabled = self.atual == 0
        self.continuar.disabled = self.atual >= len(self.paginas) - 1
        self.indicador.label = f"Parte {self.atual + 1}/{len(self.paginas)}"
        self.continuar.label = "Mostrar continuação" if self.atual == 0 else "Próxima parte"

    @discord.ui.button(label="Voltar", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.atual = max(0, self.atual - 1)
        self._atualizar_botoes()
        await interaction.response.edit_message(embed=self.paginas[self.atual], view=self)

    @discord.ui.button(label="Parte 1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def indicador(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Mostrar continuação", emoji="▶️", style=discord.ButtonStyle.primary)
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.atual = min(len(self.paginas) - 1, self.atual + 1)
        self._atualizar_botoes()
        await interaction.response.edit_message(embed=self.paginas[self.atual], view=self)


def _payload_paginado(content: Any, safe_embeds: list[discord.Embed], kwargs: dict[str, Any]) -> dict[str, Any] | None:
    if len(safe_embeds) <= 1 or kwargs.get("view") is not None:
        return None
    if content is not None and len(_as_text(content)) > DISCORD_CONTENT_LIMIT:
        return None
    payload = dict(kwargs)
    if content is not None:
        payload["content"] = content
    payload["embed"] = safe_embeds[0]
    payload["view"] = EmbedContinuacaoView(safe_embeds)
    return payload


def _strip_non_reusable_send_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    clean = dict(kwargs)
    for key in ("file", "files", "view", "stickers", "reference", "mention_author"):
        clean.pop(key, None)
    return clean


def _build_safe_send_payloads(content: Any, safe_embeds: list[discord.Embed], kwargs: dict[str, Any]) -> list[dict[str, Any]]:
    content_chunks = split_message_content(content, DISCORD_CONTENT_LIMIT) if content else [None]
    payloads: list[dict[str, Any]] = []
    first = True

    if not safe_embeds:
        for chunk in content_chunks:
            send_kwargs = dict(kwargs) if first else _strip_non_reusable_send_kwargs(kwargs)
            if chunk is not None:
                send_kwargs["content"] = chunk
            payloads.append(send_kwargs)
            first = False
        return payloads

    embed_batches = [
        safe_embeds[i : i + EMBEDS_PER_MESSAGE_LIMIT]
        for i in range(0, len(safe_embeds), EMBEDS_PER_MESSAGE_LIMIT)
    ]

    if content_chunks != [None]:
        for chunk_index, chunk in enumerate(content_chunks):
            send_kwargs = dict(kwargs) if first else _strip_non_reusable_send_kwargs(kwargs)
            send_kwargs["content"] = chunk
            if chunk_index == 0 and embed_batches:
                batch = embed_batches.pop(0)
                if len(batch) == 1:
                    send_kwargs["embed"] = batch[0]
                else:
                    send_kwargs["embeds"] = batch
            payloads.append(send_kwargs)
            first = False

    for batch in embed_batches:
        send_kwargs = dict(kwargs) if first else _strip_non_reusable_send_kwargs(kwargs)
        if len(batch) == 1:
            send_kwargs["embed"] = batch[0]
        else:
            send_kwargs["embeds"] = batch
        payloads.append(send_kwargs)
        first = False

    return payloads or [dict(kwargs)]


async def _try_send(original_send, target, *args, **kwargs):
    try:
        return await original_send(target, *args, **kwargs)
    except discord.Forbidden as exc:
        print(f"[DISCORD-SEND] Sem permissao para enviar mensagem em {target}: {exc}")
    except discord.NotFound as exc:
        print(f"[DISCORD-SEND] Canal/mensagem nao encontrado ao enviar em {target}: {exc}")
    except discord.HTTPException as exc:
        print(f"[DISCORD-SEND] HTTPException ao enviar mensagem em {target}: {exc}")
    return None


async def _safe_send_with_original(original_send, target, *args, **kwargs):
    positional = list(args)
    content = positional.pop(0) if positional else kwargs.pop("content", None)
    embed = kwargs.pop("embed", None)
    embeds = kwargs.pop("embeds", None)

    raw_embeds: list[discord.Embed] = []
    if embed is not None:
        raw_embeds.append(embed)
    if embeds:
        raw_embeds.extend(list(embeds))

    safe_embeds: list[discord.Embed] = []
    for item in raw_embeds:
        safe_embeds.extend(split_embed(item))

    paginado = _payload_paginado(content, safe_embeds, kwargs)
    if paginado is not None:
        return await _try_send(original_send, target, *positional, **paginado)

    first_message = None
    for send_kwargs in _build_safe_send_payloads(content, safe_embeds, kwargs):
        msg = await _try_send(original_send, target, *positional, **send_kwargs)
        first_message = first_message or msg

    return first_message


async def _safe_interaction_response_send(original_send, response, *args, **kwargs):
    positional = list(args)
    content = positional.pop(0) if positional else kwargs.pop("content", None)
    embed = kwargs.pop("embed", None)
    embeds = kwargs.pop("embeds", None)

    raw_embeds: list[discord.Embed] = []
    if embed is not None:
        raw_embeds.append(embed)
    if embeds:
        raw_embeds.extend(list(embeds))

    safe_embeds: list[discord.Embed] = []
    for item in raw_embeds:
        safe_embeds.extend(split_embed(item))

    paginado = _payload_paginado(content, safe_embeds, kwargs)
    if paginado is not None:
        return await _try_send(original_send, response, *positional, **paginado)

    payloads = _build_safe_send_payloads(content, safe_embeds, kwargs)
    if not payloads:
        return None

    first = await _try_send(original_send, response, *positional, **payloads[0])
    interaction = getattr(response, "_parent", None)
    followup = getattr(interaction, "followup", None)
    if followup is None:
        if len(payloads) > 1:
            print("[DISCORD-SEND] Interacao sem followup; partes extras nao puderam ser enviadas.")
        return first

    for payload in payloads[1:]:
        await _try_send(_ORIGINAL_WEBHOOK_SEND or discord.Webhook.send, followup, **payload)
    return first


async def safe_send_embed(target, embed: discord.Embed | None = None, *, embeds: Iterable[discord.Embed] | None = None, content: Any = None, **kwargs):
    """Envia embeds/texto com validação de limites e logs sem derrubar o bot."""
    original = _ORIGINAL_MESSAGEABLE_SEND or discord.abc.Messageable.send
    return await _safe_send_with_original(original, target, content, embed=embed, embeds=embeds, **kwargs)


def install_discord_safety_patch():
    """Faz todo channel.send/embed passar pela camada segura do projeto."""
    global _ORIGINAL_MESSAGEABLE_SEND, _ORIGINAL_WEBHOOK_SEND, _ORIGINAL_INTERACTION_RESPONSE_SEND
    if _ORIGINAL_MESSAGEABLE_SEND is not None:
        return

    _ORIGINAL_MESSAGEABLE_SEND = discord.abc.Messageable.send
    _ORIGINAL_WEBHOOK_SEND = discord.Webhook.send
    _ORIGINAL_INTERACTION_RESPONSE_SEND = discord.InteractionResponse.send_message

    async def _patched_send(self, *args, **kwargs):
        content = kwargs.get("content", args[0] if args else None)
        has_long_content = content is not None and len(_as_text(content)) > DISCORD_CONTENT_LIMIT
        if "embed" in kwargs or "embeds" in kwargs or has_long_content:
            return await _safe_send_with_original(_ORIGINAL_MESSAGEABLE_SEND, self, *args, **kwargs)
        return await _try_send(_ORIGINAL_MESSAGEABLE_SEND, self, *args, **kwargs)

    async def _patched_webhook_send(self, *args, **kwargs):
        content = kwargs.get("content", args[0] if args else None)
        has_long_content = content is not None and len(_as_text(content)) > DISCORD_CONTENT_LIMIT
        if "embed" in kwargs or "embeds" in kwargs or has_long_content:
            return await _safe_send_with_original(_ORIGINAL_WEBHOOK_SEND, self, *args, **kwargs)
        return await _try_send(_ORIGINAL_WEBHOOK_SEND, self, *args, **kwargs)

    async def _patched_interaction_send_message(self, *args, **kwargs):
        content = kwargs.get("content", args[0] if args else None)
        has_long_content = content is not None and len(_as_text(content)) > DISCORD_CONTENT_LIMIT
        if "embed" in kwargs or "embeds" in kwargs or has_long_content:
            return await _safe_interaction_response_send(_ORIGINAL_INTERACTION_RESPONSE_SEND, self, *args, **kwargs)
        return await _try_send(_ORIGINAL_INTERACTION_RESPONSE_SEND, self, *args, **kwargs)

    discord.abc.Messageable.send = _patched_send
    discord.Webhook.send = _patched_webhook_send
    discord.InteractionResponse.send_message = _patched_interaction_send_message

# ── Imperador ─────────────────────────────────────────────────────────────────
IMPERADOR_ID = 619302798751694849

PREFIXO = "tenshi,"
COOLDOWN_TREINO = 30 * 60
COOLDOWN_MISSAO = 60 * 60

# ── Paletas por pegada ────────────────────────────────────────────────────────
CORES_PEGADA = {
    "imperial":   0x2B0A3D,   # roxo profundo
    "familia":    0x6B0000,   # vinho escuro
    "mafia":      0x0D0D0D,   # preto absoluto
    "enterprise": 0x0A1628,   # azul marinho
}

CORES_DESTAQUE = {
    "imperial":   0x8A2BE2,   # violeta brilhante
    "familia":    0xC0392B,   # vermelho
    "mafia":      0x2C2C2C,   # cinza escuro
    "enterprise": 0x1B4F72,   # azul aço
}

EMOJI_PEGADA = {
    "imperial":   "🏛️",
    "familia":    "👨‍👩‍👧",
    "mafia":      "🖤",
    "enterprise": "🏢",
}

NOME_PEGADA = {
    "imperial":   "Império de Tenshi",
    "familia":    "Família",
    "mafia":      "Máfia",
    "enterprise": "Tenshi Enterprise",
}

# ── Separadores decorativos ───────────────────────────────────────────────────
SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SEP_LIGHT = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
RODAPE_IMPERIAL = "⚜️ Desenvolvido por Alloy Tenshi, O Imperador"


def embed_imperial(titulo: str, descricao: str, cor: int = 0x2B0A3D) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


def embed_pegada(titulo: str, descricao: str, pegada: str = "imperial") -> discord.Embed:
    cor = CORES_PEGADA.get(pegada, 0x2B0A3D)
    emoji = EMOJI_PEGADA.get(pegada, "🏛️")
    nome = NOME_PEGADA.get(pegada, "Tenshi")
    embed = discord.Embed(title=f"{emoji} {titulo}", description=descricao, color=cor)
    embed.set_footer(text=f"{emoji} {nome}  •  {RODAPE_IMPERIAL}")
    return embed


def calcular_nivel(xp: int):
    nivel = 1
    xp_necessario = 100
    xp_restante = xp
    while xp_restante >= xp_necessario:
        xp_restante -= xp_necessario
        nivel += 1
        xp_necessario = int(xp_necessario * 1.5)
    return nivel, xp_necessario - xp_restante


def barra_progresso(atual: int, maximo: int, tamanho: int = 12) -> str:
    if maximo == 0:
        return "░" * tamanho
    preenchido = int((atual / maximo) * tamanho)
    return "█" * preenchido + "░" * (tamanho - preenchido)


def _site_url_padrao() -> str:
    public_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if public_domain:
        return f"https://{public_domain}"
    port = os.environ.get("PORT") or os.environ.get("SITE_PORT") or "8081"
    return f"http://localhost:{port}"


SITE_URL = os.environ.get("TENSHI_SITE_URL") or _site_url_padrao()

AJUDA_TEXTO = f"""
{SEP}
**🏛️ PERGAMINHOS IMPERIAIS DE TENSHI**
*Prefixos: `tenshi comando` ou `Tenshi, comando`  •  `/ajuda`, `/nota`, `/aviso`, `/historico` e `/info`*
🌐 **Site oficial:** {SITE_URL}
{SEP}

**🎭 Identidade & Perfil**
`status` `ficha` `criar-ficha` `pegada [tema]` `inventario` `conquistas` `especies` `viajar [local]` `local`
`mundo` *(atlas por continente/país/cidade)* `viagem-atual` `terminar-viagem`

**✨ Poderes de RP**
`poderes` `meus-poderes`

**⚡ Jornada Imperial**
`treinar [ação]` `missao` `meditar` `descansar` `interagir [ação]` `dado [d4/d6/d10/d20/d100]`
`trabalhar` `emprego` `carreiras` `regras-trabalho` `profissao [classe]` `clima`

**📖 LoreMaster IA** *(Gerado por IA)*
`cronica [militar/politico/esoterico/mafia/enterprise]`
`evento-lore` `oraculo [pergunta]` `falar [NPC]` `lore-historico` `quadro-avisos`
`biblioteca-imperial` `documento [pdf]` `memoria-imperial [tema]`
`aula-imperial [tema]` `missao-historica [tema]` `juramento-tenshi [tema]`
`protocolo-imperial [situação]` `quiz-imperial`

**🔮 Místico**
`tarot` `runa` `astros` `destino @user` `sacrificio [item]` `ritual-protecao`

**⚔️ Combate Narrativo**
`duelo @user` `aceitar-duelo` `basquete @user` `futebol @user` `dado [tipo]`
`invocar-chefe [criatura]` *(admin)* `invasao` *(admin)*

**💰 Economia & Comércio**
`carteira` `mercado` `mercado-negro` `comprar [item]` `leilao [item]` `sorteio-real` `trabalhar` `emprego`
*O mercado possui 30 itens; equipamentos avançados exigem nível, poder, mana, item anterior ou cargo.*

**🏦 Banco & Finanças**
`banco` `depositar [v]` `sacar [v]` `transferir @user [v]` `emprestimo [v]` `pagar-divida` `historico`
`poupanca [v]` `comprar-acoes [v]` `seguro-vida` `aposentar`

**🏠 Propriedades & Condomínio**
`casas` `minha-casa` `vender-casa` `portaria` `residencia` `convidar @user` `expulsar @user`
`devolver-casa` `moradores` `relaxar` `fofoca` `trancar-casa` `destrancar-casa`
*A portaria oferece 50 casas; canais privados são criados automaticamente após compra ou aluguel.*
`sincronizar-condominio` *(admin; gera/vincula os 50 canais mantendo a estética existente)*
`organizar-canais` *(admin; cria canais temáticos, jornais e atlas mundial)*

**🚗 Garagem, Esportes & Pets**
`garagem` `vender-veiculo` `abastecer [v]` `basquete @user` `futebol @user`
`pet-shop` `meu-pet` `vender-pet` `pool-party` *(admin)*
`zoologico` *(24 habitats com tópicos)* `interagir-local` `terminar-interacao`

**💑 Social & Cotidiano**
`pedido @user` `pedido-real @user` `cerimonia @parceiro`
`iniciar-cerimonia @noivo1 @noivo2` *(Ritualista escolhido; celebração por Tenshi IA)*
`rito-real @rei @rainha` `registro-casamento @user` `divorcio`
`casar` `abandonar-preparacao` `cancelar-casamento` `anular-casamento`
`lavanderia` `sintetizar [item]` `cartaz [filme]`
`psicologo [texto]` `beber [bebida]` `jornal-cotidiano` `correio` `estacoes`
`entrevista [cargo]` `socorrer @user` `vdd`
`cassino` *(10 jogos de aposta em tópicos privados)*

**🕵️ Crime & Inteligência**
`assaltar @user` `mercado-negro-beco` `subornar-porteiro @user`
`grampear-call` `iniciar-festa [local]` `registrar-perola [msg]` `chat [pedido]`
`jornal-policial` *(ocorrências reais do RPG + informes fictícios)*

**⚖️ Jurídico & Clero**
`ficha-criminal @user` `warn @user` `perdoar-aviso @user` `mandado @user`
`pagar-fianca` `imunidade-diplomatica` `padre [rito]` `sindicancia @user`
`consultar-lei [tema]` `parecer-ia [caso]` `plano-admin [objetivo]`
`laudo-medico` `desintoxicacao` `doacao-sangue` `diagnostico-ia`
`concurso-publico` *(provas para cargos jurídicos e policiais)*

**🌍 Geopolítica & Estado**
`dominar [canal]` `territorio` `rebeliao` `visto` `cidadania` `exilio @user`
`auditoria-bancaria` `necrolo` `aposentar` `buscar-protocolo`
`set-era [nome]` `era` `decreto-marcial [ação]` `aconselhar-estrategia [sit.]`

**🏗️ Infraestrutura Crítica**
`status-energia` `inflacao` `comprar-acoes [v]` `poupanca [v]`
`checar-cameras` `biometria` `rastrear-perfil @user` `enviar-carga [tipo]`
`titulo-propriedade` `alugar-comercio`

**🎓 Tenshi Academy**
`grade-academia` `certificado [curso]` `aptidao-academica [curso/resposta]`
`matricular [mat.]` `trancar-matricula [mat.]` `presenca [mat.]` `iniciar-aula [mat.]`
`ler-apostila [mat.]` `prestar-exame [mat.]` `historico-escolar` `segunda-via-diploma`
`entrar-clube [nome]` `cofre-clube`
`professor [@user]` *(admin; define função e disciplinas)* `professores`
`ministrar-aula [mat.] [tema]` *(corpo docente; aula com IA e presença)*

**🏢 Empresa**
`empresa criar/info/contratar/demitir/funcionarios/pagar` `carreiras` `emprego legal [id]`

**👨‍👩‍👧 Família, Máfia & Facções**
`familia criar/entrar/info/membros/missao/depositar` `entrar [facção]` `ranking`
`parentesco [@user]` *(admin; lista de filhos, irmãos, cunhad@, sobrinhos, netos e outros)*
`meu-parentesco [@user]` `lista-parentescos` `arvore-familiar`
`painel-admin` *(admin; painel completo para gerenciar família e parentesco)*
`casar-admin @user` *(Imperador; casa e concede acesso admin ao cônjuge)*
*O fundador é Patriarca; novos membros recebem Membro e casamentos derivam vínculos por afinidade.*

**🛡️ Moderação Imperial** *(Admin)*
`decreto [msg]` `promover @user [cargo]` `criar-cargo [emoji] [nome]` `criar-secoes-cargos`
`punir-audacia @user` `julgamento @user`
`cargos-servidor` `mapear-cargos` `auditoria-cargos-ia` `cargo-info @cargo`
`funcao-cargo @cargo [texto]` `publicar-mapa-cargos`
`auditoria-permissoes` `corrigir-permissoes-bot` `mapa-canais`
`aplicar-perfil-canal #canal [perfil]`
`masmorra-prender @user [min]` `exilar @user` `anistia-real` `trancar-portoes`
`tesouro [v]` `veto [ação]` `ban` `kick` `mute [min]` `unmute @user` `unban [ID]`
`clear [n]` `slowmode [seg]` `warn @user` `aviso @user [motivo]` `nota @user [texto]`
`notas @user` `info @user` `historico @user`
**👑 Prerrogativas Soberanas** *(Imperador)*
`emitir-moeda` `confiscar-fortuna` `congelar-banco` `perdoar-divida` `isencao-fiscal`
`set-status [@user]` *(editor completo: nomes, textos, números, coleções e prestígio)*
`apagar-ficha` `conceder-item` `imortalidade`
`estado-de-sitio` `dissolver-mafia` `anistia-geral` `exilio-supremo`
`atualizar-diretriz` `apagar-memoria-ia` `forcar-cronica` `censo-imperial`
`reset-era` `irradiar [msg]` `congelar-economia` `exportar-banco` `desligar`

**🔧 Utilitários**
`top` `servidor` `ping` `backup` `bandeira` `brasao` `historia-tenshi` `base-historica`
`status-ia` `aniversario` `ajuda`

**�️ Proteção Imperial - Finalização UPP** *(Admin)*
`protecao-imperial` *(painel de configuração)* `ativar-protecao` `desativar-protecao`
`confianca @user` `remover-confianca @user` `bloquear-servidor [id]` `desbloquear-servidor [id]`
`atividade-suspeita [@user]` *(verifica comportamento suspeito)*

**🤝 Sistema de Parcerias - Finalização UPP** *(Admin)*
`parceria [link-convite]` *(gera embed de parceria com IA)* `historico-parcerias`

**🔒 Moderação de Conteúdo - Finalização UPP** *(Admin)*
`config-moderacao` *(painel de configuração)* `bloquear-link [url]` `desbloquear-link [url]`
`adicionar-dominio-confianca [dominio]` `remover-dominio-confianca [dominio]`

**�📚 Comandos Complementares**
`confirmar` `cancelar` `meu-lar-cond` `cronica-cond` `descansar-lazer` `auditoria-cargos`
`clima-atual` `criar-correio` `purificar-status` `historico-imovel` `bans-lista` `confiscar-veiculo`
`interdicao` `pedir-emprestimo` `quitar` `quitar-divida` `lavar` `titulo-divida` `presença`

**👑 Administração Avançada** *(Imperador/Admin)*
`estatizar-casa` `silenciar-geral` `perdao-judicial` `revogar-diploma` `cassar-conjuge`
`interceptar-correio` `forçar-cronica` `forçar-pagamento` `bypass-cooldown`
`interditar-escola` `aprovação-forçada` `estatizar-cofre-clube` `zerar-historico-academico`
`auditoria-geral-banco` `expurgar-fichas-inativas` `reset-parcial-economia` `decreto-climatico`
{SEP}
*🌐 Guia completo: {SITE_URL}*
*{RODAPE_IMPERIAL}*
"""
