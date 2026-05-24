import discord
from database import get_user, save_user, get_empresas, get_familias, get_casas
from utils import (embed_imperial, CORES_PEGADA, EMOJI_PEGADA, NOME_PEGADA,
                   calcular_nivel, IMPERADOR_ID, SEP, RODAPE_IMPERIAL,
                   barra_progresso, CORES_DESTAQUE)

# Rastreia a última mensagem de status enviada por usuário
# para poder apagá-la antes de enviar uma nova
_status_msgs: dict = {}  # user_id -> discord.Message

PEGADAS_VALIDAS = ["imperial", "familia", "mafia", "enterprise"]

TITULOS_NIVEL = {
    "imperial":   ["Cidadão", "Escudeiro", "Soldado Imperial", "Veterano", "Guardião", "Cavaleiro", "Lorde", "Duque", "Príncipe Sombrio", "Herdeiro do Trono", "Soberano Eterno"],
    "familia":    ["Associado", "Membro", "Soldato", "Capo", "Consigliere", "Underboss", "Don Adjunto", "Patriarca"],
    "mafia":      ["Recruta", "Soldado", "Enforcer", "Tenente", "Capo", "Underboss", "Consigliere", "Il Don Supremo"],
    "enterprise": ["Estagiário", "Analista", "Especialista", "Gerente", "Diretor", "VP Sênior", "C-Level", "Chairman Imperial"],
}

