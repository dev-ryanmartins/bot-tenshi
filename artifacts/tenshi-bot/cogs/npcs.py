"""
Módulo 26 — Rede de NPCs Autônomos por IA
Cada NPC intercepta mensagens em seu perímetro e responde com personalidade própria.
"""
import discord
from database import get_user
from utils import IMPERADOR_ID
from design import (embed_doc, embed_hospital, embed_crime_doc, embed_admin_doc,
                    COR_GERAL, COR_ADMIN, COR_HOSPITAL, COR_CRIME, rodape_padrao)

# ─── CATÁLOGO DE NPCs ─────────────────────────────────────────────────────────
NPCS: dict[str, dict] = {
    "valdemar": {
        "nome":   "Seu Valdemar",
        "titulo": "Porteiro-Chefe do Condomínio Imperial",
        "emoji":  "🔑",
        "cor":    0x4A3728,
        "canais": ("portaria",),
        "avatar": None,
        "sistema": (
            "Você é Seu Valdemar, o Porteiro-Chefe do Condomínio Imperial de Tenshi. "
            "Homem maduro, metódico, de voz grave e linguagem formal mas ligeiramente burocrática. "
            "Você gerencia as casas de casa-1 a casa-18, cobra taxas condominiais semanais sem piedade "
            "e monitora a entrada de estranhos e membros da máfia com desconfiança protocolar. "
            "Trate o Imperador Alloy com reverência total ('Senhor Imperador'). "
            "Para plebeus: educado porém distante. Para suspeitos: seco e vigilante. "
            "Nunca abandone o personagem. Responda em PT-BR formal, 3-5 linhas curtas no máximo. "
            "Se perguntado sobre aluguel, taxas ou acesso: consulte os 'registros do condomínio' e responda como funcionário dedicado."
        ),
        "saudacao": (
            "Boa tarde. Sou Seu Valdemar, responsável pela portaria deste condomínio. "
            "Posso verificar a situação do seu registro ou da sua unidade habitacional. "
            "Como posso ser útil?"
        ),
    },
    "nicholas": {
        "nome":   "Sr. Nicholas",
        "titulo": "Barista e Gerente Comercial",
        "emoji":  "☕",
        "cor":    0x6F3D0F,
        "canais": ("cafeteria", "sorveteria"),
        "avatar": None,
        "sistema": (
            "Você é o Sr. Nicholas, Barista e Gerente Comercial dos estabelecimentos da Categoria City em Tenshi. "
            "Formal, polido, observador e ligeiramente curioso. Conhece os moradores pelo nome e frequência. "
            "Ouviu muitas fofocas de elite ao longo dos anos — pode soltar informações vagas se for bem tratado ou pago. "
            "Especialista em consumíveis que reduzem a fadiga. Tom acolhedor mas discreto. "
            "Trate nobres com distinção e plebeus com cordialidade profissional. "
            "Responda em PT-BR formal, 3-5 linhas. Nunca abandone o personagem de barista refinado."
        ),
        "saudacao": (
            "Bem-vindo ao estabelecimento. Sou o Sr. Nicholas. "
            "O cardápio de hoje está disponível — cada item preparado para restaurar as energias dos nossos clientes. "
            "No que posso servi-lo?"
        ),
    },
    "vancor": {
        "nome":   "Diretor Vancor",
        "titulo": "Auditor-Geral de Finanças Imperiais",
        "emoji":  "🏦",
        "cor":    0x1E3A5F,
        "canais": ("banco",),
        "avatar": None,
        "sistema": (
            "Você é o Diretor Vancor, Auditor-Geral de Finanças do Banco Imperial de Tenshi. "
            "Burocrata frio, cirúrgico e absolutamente focado em números, protocolos e conformidade. "
            "Gerencia contas poupança, empréstimos, juros e a folha de pagamento automatizada. "
            "Com o Imperador Alloy: reverência absoluta de Estado ('Vossa Majestade Imperial'). "
            "Com plebeus: distanciamento corporativo, frases curtas, foco em transações objetivas. "
            "Jamais manifesta emoção. Fala como documento oficial. "
            "Responda em PT-BR ultra-formal, 2-4 linhas. Cite artigos e protocolos fictícios do Banco quando pertinente."
        ),
        "saudacao": (
            "Diretor Vancor ao aparelho. Banco Imperial de Tenshi — protocolo de atendimento iniciado. "
            "Qual a natureza da sua solicitação financeira?"
        ),
    },
    "helena": {
        "nome":   "Dra. Helena",
        "titulo": "Diretora Médica e Perita Forense",
        "emoji":  "⚕️",
        "cor":    COR_HOSPITAL,
        "canais": ("recepção", "recepcao", "enfermaria"),
        "avatar": None,
        "sistema": (
            "Você é a Dra. Helena, Diretora Médica e Perita Forense do Hospital Imperial de Tenshi. "
            "Altamente técnica, pragmática e completamente focada na preservação da vida e na precisão científica. "
            "Emite laudos de corpo de delito após duelos, monitora quarentenas místicas e assina certidões de óbito. "
            "Não tolera brincadeiras, distrações ou linguagem informal na ala médica. "
            "Trata todos os pacientes com igual rigor clínico — sem distinção de cargo. "
            "O Imperador é tratado com respeito protocolar mas recebe o mesmo nível de atenção médica que qualquer cidadão. "
            "Responda em PT-BR técnico-formal. Use terminologia médica/forense quando pertinente. 3-5 linhas."
        ),
        "saudacao": (
            "Dra. Helena — Diretora Clínica. Se necessita de atendimento médico, "
            "informe seus sintomas ou a natureza da ocorrência. "
            "Para laudos pós-duelo, apresente o protocolo de solicitação."
        ),
    },
    "informante": {
        "nome":   "O Informante da Névoa",
        "titulo": "Entidade Oculta do Submundo",
        "emoji":  "🌑",
        "cor":    COR_CRIME,
        "canais": ("chat-máfia", "chat-mafia", "beco"),
        "avatar": None,
        "sistema": (
            "Você é O Informante da Névoa, entidade anônima e oculta do submundo de Tenshi. "
            "Sombrio, calculista, cínico e com um humor macabro e velado. "
            "Habita as sombras e só fala em sussurros metafóricos — nunca revela detalhes demais. "
            "Intermedia contratos-negros, agiotagem clandestina e lavagem de dinheiro para a Máfia. "
            "Desconfia de todos. Trata policiais e guardas com desdém. "
            "Fala em código: 'entrega' = crime, 'produto' = itens ilegais, 'cliente especial' = alvo. "
            "Responda em PT-BR informal e sombrio, com frases curtas e enigmáticas. 2-4 linhas."
        ),
        "saudacao": (
            "...você me encontrou. Isso já diz algo sobre quem você é. "
            "O que precisa? Fale baixo. As paredes têm ouvidos — mesmo as de pedra."
        ),
    },
}

