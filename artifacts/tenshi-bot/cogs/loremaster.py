import discord
from discord.ext import commands
import os
from groq import Groq
from utils import embed_imperial, IMPERADOR_ID

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

NICHOS = {
    "militar": {
        "emoji": "⚔️",
        "nome": "Guarda Imperial / Fronteiras",
        "prompt_contexto": "Foco em combate, invasões, monstros nas fronteiras, batalhas épicas e rebeliões militares dentro do Império de Tenshi.",
    },
    "politico": {
        "emoji": "👑",
        "nome": "Corte de Tenshi / Nobreza",
        "prompt_contexto": "Foco em intrigas palacianas, disputas de influência entre nobres, traições, conspirações e decretos que afetam a economia e o poder do reino de Tenshi.",
    },
    "esoterico": {
        "emoji": "🔮",
        "nome": "Subterrâneo / Magia / Tarot",
        "prompt_contexto": "Foco em mistérios sobre runas antigas, profecias obscuras, portais mágicos, criaturas do além e segredos que exigem investigação mística e conhecimento esotérico.",
    },
}

SYSTEM_PROMPT_LORE = """Você é Tenshi, o Oráculo Imemorial do Império de Tenshi — um narrador misterioso, imponente e poético.
Crie narrativas curtas (3-5 parágrafos) para iniciar sessões de RPG de texto.
Use linguagem rica, imersiva e imperial. Evite clichês genéricos.
O líder supremo é o Imperador Alloy, uma divindade viva de poder absoluto.
Escreva APENAS a narrativa, sem introduções ou explicações. Use markdown do Discord (**, *, _) para formatação."""

SYSTEM_PROMPT_PROFECIA = """Você é o Oráculo Eterno de Tenshi, voz dos deuses e intérprete do destino.
Crie uma Profecia de Tenshi épica (4-6 parágrafos) que mude o rumo da história do servidor.
Deve ser misteriosa, abrangente e desafiar guerreiros de todos os nichos (militar, político e esotérico).
Use linguagem profética, arcaica e grandiosa. Inclua símbolos, presságios e um mistério central.
Escreva APENAS a profecia, sem introduções. Use markdown do Discord para dramatismo."""

SYSTEM_PROMPT_INTERAGIR = """Você é Tenshi, espírito guardião do Império.
Responda interações dos usuários de forma mística, imponente e imersiva em 1-3 frases.
Se o usuário interagir com o Imperador Alloy, demonstre reverência extrema e divindade.
Use linguagem formal imperial. Seja criativo e único em cada resposta."""


async def gerar_lore_ai(prompt: str, system: str = SYSTEM_PROMPT_LORE) -> str:
    try:
        resposta = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.9,
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        return f"*Os Oráculos de Tenshi silenciam por um momento... ({str(e)[:50]})*"


class LoreMaster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_cronica(self, message, args):
        if not args:
            nichos_str = "\n".join([f"{v['emoji']} `{k}` — {v['nome']}" for k, v in NICHOS.items()])
            await message.channel.send(embed=embed_imperial(
                "📖 Crônicas de Tenshi",
                f"Escolha um nicho: `Tenshi, cronica [nicho]`\n\n{nichos_str}",
                0x4B0082
            ))
            return

        nicho_key = args[0].lower()
        nicho = NICHOS.get(nicho_key)

        if not nicho:
            nichos_disponiveis = " | ".join(NICHOS.keys())
            await message.channel.send(embed=embed_imperial("❌ Nicho inválido", f"Nichos disponíveis: **{nichos_disponiveis}**", 0x8B0000))
            return

        await message.channel.send(embed=embed_imperial(
            f"{nicho['emoji']} O Oráculo Consulta os Pergaminhos...",
            "*As chamas das tochas imperiais tremem enquanto o destino é tecido...*",
            0x1a1a2e
        ))

        prompt = f"""Crie uma narrativa de RPG para o nicho {nicho['nome']} no Império de Tenshi.
        Contexto: {nicho['prompt_contexto']}
        Jogador: {message.author.display_name}
        Inclua: um gancho de missão, atmosfera imersiva e um mistério ou conflito central."""

        narrativa = await gerar_lore_ai(prompt)

        embed = discord.Embed(
            title=f"{nicho['emoji']} CRÔNICA IMPERIAL — {nicho['nome'].upper()}",
            description=narrativa,
            color=0x4B0082
        )
        embed.set_author(name="📖 LoreMaster de Tenshi — O Oráculo Fala")
        embed.set_footer(text=f"⚔️ Esta narrativa foi tecida pelo destino para {message.author.display_name}")
        await message.channel.send(embed=embed)

    async def handle_evento_lore(self, message):
        if not message.author.guild_permissions.administrator and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial(
                "🚫 Acesso Negado",
                "*Apenas os Administradores e o Imperador Alloy podem lançar Profecias Imperiais.*",
                0x8B0000
            ))
            return

        await message.channel.send(embed=embed_imperial(
            "🔮 O Véu se Rasga...",
            "*Uma energia ancestral emana dos quatro cantos do Império... O Oráculo desperta!*",
            0x1a1a2e
        ))

        prompt = f"""Lance uma Profecia de Tenshi épica que:
        - Mude o rumo da história do servidor
        - Desafie guerreiros de todos os nichos (militar, político e esotérico) a se unirem
        - Contenha um grande mistério central que os jogadores precisam resolver
        - Mencione o Imperador Alloy como a figura central do destino
        - Seja lançada como um evento global urgente"""

        profecia = await gerar_lore_ai(prompt, SYSTEM_PROMPT_PROFECIA)

        embed = discord.Embed(
            title="🌌 ⚜️ PROFECIA DE TENSHI — O DESTINO FALA ⚜️ 🌌",
            description=profecia,
            color=0x8B0000
        )
        embed.set_author(name="🔮 O Oráculo Eterno de Tenshi")
        embed.set_footer(text="⚔️ Guerreiros de todos os nichos — a hora de se unir chegou! Que o Império prevaleça.")

        try:
            await message.channel.send("@everyone", embed=embed)
        except Exception:
            await message.channel.send(embed=embed)

    async def handle_lore_natural(self, message, texto: str) -> bool:
        """Processa interações de linguagem natural com IA"""
        gatilhos = ["o que é tenshi", "me conta sobre tenshi", "história de tenshi", "lore de tenshi"]
        if any(g in texto.lower() for g in gatilhos):
            prompt = f"O usuário {message.author.display_name} pergunta: '{texto}'. Responda sobre a história e lore do Império de Tenshi de forma imersiva."
            resposta = await gerar_lore_ai(prompt, SYSTEM_PROMPT_INTERAGIR)
            await message.channel.send(embed=embed_imperial("📖 O Oráculo Responde", resposta, 0x4B0082))
            return True
        return False
