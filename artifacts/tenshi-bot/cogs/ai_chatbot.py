"""Advanced AI Chatbot - Conversational AI Assistant"""

import json
import os
from datetime import UTC, datetime
from typing import Optional

import discord
from discord.ext import commands
from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial

DATA_FILE = "data/ai_conversations.json"
COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


def _load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_data(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


# Respostas inteligentes baseadas em contexto
RESPONSES = {
    "saudacao": [
        "Olá! Sou Tenshi, sua assistente imperial. Como posso ajudar?",
        "Saudações, cidadão! O que deseja saber sobre o Império?",
        "Bem-vindo! Estou aqui para auxiliar em suas aventuras."
    ],
    "ajuda": [
        "Posso ajudar com comandos, informações sobre o RPG, ou conversar sobre qualquer tema!",
        "Use `tenshi ajuda` para ver todos os comandos disponíveis.",
        "Estou à disposição para tirar suas dúvidas sobre o Império de Tenshi."
    ],
    "economia": [
        "A economia do Império é robusta! Use `tenshi carteira` para ver seu saldo.",
        "Você pode ganhar moedas trabalhando, completando missões e participando de eventos.",
        "O mercado imperial oferece diversos itens para melhorar seu personagem."
    ],
    "rpg": [
        "O RPG de Tenshi possui sistemas de combate, economia, família e muito mais!",
        "Crie sua ficha com `tenshi criar-ficha` para começar sua jornada.",
        "Suba de nível treinando e completando missões para se tornar lendário."
    ],
    "familia": [
        "O sistema de família permite criar laços com outros jogadores.",
        "Use `tenshi painel-admin` (se for admin) para gerenciar parentescos.",
        "Casamentos criam vínculos especiais e concedem benefícios."
    ],
    "imperador": [
        "O Imperador Alloy Tenshi é o fundador e governante eterno do Império.",
        "Sua sabedoria guia todas as decisões do reino.",
        "O Imperador pode usar comandos especiais e tem acesso total ao sistema."
    ],
    "default": [
        "Interessante! Conte-me mais sobre isso.",
        "Entendo. Há algo específico que gostaria de saber?",
        "Estou processando... Como posso ajudar melhor?",
        "Hmm, deixa eu pensar... O que mais você gostaria de discutir?"
    ]
}


class AIChatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversation_context = {}

    async def handle_chat(self, message, args):
        """Conversa com a IA."""
        if not args:
            await message.channel.send(embed=_embed("💬 Chat com Tenshi", "Digite algo para conversar comigo! Ex: `tenshi chat olá`", COR_DOURADO))
            return

        texto = " ".join(args).lower()
        user_id = str(message.author.id)
        
        # Carregar histórico de conversa
        data = _load_data()
        historico = data.get(user_id, [])
        
        # Detectar intenção
        resposta = self._gerar_resposta(texto, historico)
        
        # Salvar no histórico
        historico.append({
            "usuario": " ".join(args),
            "tenshi": resposta,
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        # Manter apenas últimas 20 mensagens
        if len(historico) > 20:
            historico = historico[-20:]
        
        data[user_id] = historico
        _save_data(data)
        
        await message.channel.send(embed=_embed(f"💬 Tenshi responde:", resposta, COR_DOURADO))

    def _gerar_resposta(self, texto: str, historico: list) -> str:
        """Gera resposta baseada no contexto."""
        # Detectar tópicos específicos
        if any(p in texto for p in ["olá", "oi", "bom dia", "boa tarde", "boa noite", "eai", "eae"]):
            import random
            return random.choice(RESPONSES["saudacao"])
        
        if any(p in texto for p in ["ajuda", "help", "comandos", "como"]):
            import random
            return random.choice(RESPONSES["ajuda"])
        
        if any(p in texto for p in ["dinheiro", "moedas", "economia", "rico", "pobre"]):
            import random
            return random.choice(RESPONSES["economia"])
        
        if any(p in texto for p in ["rpg", "jogo", "jogar", "aventura", "missão"]):
            import random
            return random.choice(RESPONSES["rpg"])
        
        if any(p in texto for p in ["família", "casamento", "parentesco", "casar"]):
            import random
            return random.choice(RESPONSES["familia"])
        
        if any(p in texto for p in ["imperador", "alloy", "rei", "líder"]):
            import random
            return random.choice(RESPONSES["imperador"])
        
        # Resposta padrão
        import random
        return random.choice(RESPONSES["default"])

    async def handle_historico_chat(self, message, args):
        """Mostra o histórico de conversa com a IA."""
        user_id = str(message.author.id)
        data = _load_data()
        historico = data.get(user_id, [])
        
        if not historico:
            await message.channel.send(embed=_embed("📝 Histórico Vazio", "Você ainda não conversou comigo!", COR_NEUTRO))
            return
        
        linhas = []
        for i, msg in enumerate(historico[-10:], 1):
            linhas.append(f"**{i}. Você:** {msg['usuario']}")
            linhas.append(f"   **Tenshi:** {msg['tenshi']}\n")
        
        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("📝 Últimas Conversas", descricao, COR_DOURADO))

    async def handle_limpar_chat(self, message, args):
        """Limpa o histórico de conversa."""
        user_id = str(message.author.id)
        data = _load_data()
        
        if user_id in data:
            del data[user_id]
            _save_data(data)
            await message.channel.send(embed=_embed("🗑️ Histórico Limpo", "Seu histórico de conversa foi apagado.", COR_SUCESSO))
        else:
            await message.channel.send(embed=_embed("📝 Histórico Vazio", "Não há histórico para limpar.", COR_NEUTRO))

    async def handle_pergunta(self, message, args):
        """Faz uma pergunta específica à IA."""
        if not args:
            await message.channel.send(embed=_embed("❓ Pergunta", "Use: `tenshi pergunta [sua pergunta]`", COR_NEUTRO))
            return
        
        pergunta = " ".join(args)
        
        # Respostas inteligentes para perguntas comuns
        respostas_perguntas = {
            "qual o melhor comando": "O melhor comando depende do que você quer! `tenshi ajuda` mostra todos.",
            "como ganhar moedas": "Trabalhe com `tenshi trabalhar`, complete missões e participe de eventos!",
            "como subir de nível": "Use `tenshi treinar` regularmente e complete missões para ganhar XP.",
            "o que fazer no servidor": "Explore o RPG, faça amigos, participe de eventos e suba no ranking!",
            "quem é o imperador": "O Imperador Alloy Tenshi é o fundador e governante eterno do Império.",
            "como criar família": "Use `tenshi familia criar [nome]` para fundar sua própria família.",
            "tem casino": "Sim! Use `tenshi cassino` para acessar jogos de azar.",
            "como casar": "Use `tenshi pedido @usuario` para pedir alguém em casamento."
        }
        
        pergunta_lower = pergunta.lower()
        resposta = None
        
        for chave, valor in respostas_perguntas.items():
            if chave in pergunta_lower:
                resposta = valor
                break
        
        if not resposta:
            resposta = f"Essa é uma ótima pergunta! Sobre '{pergunta}', recomendo verificar `tenshi ajuda` ou perguntar a outros membros do servidor."
        
        await message.channel.send(embed=_embed(f"❓ Pergunta: {pergunta}", resposta, COR_DOURADO))