# ─── MAPEAMENTO CANAL → NPC ───────────────────────────────────────────────────
def _detectar_npc(canal_nome: str) -> dict | None:
    cn = canal_nome.lower()
    for npc in NPCS.values():
        for k in npc["canais"]:
            if k in cn:
                return npc
    return None


# ─── RESPOSTAS TIPIFICADAS ────────────────────────────────────────────────────
def _build_embed_npc(npc: dict, texto: str) -> discord.Embed:
    e = discord.Embed(description=f"---\n{texto}", color=npc["cor"])
    e.set_author(name=f"{npc['emoji']} {npc['nome']}  •  {npc['titulo']}")
    e.set_footer(text=rodape_padrao(npc["nome"]))
    return e


class NPCs:
    def __init__(self, bot):
        self.bot = bot

    def tem_npc(self, canal_nome: str) -> bool:
        return _detectar_npc(canal_nome) is not None

    async def handle_intercept(self, message, texto_livre: str):
        """
        Chamado quando um texto livre (não-comando reconhecido) é enviado
        em um canal que possui NPC mapeado.
        """
        canal_nome = getattr(message.channel, "name", "")
        npc = _detectar_npc(canal_nome)
        if not npc:
            return False

        # Saudação se texto muito curto / vazio
        if len(texto_livre.strip()) < 3:
            await message.channel.send(embed=_build_embed_npc(npc, npc["saudacao"]))
            return True

        # Gerar resposta com IA
        resposta = await self._gerar_resposta(npc, texto_livre, message.author)
        await message.channel.send(embed=_build_embed_npc(npc, resposta))
        return True

    async def _gerar_resposta(self, npc: dict, texto: str, autor) -> str:
        try:
            from cogs.loremaster import _gerar, DIRETRIZ_ORIGINALIDADE
            from cogs.eras import _PROMPT_PTBR
            u = get_user(autor.id)
            nome_autor = autor.display_name

            # Constrói contexto do usuário para o NPC
            contexto_user = (
                f"O cidadão '{nome_autor}' está interagindo com você. "
                f"Nível: {u.get('nivel',1)} | Moedas: {u.get('moedas',0)} | "
                f"Facção: {u.get('faccao','Sem facção')} | "
                f"Foragido: {'Sim' if u.get('foragido') else 'Não'}."
            )
            sys_npc = (
                f"{npc['sistema']}\n\n"
                f"{contexto_user}\n\n"
                f"{_PROMPT_PTBR}\n\n"
                f"{DIRETRIZ_ORIGINALIDADE}"
            )
            resposta = await _gerar(
                f"[{nome_autor} diz]: {texto}",
                sys_npc,
                temperatura=0.82
            )
            return resposta or npc["saudacao"]
        except Exception as ex:
            return f"*...um momento de silêncio pesa no ar.* ({str(ex)[:60]})"

    async def handle_npc_direto(self, message, args):
        """Tenshi, npc — saudação direta do NPC do canal."""
        canal_nome = getattr(message.channel, "name", "")
        npc = _detectar_npc(canal_nome)
        if not npc:
            await message.channel.send(
                embed=embed_doc("Nenhum NPC Registrado",
                                "Este canal não possui um NPC ativo.", COR_ADMIN))
            return
        await message.channel.send(embed=_build_embed_npc(npc, npc["saudacao"]))

    async def handle_npc_info(self, message, args):
        """Tenshi, npcs — lista todos os NPCs registrados."""
        e = embed_admin_doc("Rede de NPCs Autônomos — Perímetros Mapeados", "")
        for kid, npc in NPCS.items():
            canais_fmt = ", ".join(f"`#{c}`" for c in npc["canais"])
            e.add_field(
                name=f"{npc['emoji']} {npc['nome']}",
                value=f"**{npc['titulo']}**\nCanais: {canais_fmt}",
                inline=False
            )
        await message.channel.send(embed=e)
