"""Music System - Voice Channel Music Player"""

import asyncio
import json
import os
from typing import Optional

import discord
from discord.ext import commands
from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial

DATA_FILE = "data/music_queue.json"
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


class MusicQueue:
    def __init__(self):
        self.queue = []
        self.current = None
        self.voice_client = None
        self.loop = False

    def add(self, song: dict):
        self.queue.append(song)

    def next(self) -> Optional[dict]:
        if self.queue:
            return self.queue.pop(0)
        return None

    def clear(self):
        self.queue = []
        self.current = None

    def is_empty(self) -> bool:
        return len(self.queue) == 0


# Armazenar filas por servidor
server_queues = {}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_join(self, message, args):
        """Entra no canal de voz do usuário."""
        if not message.author.voice:
            await message.channel.send(embed=_embed("❌ Erro", "Você precisa estar em um canal de voz!", COR_PERIGO))
            return

        voice_channel = message.author.voice.channel
        
        # Verificar se já está conectado
        if message.guild.voice_client:
            await message.guild.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()
        
        await message.channel.send(embed=_embed("🎵 Conectado", f"Entrei no canal {voice_channel.mention}!", COR_SUCESSO))

    async def handle_leave(self, message, args):
        """Sai do canal de voz."""
        if not message.guild.voice_client:
            await message.channel.send(embed=_embed("❌ Erro", "Não estou conectado a nenhum canal de voz!", COR_PERIGO))
            return

        await message.guild.voice_client.disconnect()
        
        # Limpar fila do servidor
        if str(message.guild.id) in server_queues:
            del server_queues[str(message.guild.id)]
        
        await message.channel.send(embed=_embed("👋 Desconectado", "Saí do canal de voz.", COR_NEUTRO))

    async def handle_play(self, message, args):
        """Toca uma música (simulado - usa URLs do YouTube)."""
        if not message.author.voice:
            await message.channel.send(embed=_embed("❌ Erro", "Você precisa estar em um canal de voz!", COR_PERIGO))
            return

        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi play [nome da música ou URL]`", COR_NEUTRO))
            return

        # Conectar se não estiver
        if not message.guild.voice_client:
            await message.author.voice.channel.connect()

        song_name = " ".join(args)
        
        # Simular música (em produção, usaria youtube-dl ou similar)
        song = {
            "name": song_name,
            "url": f"https://youtube.com/watch?v=example",  # Placeholder
            "requested_by": str(message.author.id),
            "duration": "3:45"  # Placeholder
        }

        # Adicionar à fila
        guild_id = str(message.guild.id)
        if guild_id not in server_queues:
            server_queues[guild_id] = MusicQueue()
        
        server_queues[guild_id].add(song)
        
        await message.channel.send(embed=_embed("🎵 Adicionado à Fila", f"**{song_name}**\nDuração: {song['duration']}\nSolicitado por: {message.author.mention}", COR_SUCESSO))
        
        # Tocar se não estiver tocando nada
        if not server_queues[guild_id].current:
            await self._play_next(message.guild, message.channel)

    async def _play_next(self, guild, channel):
        """Toca a próxima música da fila."""
        guild_id = str(guild.id)
        
        if guild_id not in server_queues:
            return
        
        queue = server_queues[guild_id]
        song = queue.next()
        
        if not song:
            await channel.send(embed=_embed("🎵 Fila Vazia", "Não há mais músicas na fila.", COR_NEUTRO))
            return
        
        queue.current = song
        
        # Simular reprodução (em produção, usaria FFmpeg)
        await channel.send(embed=_embed("🎵 Tocando Agora", f"**{song['name']}**\nDuração: {song['duration']}", COR_DOURADO))
        
        # Simular término após 3 segundos (em produção, seria a duração real)
        await asyncio.sleep(3)
        
        # Tocar próxima
        await self._play_next(guild, channel)

    async def handle_skip(self, message, args):
        """Pula a música atual."""
        guild_id = str(message.guild.id)
        
        if guild_id not in server_queues or not server_queues[guild_id].current:
            await message.channel.send(embed=_embed("❌ Erro", "Não há música tocando.", COR_PERIGO))
            return
        
        await message.channel.send(embed=_embed("⏭️ Pulado", "Música pulada!", COR_SUCESSO))
        
        # Tocar próxima
        await self._play_next(message.guild, message.channel)

    async def handle_queue(self, message, args):
        """Mostra a fila de músicas."""
        guild_id = str(message.guild.id)
        
        if guild_id not in server_queues or server_queues[guild_id].is_empty():
            await message.channel.send(embed=_embed("📋 Fila Vazia", "Não há músicas na fila.", COR_NEUTRO))
            return
        
        queue = server_queues[guild_id]
        linhas = []
        
        if queue.current:
            linhas.append(f"🎵 **Tocando Agora:** {queue.current['name']}")
        
        for i, song in enumerate(queue.queue[:10], 1):
            linhas.append(f"{i}. {song['name']}")
        
        if len(queue.queue) > 10:
            linhas.append(f"... e mais {len(queue.queue) - 10} músicas")
        
        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("📋 Fila de Músicas", descricao, COR_DOURADO))

    async def handle_pause(self, message, args):
        """Pausa a música atual."""
        if not message.guild.voice_client or not message.guild.voice_client.is_playing():
            await message.channel.send(embed=_embed("❌ Erro", "Não há música tocando.", COR_PERIGO))
            return
        
        message.guild.voice_client.pause()
        await message.channel.send(embed=_embed("⏸️ Pausado", "Música pausada.", COR_NEUTRO))

    async def handle_resume(self, message, args):
        """Retoma a música pausada."""
        if not message.guild.voice_client or not message.guild.voice_client.is_paused():
            await message.channel.send(embed=_embed("❌ Erro", "Não há música pausada.", COR_PERIGO))
            return
        
        message.guild.voice_client.resume()
        await message.channel.send(embed=_embed("▶️ Retomado", "Música retomada.", COR_SUCESSO))

    async def handle_stop(self, message, args):
        """Para a música e limpa a fila."""
        if not message.guild.voice_client:
            await message.channel.send(embed=_embed("❌ Erro", "Não estou conectado a nenhum canal.", COR_PERIGO))
            return
        
        message.guild.voice_client.stop()
        
        guild_id = str(message.guild.id)
        if guild_id in server_queues:
            server_queues[guild_id].clear()
        
        await message.channel.send(embed=_embed("⏹️ Parado", "Música parada e fila limpa.", COR_NEUTRO))

    async def handle_volume(self, message, args):
        """Ajusta o volume."""
        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi volume [0-100]`", COR_NEUTRO))
            return
        
        try:
            volume = int(args[0])
            if volume < 0 or volume > 100:
                await message.channel.send(embed=_embed("❌ Erro", "Volume deve estar entre 0 e 100.", COR_PERIGO))
                return
            
            # Em produção, ajustaria o volume do FFmpeg
            await message.channel.send(embed=_embed("🔊 Volume", f"Volume ajustado para {volume}%", COR_SUCESSO))
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Volume deve ser um número.", COR_PERIGO))

    async def handle_np(self, message, args):
        """Mostra a música atual (Now Playing)."""
        guild_id = str(message.guild.id)
        
        if guild_id not in server_queues or not server_queues[guild_id].current:
            await message.channel.send(embed=_embed("❌ Erro", "Não há música tocando.", COR_PERIGO))
            return
        
        song = server_queues[guild_id].current
        await message.channel.send(embed=_embed("🎵 Tocando Agora", f"**{song['name']}**\nDuração: {song['duration']}\nSolicitado por: <@{song['requested_by']}>", COR_DOURADO))
