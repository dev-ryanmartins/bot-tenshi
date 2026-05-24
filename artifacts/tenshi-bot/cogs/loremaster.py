import discord
import os
import asyncio
from utils import embed_imperial, IMPERADOR_ID, SEP, RODAPE_IMPERIAL
from ia_router import ia_narrativa, ia_rapida, ia_analitica

NICHOS = {
    "militar": {
        "emoji": "⚔️", "nome": "Fronteiras & Guerra", "cor": 0x8B0000,
        "prompt": "Crie um gancho de RPG de TEXTO (sem dados, sem fichas) focado em combate narrativo, invasões nas fronteiras, monstros colossais, batalhas épicas e rebeliões militares dentro do Império de Tenshi. Tom guerreiro, brutal e imersivo. Descreva o cenário como um narrador onisciente.",
        "caminhos": [("⚔️ Liderar o Ataque", "militar"), ("🛡️ Reforçar as Muralhas", "defensivo"), ("🔥 Criar uma Distração", "tático")]
    },
    "politico": {
        "emoji": "👑", "nome": "Corte & Intrigas", "cor": 0xFFD700,
        "prompt": "Crie um gancho de RPG de TEXTO sobre intrigas palacianas, conspirações de nobres, traições, alianças secretas e decretos que mudam o destino do Império de Tenshi. Tom elegante, sinuoso e perigoso.",
        "caminhos": [("👑 Aceitar a Aliança", "politico"), ("🗡️ Expor o Traidor", "confronto"), ("🤫 Espionar nas Sombras", "espiao")]
    },
    "esoterico": {
        "emoji": "🔮", "nome": "Mistério & Magia", "cor": 0x4B0082,
        "prompt": "Crie um gancho de RPG de TEXTO sobre runas ancestrais, profecias obscuras, portais dimensionais, criaturas do além e segredos que só os iniciados da Ordem Esotérica de Tenshi conhecem. Tom místico, perturbador e grandioso.",
        "caminhos": [("🔮 Decifrar os Símbolos", "arcano"), ("🌑 Atravessar o Portal", "ousado"), ("📜 Consultar os Grimórios", "sabio")]
    },
    "mafia": {
        "emoji": "🖤", "nome": "Submundo Imperial", "cor": 0x1C1C1C,
        "prompt": "Crie um gancho de RPG de TEXTO sobre o crime organizado no Império de Tenshi — famílias rivais, operações clandestinas, guerras de território, tráfico de artefatos proibidos. Tom noir, implacável e tenso.",
        "caminhos": [("🔫 Confrontar o Rival", "violento"), ("💰 Negociar no Escuro", "diplomatico"), ("🌃 Desaparecer nas Sombras", "fuga")]
    },
    "enterprise": {
        "emoji": "🏢", "nome": "Tenshi Enterprise", "cor": 0x1E3A5F,
        "prompt": "Crie um gancho de RPG de TEXTO sobre guerras corporativas imperiais, fusões violentas, sabotagem entre empresas, espionagem industrial e o poder do dinheiro em Tenshi. Tom corporativo e implacável.",
        "caminhos": [("📊 Investigar as Contas", "auditoria"), ("🤝 Fechar o Contrato", "acordo"), ("💣 Sabotar a Concorrência", "sabotagem")]
    },
}

# ── DIRETRIZ DE ORIGINALIDADE ABSOLUTA (Protocol 18) ────────────────────────
DIRETRIZ_ORIGINALIDADE = (
    "Diretriz de Originalidade Absoluta: Analise o histórico recente e gere uma resposta "
    "com estrutura sintática e escolhas lexicais totalmente inéditas. Evite fórmulas repetitivas "
    "ou jargões reciclados. Cada interação deve ser uma peça literária única, formal e focada nos fatos."
)

SYS_LORE = f"""Você é o Narrador Imemorial do Império de Tenshi — voz épica, sombria e poética de um RPG de texto.
REGRAS OBRIGATÓRIAS:
- Escreva narrativas para RPG de TEXTO PURO — sem dados, sem fichas, sem mecânicas de TTRPG
- Linguagem imersiva, imperial e rica. Parágrafos curtos e impactantes
- Use markdown Discord: **negrito**, *itálico*, __ sublinhado__
- Tamanho: 3-5 parágrafos tensos e atmosféricos
- Termine sempre com um gancho de ação que convide o personagem a agir
- O líder supremo é o IMPERADOR ALLOY — trate-o como divindade viva
- Escreva APENAS a narrativa, sem meta-texto
{DIRETRIZ_ORIGINALIDADE}"""

