import discord
import os
from groq import Groq
from utils import embed_imperial, IMPERADOR_ID

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODELO = "llama-3.3-70b-versatile"

NICHOS = {
    "militar": {
        "emoji": "⚔️",
        "nome": "Guarda Imperial / Fronteiras",
        "prompt_contexto": "Foco em combate épico, invasões nas fronteiras, monstros colossais, batalhas e rebeliões militares dentro do Império de Tenshi. Tom guerreiro e brutal.",
    },
    "politico": {
        "emoji": "👑",
        "nome": "Corte de Tenshi / Nobreza",
        "prompt_contexto": "Foco em intrigas palacianas profundas, conspirações de nobres, traições, alianças secretas e decretos que mudam o destino econômico e político de Tenshi. Tom elegante e sinuoso.",
    },
    "esoterico": {
        "emoji": "🔮",
        "nome": "Subterrâneo / Magia / Tarot",
        "prompt_contexto": "Foco em mistérios de runas ancestrais, profecias obscuras que se cumprem, portais dimensionais, criaturas do além e segredos que só os iniciados da Ordem Esotérica conhecem. Tom místico e perturbador.",
    },
    "mafia": {
        "emoji": "🔫",
        "nome": "Submundo / Máfia Imperial",
        "prompt_contexto": "Foco no submundo do Império, famílias do crime, operações clandestinas, guerras entre clãs rivais, tráfico de artefatos proibidos. Tom noir e implacável.",
    },
    "enterprise": {
        "emoji": "🏢",
        "nome": "Tenshi Enterprise / Corporativo",
        "prompt_contexto": "Foco nas guerras corporativas imperiais, fusões e aquisições violentas, sabotagem entre empresas, espionagem industrial e o poder do dinheiro no Império. Tom corporativo e implacável.",
    },
}

SYSTEM_PROMPT_LORE = """Você é o Oráculo Imemorial do Império de Tenshi — narrador misterioso, imponente e poético.
Crie narrativas curtas (3-5 parágrafos) para iniciar sessões de RPG de texto.
Linguagem: rica, imersiva e imperial. Sem clichês genéricos.
O líder supremo é o Imperador Alloy — uma divindade viva de poder absoluto.
Escreva APENAS a narrativa, sem introduções ou metaTextos. Use markdown Discord (**, *, _)."""

SYSTEM_PROMPT_PROFECIA = """Você é o Oráculo Eterno de Tenshi, voz dos deuses e intérprete do destino.
Crie uma Profecia de Tenshi épica (4-6 parágrafos) que mude o rumo da história do servidor.
Deve ser misteriosa e desafiar guerreiros de todos os nichos a se unirem.
Linguagem profética, arcaica e grandiosa. Inclua símbolos e um mistério central.
Escreva APENAS a profecia. Use markdown Discord para dramatismo."""

SYSTEM_PROMPT_CHAT = """Você é Tenshi, espírito guardião do Império — misterioso, imponente, sábio.
Responda em 1-3 frases, em português, de forma mística e imperial.
Se mencionarem o Imperador Alloy, demonstre reverência extrema."""


async def gerar_lore_ai(prompt: str, system: str = SYSTEM_PROMPT_LORE) -> str:
    try:
        resposta = groq_client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=900,
            temperature=0.92,
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        return f"*Os Oráculos silenciam brevemente... ({str(e)[:80]})*"


