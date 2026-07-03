"""Event System - Scheduled Events and Activities"""

import json
import os
import asyncio
from datetime import UTC, datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands, tasks
from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial

DATA_FILE = "data/events.json"
COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


def _load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return _create_default_events()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return _create_default_events()


def _save_data(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _create_default_events() -> dict:
    return {
        "events": {},
        "active_events": {},
        "participants": {}
    }


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


class EventSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_events.start()

    def cog_unload(self):
        self.check_events.cancel()

    @tasks.loop(minutes=1)
    async def check_events(self):
        """Verifica eventos agendados."""
        data = _load_data()
        now = datetime.now(UTC).isoformat()
        
        for event_id, event in data["events"].items():
            if event["status"] == "scheduled" and event["scheduled_time"] <= now:
                # Iniciar evento
                await self._start_event(event_id, event)
                
                # Atualizar status
                event["status"] = "active"
                event["started_at"] = now
                _save_data(data)

    @check_events.before_loop
    async def before_check_events(self):
        await self.bot.wait_until_ready()

    async def _start_event(self, event_id: str, event: dict):
        """Inicia um evento."""
        guild_id = event.get("guild_id")
        if not guild_id:
            return
        
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            return
        
        channel_id = event.get("channel_id")
        if not channel_id:
            return
        
        channel = guild.get_channel(int(channel_id))
        if not channel:
            return
        
        # Anunciar início do evento
        embed = discord.Embed(
            title=f"🎉 {event['name']} Começou!",
            description=event["description"],
            color=COR_SUCESSO
        )
        embed.add_field(name="Duração", value=event.get("duration", "1 hora"))
        embed.add_field(name="Recompensa", value=event.get("reward", "Moedas"))
        embed.set_footer(text=RODAPE_IMPERIAL)
        
        await channel.send("@everyone", embed=embed)
        
        # Adicionar aos eventos ativos
        data = _load_data()
        data["active_events"][event_id] = {
            "started_at": datetime.now(UTC).isoformat(),
            "participants": []
        }
        _save_data(data)

    async def handle_create_event(self, message, args):
        """Cria um novo evento."""
        if not message.author.guild_permissions.administrator and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem criar eventos.", COR_PERIGO))
            return

        if len(args) < 2:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi create-event [nome] [descrição]`", COR_NEUTRO))
            return

        nome = " ".join(args[:args.index(args[-1])]) if len(args) > 2 else args[0]
        descricao = args[-1] if len(args) > 1 else args[1]

        data = _load_data()
        event_id = str(len(data["events"]) + 1)

        data["events"][event_id] = {
            "name": nome,
            "description": descricao,
            "created_by": str(message.author.id),
            "created_at": datetime.now(UTC).isoformat(),
            "guild_id": str(message.guild.id),
            "channel_id": str(message.channel.id),
            "status": "draft",
            "scheduled_time": None,
            "duration": "1 hora",
            "reward": "100 moedas"
        }

        _save_data(data)
        await message.channel.send(embed=_embed("✅ Evento Criado", f"Evento '{nome}' criado! Use `tenshi schedule-event {event_id} [tempo]` para agendar.", COR_SUCESSO))

    async def handle_schedule_event(self, message, args):
        """Agenda um evento."""
        if not message.author.guild_permissions.administrator and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem agendar eventos.", COR_PERIGO))
            return

        if len(args) < 2:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi schedule-event [id] [minutos]`", COR_NEUTRO))
            return

        event_id = args[0]
        try:
            minutes = int(args[1])
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Minutos deve ser um número.", COR_PERIGO))
            return

        data = _load_data()
        if event_id not in data["events"]:
            await message.channel.send(embed=_embed("❌ Evento Não Encontrado", f"Evento {event_id} não existe.", COR_PERIGO))
            return

        scheduled_time = (datetime.now(UTC) + timedelta(minutes=minutes)).isoformat()
        data["events"][event_id]["scheduled_time"] = scheduled_time
        data["events"][event_id]["status"] = "scheduled"
        _save_data(data)

        await message.channel.send(embed=_embed("✅ Evento Agendado", f"Evento agendado para {minutes} minutos!", COR_SUCESSO))

    async def handle_list_events(self, message, args):
        """Lista todos os eventos."""
        data = _load_data()
        events = data["events"]

        if not events:
            await message.channel.send(embed=_embed("📋 Sem Eventos", "Não há eventos criados.", COR_NEUTRO))
            return

        linhas = []
        for event_id, event in events.items():
            status_emoji = "📅" if event["status"] == "scheduled" else "🎉" if event["status"] == "active" else "📝"
            linhas.append(f"{status_emoji} **{event['name']}** (ID: {event_id})")
            linhas.append(f"   Status: {event['status']}")
            if event["status"] == "scheduled":
                linhas.append(f"   Agendado para: {event['scheduled_time']}")
            linhas.append("")

        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("📋 Eventos", descricao, COR_DOURADO))

    async def handle_join_event(self, message, args):
        """Participa de um evento ativo."""
        data = _load_data()
        
        # Encontrar evento ativo
        active_event = None
        for event_id, event in data["events"].items():
            if event["status"] == "active":
                active_event = event_id
                break
        
        if not active_event:
            await message.channel.send(embed=_embed("❌ Sem Eventos Ativos", "Não há eventos acontecendo agora.", COR_NEUTRO))
            return

        user_id = str(message.author.id)
        if active_event not in data["participants"]:
            data["participants"][active_event] = []
        
        if user_id in data["participants"][active_event]:
            await message.channel.send(embed=_embed("❌ Já Participando", "Você já está participando deste evento!", COR_NEUTRO))
            return

        data["participants"][active_event].append(user_id)
        _save_data(data)

        await message.channel.send(embed=_embed("✅ Participando", f"Você entrou no evento!", COR_SUCESSO))

    async def handle_event_info(self, message, args):
        """Mostra informações de um evento."""
        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi event-info [id]`", COR_NEUTRO))
            return

        event_id = args[0]
        data = _load_data()

        if event_id not in data["events"]:
            await message.channel.send(embed=_embed("❌ Evento Não Encontrado", f"Evento {event_id} não existe.", COR_PERIGO))
            return

        event = data["events"][event_id]
        participants = len(data["participants"].get(event_id, []))

        descricao = (
            f"**Nome:** {event['name']}\n"
            f"**Descrição:** {event['description']}\n"
            f"**Status:** {event['status']}\n"
            f"**Participantes:** {participants}\n"
        )

        if event["status"] == "scheduled":
            descricao += f"**Agendado para:** {event['scheduled_time']}\n"

        await message.channel.send(embed=_embed(f"📋 Info: {event['name']}", descricao, COR_DOURADO))

    async def handle_end_event(self, message, args):
        """Finaliza um evento (admin)."""
        if not message.author.guild_permissions.administrator and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem finalizar eventos.", COR_PERIGO))
            return

        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi end-event [id]`", COR_NEUTRO))
            return

        event_id = args[0]
        data = _load_data()

        if event_id not in data["events"]:
            await message.channel.send(embed=_embed("❌ Evento Não Encontrado", f"Evento {event_id} não existe.", COR_PERIGO))
            return

        if data["events"][event_id]["status"] != "active":
            await message.channel.send(embed=_embed("❌ Evento Não Ativo", "Este evento não está ativo.", COR_PERIGO))
            return

        # Dar recompensas aos participantes
        participants = data["participants"].get(event_id, [])
        reward = int(data["events"][event_id].get("reward", "100").split()[0])

        for user_id in participants:
            user = get_user(int(user_id))
            user["moedas"] += reward
            save_user(int(user_id), user)

        # Atualizar status
        data["events"][event_id]["status"] = "completed"
        data["events"][event_id]["ended_at"] = datetime.now(UTC).isoformat()
        _save_data(data)

        await message.channel.send(embed=_embed(
            "🎉 Evento Finalizado",
            f"Evento finalizado! {len(participants)} participantes receberam {reward} moedas.",
            COR_SUCESSO
        ))

    async def handle_delete_event(self, message, args):
        """Deleta um evento (admin)."""
        if not message.author.guild_permissions.administrator and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem deletar eventos.", COR_PERIGO))
            return

        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi delete-event [id]`", COR_NEUTRO))
            return

        event_id = args[0]
        data = _load_data()

        if event_id not in data["events"]:
            await message.channel.send(embed=_embed("❌ Evento Não Encontrado", f"Evento {event_id} não existe.", COR_PERIGO))
            return

        del data["events"][event_id]
        if event_id in data["participants"]:
            del data["participants"][event_id]
        if event_id in data["active_events"]:
            del data["active_events"][event_id]

        _save_data(data)
        await message.channel.send(embed=_embed("✅ Evento Deletado", f"Evento {event_id} foi deletado.", COR_SUCESSO))
