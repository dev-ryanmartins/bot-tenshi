"""Mini-Games System - Fun Games for Users"""

import json
import os
import random
from datetime import UTC, datetime
from typing import Optional

import discord
from discord.ext import commands
from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial

DATA_FILE = "data/minigames.json"
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


class MiniGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    async def handle_adivinhacao(self, message, args):
        """Jogo de adivinhação de números."""
        if str(message.channel.id) in self.active_games:
            await message.channel.send(embed=_embed("❌ Jogo em Andamento", "Já há um jogo acontecendo neste canal!", COR_PERIGO))
            return
        
        numero = random.randint(1, 100)
        self.active_games[str(message.channel.id)] = {
            "game": "adivinhacao",
            "number": numero,
            "attempts": 0,
            "max_attempts": 10,
            "started_by": message.author.id
        }
        
        await message.channel.send(embed=_embed("🔢 Adivinhação", f"Pensei em um número entre 1 e 100!\nVocê tem 10 tentativas.\nUse `tenshi guess [número]` para adivinhar!", COR_DOURADO))

    async def handle_guess(self, message, args):
        """Adivinha o número no jogo de adivinhação."""
        channel_id = str(message.channel.id)
        
        if channel_id not in self.active_games or self.active_games[channel_id]["game"] != "adivinhacao":
            await message.channel.send(embed=_embed("❌ Sem Jogo", "Não há jogo de adivinhação ativo. Use `tenshi adivinhacao` para começar!", COR_PERIGO))
            return
        
        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi guess [número]`", COR_NEUTRO))
            return
        
        try:
            guess = int(args[0])
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Digite um número válido!", COR_PERIGO))
            return
        
        game = self.active_games[channel_id]
        game["attempts"] += 1
        
        if guess == game["number"]:
            attempts = game["attempts"]
            reward = 100 - (attempts * 5)  # Menos tentativas = mais recompensa
            reward = max(10, reward)
            
            user = get_user(message.author.id)
            user["moedas"] += reward
            save_user(message.author.id, user)
            
            del self.active_games[channel_id]
            await message.channel.send(embed=_embed(f"🎉 Parabéns {message.author.display_name}!", f"Você acertou em {attempts} tentativas!\nRecompensa: {reward} moedas!", COR_SUCESSO))
        
        elif game["attempts"] >= game["max_attempts"]:
            del self.active_games[channel_id]
            await message.channel.send(embed=_embed("😢 Game Over", f"Você não conseguiu adivinhar! O número era {game['number']}.", COR_PERIGO))
        
        elif guess < game["number"]:
            await message.channel.send(embed=_embed("📈 Mais Alto!", f"Tentativa {game['attempts']}/{game['max_attempts']}: O número é maior!", COR_NEUTRO))
        
        else:
            await message.channel.send(embed=_embed("📉 Mais Baixo!", f"Tentativa {game['attempts']}/{game['max_attempts']}: O número é menor!", COR_NEUTRO))

    async def handle_pedra_papel_tesoura(self, message, args):
        """Jogo de Pedra, Papel e Tesoura."""
        if not message.mentions:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi ppt @usuario` para desafiar alguém!", COR_NEUTRO))
            return
        
        opponent = message.mentions[0]
        if opponent.bot:
            await message.channel.send(embed=_embed("❌ Erro", "Não pode jogar contra bots!", COR_PERIGO))
            return
        
        if opponent.id == message.author.id:
            await message.channel.send(embed=_embed("❌ Erro", "Não pode jogar contra si mesmo!", COR_PERIGO))
            return
        
        # Simular jogo (em produção, seria interativo)
        choices = ["pedra", "papel", "tesoura"]
        player1 = random.choice(choices)
        player2 = random.choice(choices)
        
        emojis = {"pedra": "🪨", "papel": "📄", "tesoura": "✂️"}
        
        # Determinar vencedor
        if player1 == player2:
            result = "Empate!"
            winner = None
        elif (player1 == "pedra" and player2 == "tesoura") or \
             (player1 == "papel" and player2 == "pedra") or \
             (player1 == "tesoura" and player2 == "papel"):
            result = f"{message.author.mention} venceu!"
            winner = message.author.id
        else:
            result = f"{opponent.mention} venceu!"
            winner = opponent.id
        
        descricao = (
            f"{message.author.mention}: {emojis[player1]} {player1}\n"
            f"{opponent.mention}: {emojis[player2]} {player2}\n\n"
            f"**{result}**"
        )
        
        await message.channel.send(embed=_embed("✂️ Pedra, Papel e Tesoura", descricao, COR_DOURADO))

    async def handle_dado_sorte(self, message, args):
        """Jogo de dado da sorte."""
        user = get_user(message.author.id)
        
        if user["moedas"] < 10:
            await message.channel.send(embed=_embed("❌ Saldo Insuficiente", "Você precisa de 10 moedas para jogar!", COR_PERIGO))
            return
        
        user["moedas"] -= 10
        save_user(message.author.id, user)
        
        # Rolagem do dado
        roll = random.randint(1, 6)
        
        rewards = {
            1: 0,
            2: 5,
            3: 10,
            4: 20,
            5: 50,
            6: 100
        }
        
        reward = rewards[roll]
        user["moedas"] += reward
        save_user(message.author.id, user)
        
        emojis = {1: "😢", 2: "😐", 3: "🙂", 4: "😊", 5: "😃", 6: "🎉"}
        
        if reward > 0:
            descricao = f"Você tirou {roll}! {emojis[roll]}\nGanhou {reward} moedas!"
            cor = COR_SUCESSO
        else:
            descricao = f"Você tirou {roll}! {emojis[roll]}\nNão ganhou nada dessa vez."
            cor = COR_NEUTRO
        
        await message.channel.send(embed=_embed("🎲 Dado da Sorte", descricao, cor))

    async def handle_quiz(self, message, args):
        """Quiz rápido com perguntas."""
        perguntas = [
            {
                "pergunta": "Qual é a capital do Brasil?",
                "opcoes": ["Rio de Janeiro", "São Paulo", "Brasília", "Salvador"],
                "resposta": 2
            },
            {
                "pergunta": "Quem fundou o Império de Tenshi?",
                "opcoes": ["Alloy Tenshi", "Discord", "Bill Gates", "Elon Musk"],
                "resposta": 0
            },
            {
                "pergunta": "Qual é o maior planeta do sistema solar?",
                "opcoes": ["Terra", "Marte", "Júpiter", "Saturno"],
                "resposta": 2
            },
            {
                "pergunta": "Em que ano o Império de Tenshi foi fundado?",
                "opcoes": ["2015", "2016", "2017", "2018"],
                "resposta": 1
            }
        ]
        
        pergunta = random.choice(perguntas)
        
        # Criar embed com opções
        descricao = f"**{pergunta['pergunta']}**\n\n"
        for i, opcao in enumerate(pergunta["opcoes"]):
            descricao += f"{i + 1}. {opcao}\n"
        
        descricao += "\nResponda com o número da opção!"
        
        self.active_games[str(message.channel.id)] = {
            "game": "quiz",
            "answer": pergunta["resposta"],
            "question": pergunta["pergunta"],
            "started_by": message.author.id
        }
        
        await message.channel.send(embed=_embed("🧠 Quiz Rápido", descricao, COR_DOURADO))

    async def handle_quiz_answer(self, message, args):
        """Responde ao quiz."""
        channel_id = str(message.channel.id)
        
        if channel_id not in self.active_games or self.active_games[channel_id]["game"] != "quiz":
            await message.channel.send(embed=_embed("❌ Sem Quiz", "Não há quiz ativo. Use `tenshi quiz` para começar!", COR_PERIGO))
            return
        
        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi quiz-answer [número]`", COR_NEUTRO))
            return
        
        try:
            answer = int(args[0]) - 1  # Converter para 0-indexed
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Digite um número válido!", COR_PERIGO))
            return
        
        game = self.active_games[channel_id]
        
        if answer == game["answer"]:
            reward = 50
            user = get_user(message.author.id)
            user["moedas"] += reward
            save_user(message.author.id, user)
            
            del self.active_games[channel_id]
            await message.channel.send(embed=_embed("✅ Correto!", f"Você acertou! Ganhou {reward} moedas!", COR_SUCESSO))
        else:
            del self.active_games[channel_id]
            await message.channel.send(embed=_embed("❌ Errado!", "Que pena! Tente novamente com `tenshi quiz`.", COR_PERIGO))

    async def handle_memoria(self, message, args):
        """Jogo da memória - mostrar sequência de emojis."""
        emojis = ["🍎", "🍊", "🍋", "🍇", "🍓", "🍒", "🥝", "🍑"]
        sequencia = random.sample(emojis, 5)
        
        self.active_games[str(message.channel.id)] = {
            "game": "memoria",
            "sequence": sequencia,
            "started_by": message.author.id
        }
        
        await message.channel.send(embed=_embed("🧠 Jogo da Memória", f"Memorize esta sequência:\n\n{' '.join(sequencia)}\n\nUse `tenshi memoria-responder [sequência]` para responder!", COR_DOURADO))

    async def handle_memoria_responder(self, message, args):
        """Responde ao jogo da memória."""
        channel_id = str(message.channel.id)
        
        if channel_id not in self.active_games or self.active_games[channel_id]["game"] != "memoria":
            await message.channel.send(embed=_embed("❌ Sem Jogo", "Não há jogo de memória ativo. Use `tenshi memoria` para começar!", COR_PERIGO))
            return
        
        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi memoria-responder [sequência de emojis]`", COR_NEUTRO))
            return
        
        resposta = args
        game = self.active_games[channel_id]
        sequencia = game["sequence"]
        
        if resposta == sequencia:
            reward = 75
            user = get_user(message.author.id)
            user["moedas"] += reward
            save_user(message.author.id, user)
            
            del self.active_games[channel_id]
            await message.channel.send(embed=_embed("✅ Perfeito!", f"Você memorizou a sequência! Ganhou {reward} moedas!", COR_SUCESSO))
        else:
            del self.active_games[channel_id]
            await message.channel.send(embed=_embed("❌ Errado!", f"A sequência correta era: {' '.join(sequencia)}", COR_PERIGO))

    async def handle_jogos(self, message, args):
        """Lista todos os mini-jogos disponíveis."""
        jogos = [
            "🔢 **adivinhacao** - Adivinhe o número entre 1 e 100",
            "✂️ **ppt** - Pedra, Papel e Tesoura contra outro jogador",
            "🎲 **dado** - Jogue o dado da sorte (10 moedas)",
            "🧠 **quiz** - Responda perguntas e ganhe moedas",
            "🧠 **memoria** - Memorize sequências de emojis"
        ]
        
        descricao = "**Mini-Jogos Disponíveis:**\n\n" + "\n".join(jogos)
        await message.channel.send(embed=_embed("🎮 Mini-Jogos", descricao, COR_DOURADO))