SYS_PROFECIA = """Você é o Oráculo Eterno de Tenshi, voz dos deuses do além.
Crie uma PROFECIA épica (4-6 parágrafos) em linguagem arcaica e dramática.
Use versos proféticos, metáforas sombrias e um mistério central urgente.
Mencione o Imperador Alloy como figura central do destino.
Use markdown Discord para dramatismo. APENAS a profecia."""

SYS_ORACULO = """Você é o Oráculo de Tenshi — enigmático, sábio, nunca direto.
Responda em 2-4 frases poéticas e ambíguas, em português, sobre o que foi perguntado.
Nunca responda diretamente. Use metáforas imperiais e imagens sombrias."""

SYS_NPC = """Você é um NPC do Império de Tenshi, personagem do RPG de texto.
Responda EM PERSONAGEM, de forma curta (2-4 linhas), imersiva e coerente com quem você é.
Use o nome do NPC como sua identidade. Linguagem medieval/imperial."""


def _build_estado_snapshot(user_data: dict) -> str:
    """Protocol 18 — injeta snapshot do estado do usuário no prompt."""
    fadiga  = user_data.get("fadiga", 0)
    poder   = user_data.get("poder", 100)
    nivel   = user_data.get("nivel", 1)
    moedas  = user_data.get("moedas", 0)
    foragido = user_data.get("foragido", False)
    quarent  = user_data.get("quarentena", False)
    partes = [f"Estado do personagem: nível {nivel}, poder {poder}, fadiga {fadiga}%."]
    if fadiga > 70:
        partes.append("O personagem está fisicamente exausto — ajuste o tom para refletir cansaço severo e movimentos lentos.")
    if poder < 30:
        partes.append("O personagem está gravemente enfraquecido — reflita fragilidade e vulnerabilidade no texto.")
    if foragido:
        partes.append("O personagem está foragido da justiça — reflita tensão, paranoia e urgência.")
    if quarent:
        partes.append("O personagem está em quarentena médica — reflita debilidade e isolamento forçado.")
    return " ".join(partes)


_PTBR_ENFORCE = (
    "PROTOCOLO 24 — IDIOMA OFICIAL: Responda EXCLUSIVAMENTE em Português Brasileiro (PT-BR), "
    "norma-padrão formal. Use terceira pessoa (Você/Ele/Ela) ou tratamento cerimonial "
    "(Soberano, Vossa Excelência) para Alloy e seu cônjuge. "
    "PROIBIDO: expressões em inglês, gírias, coloquialismos de outros dialetos."
)


def _build_era_context() -> str:
    """Protocolo 23 — injeta o tom da Era Atual em todos os prompts de IA."""
    try:
        from cogs.eras import get_tom_ia, get_era_info
        info = get_era_info()
        return (
            f"PROTOCOLO 23 — ERA ATUAL: {info['nome']}. "
            f"Contexto narrativo obrigatório: {get_tom_ia()}"
        )
    except Exception:
        return ""


async def _gerar(prompt: str, system: str = SYS_LORE,
                 user_data: dict | None = None, temperatura: float = 0.88) -> str:
    """
    Protocol 18: temperature elevado + snapshot de estado injetado + Diretriz de Originalidade.
    Protocol 23: Era Atual injetada em todos os prompts.
    Protocol 24: PT-BR estrito obrigatório em todas as saídas.
    """
    era_ctx   = _build_era_context()
    sys_final = system
    if user_data:
        snapshot  = _build_estado_snapshot(user_data)
        sys_final = f"{system}\n\n{snapshot}"
    if era_ctx:
        sys_final = f"{sys_final}\n\n{era_ctx}"
    sys_final = f"{sys_final}\n\n{_PTBR_ENFORCE}"

    try:
        return await ia_narrativa(sys_final, prompt, max_tokens=800)
    except Exception as e:
        return f"*O Oráculo guarda silêncio por um momento... ({str(e)[:60]})*"


