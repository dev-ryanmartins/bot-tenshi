"""Level-Up Rewards System - Rewards for leveling up"""

import json
import os
from datetime import UTC, datetime
from typing import Optional

import discord
from discord.ext import commands
from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial

DATA_FILE = "data/level_rewards.json"
COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


def _load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return _create_default_rewards()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return _create_default_rewards()


def _save_data(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _create_default_rewards() -> dict:
    return {
        "rewards": {
            "5": {
                "moedas": 100,
                "titulo": "Iniciante",
                "items": []
            },
            "10": {
                "moedas": 250,
                "titulo": "Aprendiz",
                "items": ["espada_basica"]
            },
            "15": {
                "moedas": 500,
                "titulo": "Veterano",
                "items": ["armadura_leve"]
            },
            "20": {
                "moedas": 1000,
                "titulo": "Elite",
                "items": ["espada_afiada", "poção_vida"]
            },
            "25": {
                "moedas": 2000,
                "titulo": "Mestre",
                "items": ["armadura_pesada", "poção_mana"]
            },
            "30": {
                "moedas": 5000,
                "titulo": "Lendário",
                "items": ["espada_lendaria", "escudo_divino"]
            },
            "40": {
                "moedas": 10000,
                "titulo": "Imperial",
                "items": ["coroa_imperial", "manto_real"]
            },
            "50": {
                "moedas": 25000,
                "titulo": "Soberano",
                "items": ["cetro_poder", "anel_magico"]
            }
        },
        "claimed": {}
    }


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


class LevelRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_rewards(self, message, args):
        """Mostra todas as recompensas disponíveis."""
        data = _load_data()
        rewards = data["rewards"]
        
        linhas = []
        for level, reward in sorted(rewards.items(), key=lambda x: int(x[0])):
            items_str = ", ".join(reward["items"]) if reward["items"] else "Nenhum"
            linhas.append(f"**Nível {level}** - {reward['titulo']}")
            linhas.append(f"   💰 {reward['moedas']} moedas")
            linhas.append(f"   🎁 {items_str}\n")
        
        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("🏆 Recompensas por Nível", descricao, COR_DOURADO))

    async def handle_claim_reward(self, message, args):
        """Reivindica recompensa de nível."""
        user = get_user(message.author.id)
        current_level = user.get("nivel", 1)
        
        data = _load_data()
        user_id = str(message.author.id)
        
        if user_id not in data["claimed"]:
            data["claimed"][user_id] = []
        
        claimed = data["claimed"][user_id]
        
        # Encontrar próxima recompensa não reivindicada
        for level_str, reward in data["rewards"].items():
            level = int(level_str)
            if level <= current_level and level_str not in claimed:
                # Dar recompensa
                user["moedas"] += reward["moedas"]
                
                # Adicionar itens ao inventário
                if "inventario" not in user:
                    user["inventario"] = []
                user["inventario"].extend(reward["items"])
                
                # Dar título
                if reward["titulo"]:
                    user["titulo"] = reward["titulo"]
                
                claimed.append(level_str)
                _save_data(data)
                save_user(message.author.id, user)
                
                items_str = ", ".join(reward["items"]) if reward["items"] else "Nenhum"
                await message.channel.send(embed=_embed(
                    f"🎉 Recompensa do Nível {level}!",
                    f"Você recebeu:\n"
                    f"💰 {reward['moedas']} moedas\n"
                    f"🎁 {items_str}\n"
                    f"👑 Título: {reward['titulo']}",
                    COR_SUCESSO
                ))
                return
        
        await message.channel.send(embed=_embed("❌ Sem Recompensas", "Você não tem recompensas pendentes para reivindicar.", COR_NEUTRO))

    async def handle_my_rewards(self, message, args):
        """Mostra recompensas reivindicadas e pendentes."""
        user = get_user(message.author.id)
        current_level = user.get("nivel", 1)
        
        data = _load_data()
        user_id = str(message.author.id)
        
        claimed = data["claimed"].get(user_id, [])
        
        linhas = []
        linhas.append(f"**Nível Atual:** {current_level}\n")
        
        # Recompensas pendentes
        pending = []
        for level_str, reward in data["rewards"].items():
            level = int(level_str)
            if level <= current_level and level_str not in claimed:
                pending.append(f"• Nível {level} - {reward['titulo']}")
        
        if pending:
            linhas.append("📦 **Recompensas Pendentes:**")
            linhas.extend(pending)
            linhas.append("\nUse `tenshi claim-reward` para reivindicar!")
        else:
            linhas.append("✅ **Todas as recompensas reivindicadas!**")
        
        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("🎁 Minhas Recompensas", descricao, COR_DOURADO))

    async def handle_add_reward(self, message, args):
        """Adiciona uma nova recompensa (admin)."""
        if not message.author.guild_permissions.administrator and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem adicionar recompensas.", COR_PERIGO))
            return

        if len(args) < 3:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi add-reward [nível] [moedas] [título]`", COR_NEUTRO))
            return

        try:
            level = args[0]
            moedas = int(args[1])
            titulo = " ".join(args[2:])
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Moedas deve ser um número.", COR_PERIGO))
            return

        data = _load_data()
        data["rewards"][level] = {
            "moedas": moedas,
            "titulo": titulo,
            "items": []
        }
        _save_data(data)

        await message.channel.send(embed=_embed("✅ Recompensa Adicionada", f"Recompensa para nível {level} criada!", COR_SUCESSO))

    async def handle_add_reward_item(self, message, args):
        """Adiciona item a uma recompensa (admin)."""
        if not message.author.guild_permissions.administrator and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem modificar recompensas.", COR_PERIGO))
            return

        if len(args) < 2:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi add-reward-item [nível] [item]`", COR_NEUTRO))
            return

        level = args[0]
        item = " ".join(args[1:])

        data = _load_data()
        if level not in data["rewards"]:
            await message.channel.send(embed=_embed("❌ Erro", f"Recompensa do nível {level} não existe.", COR_PERIGO))
            return

        data["rewards"][level]["items"].append(item)
        _save_data(data)

        await message.channel.send(embed=_embed("✅ Item Adicionado", f"Item '{item}' adicionado à recompensa do nível {level}.", COR_SUCESSO))

    async def handle_reset_rewards(self, message, args):
        """Reseta recompensas reivindicadas de um usuário (admin)."""
        if not message.author.guild_permissions.administrator and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem resetar recompensas.", COR_PERIGO))
            return

        if not message.mentions:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi reset-rewards @usuario`", COR_NEUTRO))
            return

        target = message.mentions[0]
        user_id = str(target.id)

        data = _load_data()
        if user_id in data["claimed"]:
            del data["claimed"][user_id]
            _save_data(data)
            await message.channel.send(embed=_embed("✅ Resetado", f"Recompensas de {target.mention} foram resetadas.", COR_SUCESSO))
        else:
            await message.channel.send(embed=_embed("❌ Erro", "Este usuário não tem recompensas registradas.", COR_NEUTRO))