class LoreMaster:
    def __init__(self, bot):
        self.bot = bot

    async def handle_cronica(self, message, args):
        if not args:
            embed = discord.Embed(
                title="📖 CRÔNICAS DE TENSHI — LoreMaster IA",
                description="Escolha um nicho para gerar uma narrativa épica de RPG:",
                color=0x4B0082
            )
            for key, n in NICHOS.items():
                embed.add_field(name=f"{n['emoji']} {n['nome']}", value=f"`Tenshi, cronica {key}`", inline=True)
            await message.channel.send(embed=embed)
            return

        nicho_key = args[0].lower()
        nicho = NICHOS.get(nicho_key)
        if not nicho:
            disponiveis = " | ".join(NICHOS.keys())
            await message.channel.send(embed=embed_imperial("❌ Nicho inválido", f"Disponíveis: **{disponiveis}**", 0x8B0000))
            return

        msg_loading = await message.channel.send(embed=embed_imperial(
            f"{nicho['emoji']} O Oráculo Tece o Destino...",
            "*As chamas das tochas imperiais tremem enquanto a narrativa é forjada...*",
            0x1a1a2e
        ))

        tema_extra = " ".join(args[1:]) if len(args) > 1 else ""
        prompt = (
            f"Crie uma narrativa de RPG para o nicho: {nicho['nome']}.\n"
            f"Contexto: {nicho['prompt_contexto']}\n"
            f"Jogador principal: {message.author.display_name}\n"
            + (f"Tema adicional: {tema_extra}\n" if tema_extra else "") +
            "Inclua: um gancho de missão imersivo, atmosfera densa e um mistério ou conflito central urgente."
        )

        narrativa = await gerar_lore_ai(prompt)

        embed = discord.Embed(
            title=f"{nicho['emoji']} CRÔNICA — {nicho['nome'].upper()}",
            description=narrativa,
            color=0x4B0082
        )
        embed.set_author(name="📖 LoreMaster de Tenshi • O Oráculo Fala")
        embed.set_footer(text=f"Narrativa tecida pelo destino para {message.author.display_name}")
        try:
            await msg_loading.edit(embed=embed)
        except Exception:
            await message.channel.send(embed=embed)

    async def handle_evento_lore(self, message):
        tem_perm = False
        try:
            tem_perm = message.author.guild_permissions.administrator
        except Exception:
            pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial(
                "🚫 Acesso Negado",
                "*Apenas Administradores e o Imperador Alloy podem lançar Profecias Imperiais.*",
                0x8B0000
            ))
            return

        msg_loading = await message.channel.send(embed=embed_imperial(
            "🔮 O Véu se Rasga...",
            "*Uma energia ancestral emana dos quatro cantos do Império...*",
            0x1a1a2e
        ))

        prompt = (
            "Lance uma Profecia de Tenshi épica que:\n"
            "- Mude o rumo da história do servidor de Discord\n"
            "- Desafie guerreiros de todos os nichos (militar, político, esotérico, máfia, enterprise) a se unirem\n"
            "- Contenha um grande mistério que os jogadores precisam resolver juntos\n"
            "- Mencione o Imperador Alloy como a figura central e divina do destino\n"
            "- Seja um evento global dramático e urgente\n"
            "Use símbolos, profecias em versos e linguagem arcaica grandiosa."
        )

        profecia = await gerar_lore_ai(prompt, SYSTEM_PROMPT_PROFECIA)

        embed = discord.Embed(
            title="🌌 ⚜️ PROFECIA DE TENSHI — O DESTINO FALA ⚜️ 🌌",
            description=profecia,
            color=0x8B0000
        )
        embed.set_author(name="🔮 O Oráculo Eterno de Tenshi")
        embed.set_footer(text="⚔️ Guerreiros de todos os nichos — a hora de se unir chegou!")

        try:
            await msg_loading.edit(embed=embed)
            await message.channel.send("@everyone ⚔️ Uma profecia foi lançada sobre o Império!")
        except Exception:
            await message.channel.send(embed=embed)

    async def handle_lore_natural(self, message, texto: str) -> bool:
        gatilhos = [
            "o que é tenshi", "me conta sobre tenshi", "história de tenshi",
            "lore de tenshi", "quem é alloy", "o que é o império"
        ]
        if any(g in texto.lower() for g in gatilhos):
            prompt = f"O usuário {message.author.display_name} pergunta: '{texto}'. Responda sobre Tenshi de forma mística."
            resposta = await gerar_lore_ai(prompt, SYSTEM_PROMPT_CHAT)
            await message.channel.send(embed=embed_imperial("📖 O Oráculo Responde", resposta, 0x4B0082))
            return True
        return False