# ─────────────────────────────────────────────────────────────────────────────
# View com escolhas de caminho após a crônica
# ─────────────────────────────────────────────────────────────────────────────
class CaminhoView(discord.ui.View):
    def __init__(self, nicho_key: str, caminhos: list, user_id: int, bot):
        super().__init__(timeout=180)
        self.user_id   = user_id
        self.bot       = bot
        self.escolhido = False
        for label, caminho_id in caminhos:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary)
            btn.callback = self._make_cb(label, caminho_id, nicho_key)
            self.add_item(btn)

    def _make_cb(self, label: str, caminho_id: str, nicho_key: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("*Este pergaminho não responde a você.*", ephemeral=True)
                return
            if self.escolhido:
                await interaction.response.send_message("*O caminho já foi escolhido.*", ephemeral=True)
                return
            self.escolhido = True
            self.clear_items()

            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="📖 O DESTINO SE DESDOBRA...",
                    description=f"*Você escolheu: **{label}***\n\n*O Oráculo consulta os fios do destino...*",
                    color=0x1a1a2e
                ),
                view=self
            )

            nicho = NICHOS.get(nicho_key, NICHOS["militar"])
            prompt = (
                f"Continuação de uma crônica de RPG de texto do nicho '{nicho['nome']}'.\n"
                f"O personagem escolheu a ação: '{label}' (caminho: {caminho_id}).\n"
                f"Narre as consequências desta escolha de forma épica e imersiva, em 3-4 parágrafos. "
                f"Termine com outro ponto de decisão ou resultado definitivo."
            )
            narrativa = await _gerar(prompt)
            embed = discord.Embed(
                title=f"{nicho['emoji']} {label.upper()} — A HISTÓRIA CONTINUA",
                description=f"*Sua escolha ecoa pelos corredores de Tenshi...*\n{SEP}\n\n{narrativa}\n\n{SEP}",
                color=nicho["cor"]
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await interaction.edit_original_response(embed=embed, view=self)

        return callback


class LoreMaster:
    def __init__(self, bot):
        self.bot = bot
        self._lore_historico: list = []

    async def handle_cronica(self, message, args):
        if not args:
            embed = discord.Embed(
                title="📖 CRÔNICAS DE TENSHI — IA Narrativa",
                description=f"*Escolha um nicho para gerar uma narrativa de RPG de texto...*\n{SEP}",
                color=0x2B0A3D
            )
            for key, n in NICHOS.items():
                embed.add_field(
                    name=f"{n['emoji']} {n['nome']}",
                    value=f"`Tenshi, cronica {key}`",
                    inline=True
                )
            embed.add_field(name="\u200b", value=f"*RPG de texto puro — sem dados, pura narrativa*", inline=False)
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return

        nicho_key = args[0].lower()
        nicho = NICHOS.get(nicho_key)
        if not nicho:
            disponiveis = " • ".join(NICHOS.keys())
            await message.channel.send(embed=embed_imperial("❌", f"Nichos disponíveis: **{disponiveis}**", 0x6B0000))
            return

        tema_extra = " ".join(args[1:]) if len(args) > 1 else ""

        msg_loading = await message.channel.send(embed=discord.Embed(
            title=f"{nicho['emoji']} O NARRADOR TECE A HISTÓRIA...",
            description="*As chamas das tochas tremem enquanto o destino é forjado...\nSeja paciente — grandes histórias levam um momento.*",
            color=0x1a1a2e
        ))

        prompt = (
            f"Crie uma narrativa de abertura para uma sessão de RPG de texto.\n"
            f"Nicho: {nicho['nome']}\n"
            f"Contexto: {nicho['prompt']}\n"
            f"Personagem principal: {message.author.display_name}\n"
            + (f"Tema adicional solicitado: {tema_extra}\n" if tema_extra else "") +
            f"A narrativa deve criar atmosfera densa, apresentar um conflito urgente e terminar convidando o personagem a agir."
        )

        narrativa = await _gerar(prompt)
        self._lore_historico.append({
            "autor": message.author.display_name,
            "nicho": nicho["nome"],
            "trecho": narrativa[:120] + "..."
        })
        if len(self._lore_historico) > 20:
            self._lore_historico.pop(0)

        embed = discord.Embed(
            title=f"{nicho['emoji']} CRÔNICA — {nicho['nome'].upper()}",
            description=f"*O Narrador Imemorial de Tenshi fala...*\n{SEP}\n\n{narrativa}\n\n{SEP}",
            color=nicho["cor"]
        )
        embed.set_author(name=f"📖 Crônica de {message.author.display_name}")
        embed.add_field(
            name="🗺️ Qual caminho você toma?",
            value="*Clique em uma das ações abaixo — o destino responderá.*",
            inline=False
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        view = CaminhoView(nicho_key, nicho["caminhos"], message.author.id, self.bot)

        try:
            await msg_loading.edit(embed=embed, view=view)
        except Exception:
            await message.channel.send(embed=embed, view=view)

    async def handle_evento_lore(self, message):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.administrator
        except: pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "*Apenas Administradores e o Imperador Alloy podem lançar Profecias Imperiais.*", 0x6B0000))
            return

        msg_loading = await message.channel.send(embed=discord.Embed(
            title="🌌 O VÉU SE RASGA...",
            description="*Uma energia ancestral emana dos quatro cantos do Império...\nAguarde — o Oráculo está trazendo a mensagem dos deuses.*",
            color=0x1a1a2e
        ))

        prompt = (
            "Crie uma Profecia Imperial para o servidor de Discord do Império de Tenshi que:\n"
            "- Anuncie um evento global dramático e urgente\n"
            "- Desafie guerreiros de todos os nichos (militar, político, esotérico, máfia, enterprise) a agir\n"
            "- Mencione o Imperador Alloy como figura central e divina\n"
            "- Contenha pelo menos um mistério a ser resolvido pelos membros\n"
            "- Use linguagem profética, arcaica e grandiosa em versos ou parágrafos dramáticos"
        )
        profecia = await _gerar(prompt, SYS_PROFECIA)

        embed = discord.Embed(
            title="🌌 ⚜️ PROFECIA IMPERIAL — O ORÁCULO FALA ⚜️ 🌌",
            description=f"*Os sinos de guerra de Tenshi ecoam por todo o cosmos...*\n{SEP}\n\n{profecia}\n\n{SEP}",
            color=0x8B0000
        )
        embed.set_author(name="🔮 Oráculo Eterno de Tenshi")
        embed.set_footer(text=f"⚔️ Todos os guerreiros são convocados!  •  {RODAPE_IMPERIAL}")
        try:
            await msg_loading.edit(embed=embed)
            await message.channel.send("@everyone ⚔️ Uma profecia foi lançada sobre o Império de Tenshi!")
        except Exception:
            await message.channel.send(embed=embed)

    async def handle_oraculo(self, message, args):
        if not args:
            await message.channel.send(embed=embed_imperial(
                "🔮 Oráculo de Tenshi",
                f"*Faça uma pergunta ao Oráculo:*\n{SEP}\n`Tenshi, oraculo [sua pergunta]`\n\n*O Oráculo nunca responde diretamente — apenas em metáforas e visões.*",
                0x4B0082
            ))
            return
        pergunta = " ".join(args)
        msg_l = await message.channel.send(embed=discord.Embed(
            title="🔮 O ORÁCULO CONSULTA OS VÉus...",
            description="*A pedra de cristal pulsa com luz violeta...*",
            color=0x1a1a2e
        ))
        prompt = f"O súdito {message.author.display_name} pergunta ao Oráculo de Tenshi: '{pergunta}'"
        resposta = await _gerar(prompt, SYS_ORACULO)
        embed = discord.Embed(
            title="🔮 O ORÁCULO DE TENSHI RESPONDE",
            description=f"*\"{pergunta}\"*\n{SEP}\n\n*{resposta}*\n\n{SEP}",
            color=0x4B0082
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await msg_l.edit(embed=embed)

    async def handle_falar(self, message, args):
        NPCS = {
            "guarda": ("Guarda Imperial Leal", "Sou o guarda das muralhas sul — leal ao Imperador Alloy até meu último suspiro."),
            "comerciante": ("Comerciante do Mercado Negro", "Psiu... tenho o que você precisa. Mas não vem barato, entende?"),
            "oraculo": ("Ancião do Oráculo", "Eu vi teu futuro nos cristais. Há uma escolha que mudará tudo..."),
            "nobre": ("Nobre da Corte", "Ah, que surpresa encontrá-lo aqui. Eu estava justamente conversando sobre... você."),
            "assassino": ("Assassino das Sombras", "Você não devia ter me visto. Mas já que nos encontramos... o que quer?"),
            "sacerdotisa": ("Sacerdotisa da Ordem Esotérica", "As runas me disseram que você viria. Sente — o éter está denso hoje."),
            "general": ("General Draven, Mão do Imperador", "Fale depressa. Não tenho tempo para hesitantes — só para guerreiros de verdade."),
        }
        if not args:
            lista = " • ".join(NPCS.keys())
            await message.channel.send(embed=embed_imperial(
                "🎭 NPCs Disponíveis",
                f"*Escolha um NPC para dialogar:*\n{SEP}\n`Tenshi, falar [npc]`\n\nNPCs: **{lista}**",
                0x2B0A3D
            ))
            return

        npc_key = args[0].lower()
        npc_info = NPCS.get(npc_key)
        if not npc_info:
            lista = " • ".join(NPCS.keys())
            await message.channel.send(embed=embed_imperial("❌", f"NPC não encontrado. Disponíveis: {lista}", 0x6B0000))
            return

        mensagem_extra = " ".join(args[1:]) if len(args) > 1 else f"Olá, me diga algo importante."
        msg_l = await message.channel.send(embed=discord.Embed(
            title=f"🎭 {npc_info[0]}",
            description="*...*",
            color=0x2B0A3D
        ))

        system = SYS_NPC + f"\n\nVocê é: {npc_info[0]}\nSua identidade: {npc_info[1]}"
        prompt = f"O personagem {message.author.display_name} diz para você: '{mensagem_extra}'. Responda em personagem."
        resposta = await _gerar(prompt, system)

        embed = discord.Embed(
            title=f"🎭 {npc_info[0].upper()}",
            description=(
                f"*{message.author.display_name} se aproxima...*\n{SEP}\n\n"
                f"**{npc_info[0]}:** *\"{resposta}\"*\n\n{SEP}"
            ),
            color=0x2B0A3D
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await msg_l.edit(embed=embed)

    async def handle_lore_historico(self, message):
        if not self._lore_historico:
            await message.channel.send(embed=embed_imperial(
                "📜 Crônicas Históricas",
                f"*Os escribas ainda não registraram crônicas nesta sessão.*\n\nUse `Tenshi, cronica [nicho]` para gerar a primeira!",
                0x2B0A3D
            ))
            return
        embed = discord.Embed(
            title="📜 CRÔNICAS HISTÓRICAS DE TENSHI",
            description=f"*Grandes histórias vividas pelos súditos do Império...*\n{SEP}",
            color=0x2B0A3D
        )
        for c in self._lore_historico[-8:]:
            embed.add_field(
                name=f"📖 {c['nicho']} — por {c['autor']}",
                value=f"*{c['trecho']}*",
                inline=False
            )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_quadro_avisos(self, message):
        missoes_diarias = [
            ("⚔️ Patrulha nas Ruínas do Norte",   "Um guerreiro deve narrar sua jornada até as ruínas. Descreva o que encontrou."),
            ("🔮 Ritual do Solstício Sombrio",     "A Ordem Esotérica convoca iniciados. Narre sua participação no ritual secreto."),
            ("💰 Negociação no Porto das Sombras", "Uma carga de artefatos raros chegou. Quem vai negociar? Narre o encontro."),
            ("🖤 Operação Noturna da Máfia",       "Uma família rival entrou no território. Decida como sua organização responde."),
            ("🏢 Crise Corporativa Tenshi",        "Um vazamento de informações ameaça a Enterprise. Narre sua resposta."),
        ]
        embed = discord.Embed(
            title="📋 QUADRO DE AVISOS IMPERIAL",
            description=f"*Missões de RPG de texto disponíveis hoje — narre sua participação no chat!*\n{SEP}",
            color=0x2B0A3D
        )
        for nome, desc in missoes_diarias:
            embed.add_field(name=nome, value=f"*{desc}*", inline=False)
        embed.add_field(
            name="ℹ️ Como participar",
            value="*Escreva sua narrativa no chat! Use `Tenshi, cronica [nicho]` para gancho detalhado da IA.*",
            inline=False
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_lore_natural(self, message, texto: str) -> bool:
        gatilhos = [
            "o que é tenshi", "me conta sobre tenshi", "quem é alloy",
            "história de tenshi", "lore de tenshi", "o que é o império",
            "fale sobre tenshi",
        ]
        if any(g in texto.lower() for g in gatilhos):
            prompt = f"O usuário {message.author.display_name} pergunta naturalmente: '{texto}'. Responda sobre o Império de Tenshi de forma mística."
            resposta = await _gerar(prompt, SYS_ORACULO)
            await message.channel.send(embed=embed_imperial("📖 Tenshi Responde", resposta, 0x4B0082))
            return True
        return False