def _titulo_por_nivel(nivel: int, pegada: str) -> str:
    titulos = TITULOS_NIVEL.get(pegada, TITULOS_NIVEL["imperial"])
    idx = min((nivel - 1) // 3, len(titulos) - 1)
    return titulos[max(0, idx)]


# ─────────────────────────────────────────────────────────────────────────────
# View de navegação do Status
# ─────────────────────────────────────────────────────────────────────────────
class StatusView(discord.ui.View):
    def __init__(self, bot, user_id: int, member: discord.Member | discord.User, pagina: str = "perfil"):
        super().__init__(timeout=120)
        self.bot      = bot
        self.user_id  = user_id
        self.member   = member
        self.pagina   = pagina
        self._update_buttons()

    def _update_buttons(self):
        self.clear_items()
        p = self.pagina
        btn_perfil    = discord.ui.Button(label="🏛️ Perfil",      style=discord.ButtonStyle.primary if p == "perfil"    else discord.ButtonStyle.secondary, custom_id="p_perfil")
        btn_inv       = discord.ui.Button(label="🎒 Inventário",  style=discord.ButtonStyle.primary if p == "inventario" else discord.ButtonStyle.secondary, custom_id="p_inv")
        btn_conquistas= discord.ui.Button(label="🏆 Conquistas",  style=discord.ButtonStyle.primary if p == "conquistas" else discord.ButtonStyle.secondary, custom_id="p_conq")
        btn_financeiro= discord.ui.Button(label="💰 Finanças",    style=discord.ButtonStyle.primary if p == "financas"   else discord.ButtonStyle.secondary, custom_id="p_fin")

        btn_perfil.callback     = self._cb_perfil
        btn_inv.callback        = self._cb_inv
        btn_conquistas.callback = self._cb_conquistas
        btn_financeiro.callback = self._cb_financeiro

        for btn in [btn_perfil, btn_inv, btn_conquistas, btn_financeiro]:
            self.add_item(btn)

    async def _cb_perfil(self, interaction: discord.Interaction):
        self.pagina = "perfil"
        self._update_buttons()
        embed = await _build_perfil_embed(self.bot, self.member)
        await interaction.response.edit_message(embed=embed, view=self)

    async def _cb_inv(self, interaction: discord.Interaction):
        self.pagina = "inventario"
        self._update_buttons()
        embed = _build_inventario_embed(self.member)
        await interaction.response.edit_message(embed=embed, view=self)

    async def _cb_conquistas(self, interaction: discord.Interaction):
        self.pagina = "conquistas"
        self._update_buttons()
        embed = _build_conquistas_embed(self.member)
        await interaction.response.edit_message(embed=embed, view=self)

    async def _cb_financeiro(self, interaction: discord.Interaction):
        self.pagina = "financas"
        self._update_buttons()
        embed = _build_financeiro_embed(self.member)
        await interaction.response.edit_message(embed=embed, view=self)


# ─────────────────────────────────────────────────────────────────────────────
# Builders de embed por aba
# ─────────────────────────────────────────────────────────────────────────────
async def _build_perfil_embed(bot, member: discord.Member | discord.User) -> discord.Embed:
    user      = get_user(member.id)
    nivel, xp_prox = calcular_nivel(user["xp"])
    user["nivel"] = nivel
    pegada    = user.get("pegada", "imperial")
    cor       = CORES_PEGADA.get(pegada, 0x2B0A3D)
    emoji_p   = EMOJI_PEGADA.get(pegada, "🏛️")
    nome_p    = NOME_PEGADA.get(pegada, "Tenshi")
    eh_imp    = member.id == IMPERADOR_ID

    titulo    = user.get("titulo") or _titulo_por_nivel(nivel, pegada)
    xp_atual  = user["xp"]
    xp_barra  = barra_progresso(xp_atual % max(xp_prox, 1), xp_prox, 14)

    # Social
    faccao_str  = user.get("faccao") or "—"
    familia_str = "—"
    empresa_str = "—"
    casa_str    = "—"

    fid = user.get("familia_id")
    if fid:
        fs = get_familias().get(fid, {})
        cargo_f = user.get("cargo_familia", "Membro")
        familia_str = f"{fs.get('nome','?')} • {cargo_f}"

    eid = user.get("empresa_id")
    if eid:
        es = get_empresas().get(eid, {})
        cargo_e = user.get("cargo_empresa", "Funcionário")
        empresa_str = f"{es.get('nome','?')} • {cargo_e}"

    cid = user.get("casa_id")
    if cid:
        cs = get_casas().get(cid, {})
        casa_str = f"{cs.get('emoji','🏠')} {cs.get('nome','?')}"

    ficha     = user.get("ficha", {})
    nome_rp   = ficha.get("nome") or user.get("nome") or member.display_name
    historia  = ficha.get("historia") or user.get("historia") or "*Sem história registrada...*"
    habs      = ficha.get("habilidades") or user.get("habilidades") or []

    if eh_imp:
        embed = discord.Embed(
            title="⚜️ 👑 IMPERADOR SUPREMO DE TENSHI 👑 ⚜️",
            description=f"*O universo inteiro reconhece esta presença divina...*\n{SEP}",
            color=0xFFD700
        )
    else:
        embed = discord.Embed(
            title=f"{emoji_p} PERGAMINHO IMPERIAL",
            description=f"*Os registros de Tenshi revelam a alma de **{nome_rp}**...*\n{SEP}",
            color=cor
        )

    embed.add_field(name="👤 Nome RP",    value=f"**{nome_rp}**",         inline=True)
    embed.add_field(name="🏷️ Título",    value=f"*{titulo}*",             inline=True)
    embed.add_field(name=f"{emoji_p} Pegada", value=nome_p,               inline=True)
    embed.add_field(name="📊 Nível",     value=f"**{nivel}**",            inline=True)
    embed.add_field(name="💥 Poder",     value=f"**{user['poder']}**",    inline=True)
    embed.add_field(name="⚔️ Facção",    value=faccao_str,                inline=True)

    embed.add_field(
        name="✨ Progressão",
        value=f"`{xp_barra}` **{xp_atual} XP** → próx. nível em **{xp_prox} XP**",
        inline=False
    )

    if historia and historia != "*Sem história registrada...*":
        hist_curta = historia[:220] + ("..." if len(historia) > 220 else "")
        embed.add_field(name="📖 História", value=f"*{hist_curta}*", inline=False)

    if habs:
        embed.add_field(name="⚡ Habilidades", value=" `|` ".join(habs[:6]), inline=False)

    embed.add_field(name="🏠 Moradia",         value=casa_str,    inline=True)
    embed.add_field(name="👨‍👩‍👧 Organização",  value=familia_str, inline=True)
    embed.add_field(name="🏢 Empresa",         value=empresa_str, inline=True)

    pvp = f"⚔️ {user.get('vitorias_duelo',0)}V / 💀 {user.get('derrotas_duelo',0)}D"
    embed.add_field(name="🏟️ PvP", value=pvp, inline=True)

    embed.set_thumbnail(url=member.display_avatar.url)
    if eh_imp:
        embed.set_footer(text="⚜️ Alloy Tenshi — O Imperador Eterno  •  " + RODAPE_IMPERIAL)
    else:
        embed.set_footer(text=f"{emoji_p} {nome_p}  •  {RODAPE_IMPERIAL}")
    return embed


def _build_inventario_embed(member: discord.Member | discord.User) -> discord.Embed:
    user = get_user(member.id)
    pegada = user.get("pegada", "imperial")
    cor = CORES_DESTAQUE.get(pegada, 0x8A2BE2)
    inv = user.get("inventario", [])
    embed = discord.Embed(
        title="🎒 INVENTÁRIO IMPERIAL",
        description=f"*Artefatos e relíquias de {member.display_name}*\n{SEP}",
        color=cor
    )
    if not inv:
        embed.add_field(name="📭 Vazio", value="*Seu inventário está vazio.*\nUse `Tenshi, mercado` para adquirir itens.", inline=False)
    else:
        for i, item in enumerate(inv, 1):
            embed.add_field(name=f"📦 {i}. {item}", value="\u200b", inline=True)
    embed.add_field(name="\u200b", value=f"*{len(inv)} item(ns) no total*", inline=False)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


def _build_conquistas_embed(member: discord.Member | discord.User) -> discord.Embed:
    user = get_user(member.id)
    pegada = user.get("pegada", "imperial")
    cor = CORES_DESTAQUE.get(pegada, 0x8A2BE2)
    nivel = user.get("nivel", 1)
    poder = user.get("poder", 0)
    vitorias = user.get("vitorias_duelo", 0)
    missoes = user.get("missoes_completas", 0)
    moedas_total = user.get("moedas", 0) + user.get("conta_banco", 0)

    conquistas = []
    if nivel >= 5:   conquistas.append(("🥉 Veterano Imperial", f"Nível {nivel} atingido"))
    if nivel >= 10:  conquistas.append(("🥈 Guardião de Tenshi", "Nível 10 atingido"))
    if nivel >= 20:  conquistas.append(("🥇 Lorde do Império", "Nível 20 atingido"))
    if poder >= 200: conquistas.append(("💥 Força Colossal", "200+ Poder de luta"))
    if poder >= 500: conquistas.append(("⚡ Transcendido", "500+ Poder de luta"))
    if vitorias >= 1:  conquistas.append(("⚔️ Primeiro Sangue", "Primeira vitória em duelo"))
    if vitorias >= 10: conquistas.append(("🏆 Arena Imperial", "10 vitórias em duelo"))
    if missoes >= 5:   conquistas.append(("📜 Agente Leal", "5 missões completadas"))
    if moedas_total >= 1000: conquistas.append(("💰 Magnata", "1000+ moedas acumuladas"))
    if user.get("casa_id"): conquistas.append(("🏠 Proprietário", "Possui uma propriedade"))
    if user.get("familia_id"): conquistas.append(("👨‍👩‍👧 Laços de Sangue", "Membro de uma organização"))
    if user.get("empresa_id"): conquistas.append(("🏢 Homem de Negócios", "Ligado a uma empresa"))

    embed = discord.Embed(
        title="🏆 CONQUISTAS IMPERIAIS",
        description=f"*Títulos de prestígio de {member.display_name}*\n{SEP}",
        color=cor
    )
    if not conquistas:
        embed.add_field(name="🔒 Nenhuma ainda", value="*Continue sua jornada — conquistas aguardam.*", inline=False)
    else:
        for titulo, desc in conquistas:
            embed.add_field(name=titulo, value=f"*{desc}*", inline=True)
    embed.add_field(name="\u200b", value=f"*{len(conquistas)} conquista(s) desbloqueada(s)*", inline=False)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


def _build_financeiro_embed(member: discord.Member | discord.User) -> discord.Embed:
    user = get_user(member.id)
    pegada = user.get("pegada", "imperial")
    cor = CORES_DESTAQUE.get(pegada, 0x8A2BE2)
    moedas = user.get("moedas", 0)
    banco  = user.get("conta_banco", 0)
    divida = sum(e["valor_restante"] for e in user.get("emprestimos", []))
    patrimonio = moedas + banco - divida
    salario = user.get("salario", 0)

    embed = discord.Embed(
        title="💰 CÂMARA DO TESOURO",
        description=f"*Finanças imperiais de {member.display_name}*\n{SEP}",
        color=cor
    )
    embed.add_field(name="🪙 Em Mãos",         value=f"**{moedas}** moedas",     inline=True)
    embed.add_field(name="🏦 No Banco",         value=f"**{banco}** moedas",      inline=True)
    embed.add_field(name="💸 Dívidas",          value=f"**{divida}** moedas",     inline=True)
    embed.add_field(name="💎 Patrimônio Líq.",  value=f"**{patrimonio}** moedas", inline=True)
    embed.add_field(name="💼 Salário",          value=f"**{salario}**/pagto",     inline=True)
    embed.add_field(
        name="📋 Comandos rápidos",
        value="`banco` `depositar` `sacar` `transferir @user [v]` `emprestimo [v]`",
        inline=False
    )
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


# ─────────────────────────────────────────────────────────────────────────────
# Cog
# ─────────────────────────────────────────────────────────────────────────────
class PerfilConfig:
    def __init__(self, bot):
        self.bot = bot

    async def handle_status(self, message):
        user_db = get_user(message.author.id)
        nivel, _ = calcular_nivel(user_db["xp"])
        user_db["nivel"] = nivel
        save_user(message.author.id, user_db)

        # Apaga a mensagem de status anterior deste usuário neste canal, se existir
        prev = _status_msgs.get(message.author.id)
        if prev is not None:
            try:
                await prev.delete()
            except Exception:
                pass

        embed = await _build_perfil_embed(self.bot, message.author)
        view  = StatusView(self.bot, message.author.id, message.author, "perfil")
        sent  = await message.channel.send(embed=embed, view=view)
        _status_msgs[message.author.id] = sent

    async def handle_inventario(self, message):
        embed = _build_inventario_embed(message.author)
        view  = StatusView(self.bot, message.author.id, message.author, "inventario")
        await message.channel.send(embed=embed, view=view)

    async def handle_conquistas(self, message):
        embed = _build_conquistas_embed(message.author)
        view  = StatusView(self.bot, message.author.id, message.author, "conquistas")
        await message.channel.send(embed=embed, view=view)

    async def handle_pegada(self, message, args):
        if not args:
            embed = discord.Embed(
                title="🎭 ESCOLHA SUA PEGADA",
                description=f"*A pegada define a essência do seu personagem em Tenshi...*\n{SEP}",
                color=0x2B0A3D
            )
            for p in PEGADAS_VALIDAS:
                embed.add_field(
                    name=f"{EMOJI_PEGADA[p]} {NOME_PEGADA[p]}",
                    value=f"`Tenshi, pegada {p}`",
                    inline=True
                )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return
        nova = args[0].lower()
        if nova not in PEGADAS_VALIDAS:
            await message.channel.send(embed=embed_imperial("❌", f"Pegadas disponíveis: {' • '.join(PEGADAS_VALIDAS)}", 0x6B0000))
            return
        user = get_user(message.author.id)
        user["pegada"] = nova
        save_user(message.author.id, user)
        cor   = CORES_PEGADA[nova]
        emoji = EMOJI_PEGADA[nova]
        nome  = NOME_PEGADA[nova]
        embed = discord.Embed(
            title=f"{emoji} PEGADA ATIVADA — {nome.upper()}",
            description=(
                f"*{message.author.display_name} assume uma nova identidade...*\n{SEP}\n\n"
                f"Seu perfil agora reflete a essência de **{nome}**.\n"
                f"*Use `Tenshi, status` para ver as mudanças.*"
            ),
            color=cor
        )
        embed.set_footer(text=f"{emoji} {nome}  •  {RODAPE_IMPERIAL}")
        await message.channel.send(embed=embed)

    async def handle_ficha(self, message, args):
        ficha_texto = message.content[message.content.lower().index("ficha"):].replace("ficha", "", 1).strip()
        # Parse automático
        if not ficha_texto and not args:
            embed = discord.Embed(
                title="📋 FICHA DE PERSONAGEM",
                description=(
                    f"*Configure sua identidade no Império de Tenshi...*\n{SEP}\n\n"
                    "**Formato multilinha:**\n"
                    "```\nTenshi, ficha\n"
                    "Nome: Seu Nome RP\n"
                    "Historia: Sua história aqui...\n"
                    "Habilidades: Combate, Furtividade, Magia\n"
                    "Titulo: Seu Título Personalizado\n"
                    "Pegada: imperial\n```\n"
                    "**Formato inline:**\n"
                    "`Tenshi, ficha Nome: João | Historia: Guerreiro das sombras | Habilidades: Combate, Furtividade`"
                ),
                color=0x2B0A3D
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return

        linhas = message.content.split("\n")
        campos_map = {
            "nome": "nome", "name": "nome",
            "historia": "historia", "história": "historia", "story": "historia",
            "habilidades": "habilidades", "habilidade": "habilidades",
            "titulo": "titulo", "título": "titulo", "title": "titulo",
            "pegada": "pegada", "vibe": "pegada", "estilo": "pegada",
        }
        ficha_data = {}

        for linha in linhas:
            if ":" in linha:
                chave_r, _, valor = linha.partition(":")
                chave = chave_r.strip().lower()
                valor = valor.strip()
                campo = campos_map.get(chave)
                if campo and valor:
                    ficha_data[campo] = valor

        if not ficha_data:
            texto_inline = " ".join(args) if args else ficha_texto
            for sep in ["|", ",", ";"]:
                if sep in texto_inline:
                    for parte in texto_inline.split(sep):
                        if ":" in parte:
                            c, _, v = parte.partition(":")
                            cam = campos_map.get(c.strip().lower())
                            if cam:
                                ficha_data[cam] = v.strip()
                    break
            if not ficha_data and (args or ficha_texto):
                ficha_data["nome"] = (ficha_texto or " ".join(args))[:50]

        user = get_user(message.author.id)
        ficha_atual = user.get("ficha", {})

        mudancas = []
        if "nome" in ficha_data:
            ficha_atual["nome"] = ficha_data["nome"]
            user["nome"] = ficha_data["nome"]
            mudancas.append(f"👤 **Nome:** {ficha_data['nome']}")
        if "historia" in ficha_data:
            ficha_atual["historia"] = ficha_data["historia"]
            user["historia"] = ficha_data["historia"]
            mudancas.append(f"📖 **História** registrada")
        if "habilidades" in ficha_data:
            habs = [h.strip() for h in ficha_data["habilidades"].replace(",", "|").split("|") if h.strip()]
            ficha_atual["habilidades"] = habs
            user["habilidades"] = habs
            mudancas.append(f"⚡ **Habilidades:** {' • '.join(habs)}")
        if "titulo" in ficha_data:
            ficha_atual["titulo"] = ficha_data["titulo"]
            user["titulo"] = ficha_data["titulo"]
            mudancas.append(f"🏷️ **Título:** {ficha_data['titulo']}")
        if "pegada" in ficha_data and ficha_data["pegada"].lower() in PEGADAS_VALIDAS:
            peg = ficha_data["pegada"].lower()
            user["pegada"] = peg
            ficha_atual["pegada"] = peg
            mudancas.append(f"🎭 **Pegada:** {NOME_PEGADA[peg]}")

        user["ficha"] = ficha_atual
        save_user(message.author.id, user)

        pegada = user.get("pegada", "imperial")
        cor    = CORES_PEGADA.get(pegada, 0x2B0A3D)
        emoji  = EMOJI_PEGADA.get(pegada, "🏛️")

        embed = discord.Embed(
            title=f"{emoji} FICHA REGISTRADA NOS PERGAMINHOS",
            description=(
                f"*Os Escribas de Tenshi anotaram cada detalhe...*\n{SEP}\n\n"
                + "\n".join(mudancas) +
                f"\n\n{SEP}\n*Use `Tenshi, status` para ver seu perfil completo.*"
            ),
            color=cor
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)
