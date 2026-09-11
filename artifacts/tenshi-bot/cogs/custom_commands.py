"""Custom Commands System - Allow users to create their own commands"""

import json
import os
from datetime import UTC, datetime
from typing import Optional

import discord
from discord.ext import commands
from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial

DATA_FILE = "data/custom_commands.json"
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


class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_criar_comando(self, message, args):
        """Cria um comando personalizado."""
        if not message.author.guild_permissions.manage_messages and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem criar comandos personalizados.", COR_PERIGO))
            return

        if len(args) < 2:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi criar-comando [nome] [resposta]`", COR_NEUTRO))
            return

        nome = args[0].lower()
        resposta = " ".join(args[1:])

        data = _load_data()
        guild_id = str(message.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id][nome] = {
            "response": resposta,
            "created_by": str(message.author.id),
            "created_at": datetime.now(UTC).isoformat(),
            "uses": 0
        }

        _save_data(data)
        await message.channel.send(embed=_embed("✅ Comando Criado", f"Comando `{nome}` criado com sucesso!\nUse: `tenshi {nome}`", COR_SUCESSO))

    async def handle_deletar_comando(self, message, args):
        """Deleta um comando personalizado."""
        if not message.author.guild_permissions.manage_messages and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem deletar comandos.", COR_PERIGO))
            return

        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi deletar-comando [nome]`", COR_NEUTRO))
            return

        nome = args[0].lower()
        data = _load_data()
        guild_id = str(message.guild.id)

        if guild_id not in data or nome not in data[guild_id]:
            await message.channel.send(embed=_embed("❌ Comando Não Encontrado", f"O comando `{nome}` não existe.", COR_PERIGO))
            return

        del data[guild_id][nome]

        if not data[guild_id]:
            del data[guild_id]

        _save_data(data)
        await message.channel.send(embed=_embed("✅ Comando Deletado", f"O comando `{nome}` foi deletado.", COR_SUCESSO))

    async def handle_listar_comandos(self, message, args):
        """Lista todos os comandos personalizados do servidor."""
        data = _load_data()
        guild_id = str(message.guild.id)

        if guild_id not in data or not data[guild_id]:
            await message.channel.send(embed=_embed("📋 Sem Comandos", "Este servidor não tem comandos personalizados.", COR_NEUTRO))
            return

        comandos = data[guild_id]
        linhas = []

        for nome, info in comandos.items():
            linhas.append(f"• **{nome}** - Usos: {info['uses']}")
            linhas.append(f"  `{info['response'][:50]}...`\n")

        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("📋 Comandos Personalizados", descricao, COR_DOURADO))

    async def handle_editar_comando(self, message, args):
        """Edita um comando personalizado."""
        if not message.author.guild_permissions.manage_messages and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem editar comandos.", COR_PERIGO))
            return

        if len(args) < 2:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi editar-comando [nome] [nova resposta]`", COR_NEUTRO))
            return

        nome = args[0].lower()
        nova_resposta = " ".join(args[1:])

        data = _load_data()
        guild_id = str(message.guild.id)

        if guild_id not in data or nome not in data[guild_id]:
            await message.channel.send(embed=_embed("❌ Comando Não Encontrado", f"O comando `{nome}` não existe.", COR_PERIGO))
            return

        data[guild_id][nome]["response"] = nova_resposta
        data[guild_id][nome]["edited_by"] = str(message.author.id)
        data[guild_id][nome]["edited_at"] = datetime.now(UTC).isoformat()

        _save_data(data)
        await message.channel.send(embed=_embed("✅ Comando Editado", f"O comando `{nome}` foi atualizado.", COR_SUCESSO))

    async def handle_info_comando(self, message, args):
        """Mostra informações de um comando personalizado."""
        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi info-comando [nome]`", COR_NEUTRO))
            return

        nome = args[0].lower()
        data = _load_data()
        guild_id = str(message.guild.id)

        if guild_id not in data or nome not in data[guild_id]:
            await message.channel.send(embed=_embed("❌ Comando Não Encontrado", f"O comando `{nome}` não existe.", COR_PERIGO))
            return

        info = data[guild_id][nome]
        created_by = await self.bot.fetch_user(int(info["created_by"]))
        edited_by = await self.bot.fetch_user(int(info["edited_by"])) if "edited_by" in info else None

        descricao = (
            f"**Nome:** {nome}\n"
            f"**Resposta:** {info['response']}\n"
            f"**Criado por:** {created_by.mention if created_by else 'Desconhecido'}\n"
            f"**Criado em:** {info['created_at']}\n"
            f"**Usos:** {info['uses']}\n"
        )

        if edited_by:
            descricao += f"**Editado por:** {edited_by.mention if edited_by else 'Desconhecido'}\n"
            descricao += f"**Editado em:** {info['edited_at']}\n"

        await message.channel.send(embed=_embed(f"📋 Info: {nome}", descricao, COR_DOURADO))

    async def execute_custom_command(self, message, cmd):
        """Executa um comando personalizado."""
        data = _load_data()
        guild_id = str(message.guild.id)

        if guild_id not in data or cmd not in data[guild_id]:
            return False

        comando = data[guild_id][cmd]
        resposta = comando["response"]

        # Substituir variáveis
        resposta = resposta.replace("{user}", message.author.mention)
        resposta = resposta.replace("{server}", message.guild.name)
        resposta = resposta.replace("{channel}", message.channel.mention)
        resposta = resposta.replace("{date}", datetime.now(UTC).strftime("%d/%m/%Y"))
        resposta = resposta.replace("{time}", datetime.now(UTC).strftime("%H:%M"))

        # Incrementar usos
        comando["uses"] += 1
        _save_data(data)

        await message.channel.send(resposta)
        return True
