"""Sistema de Embeds e Tópicos para Chats Gerais"""

import json
import os
from datetime import UTC, datetime

import discord
from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial

DATA_FILE = "data/embed_topics.json"
COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F


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


TOPICOS_PREDEFINIDOS = {
    "boas-vindas": {
        "titulo": "🏛️ Bem-vindo ao Império de Tenshi",
        "descricao": (
            "Saudações, cidadão! Você entrou no Império de Tenshi, um reino de RPG, "
            "aventuras e conquistas.\n\n"
            "**Comece aqui:**\n"
            "• `tenshi ajuda` - Ver todos os comandos\n"
            "• `tenshi criar-ficha` - Criar seu personagem\n"
            "• `tenshi status` - Ver seu perfil\n\n"
            "**Canais importantes:**\n"
            "• #geral - Conversas e RP\n"
            "• #comandos - Use comandos do bot\n"
            "• #regras - Regras do servidor"
        ),
        "cor": COR_DOURADO
    },
    "regras-basicas": {
        "titulo": "⚖️ Regras do Império",
        "descricao": (
            "**1. Respeito**\n"
            "Trate todos com respeito e dignidade.\n\n"
            "**2. No RP**\n"
            "Mantenha o RP nos canais apropriados.\n\n"
            "**3. Sem spam**\n"
            "Evite flood e mensagens repetitivas.\n\n"
            "**4. Obedeça à staff**\n"
            "Siga as instruções dos administradores."
        ),
        "cor": COR_PERIGO
    },
    "eventos-atuais": {
        "titulo": "📅 Eventos em Andamento",
        "descricao": (
            "**Eventos Ativos:**\n"
            "• Nenhum evento no momento\n\n"
            "Fique atento aos anúncios para novos eventos!"
        ),
        "cor": COR_SUCESSO
    },
    "ranking-imperial": {
        "titulo": "🏆 Ranking Imperial",
        "descricao": (
            "**Top Cidadãos por Nível:**\n"
            "1. @Imperador - Nível ∞\n"
            "2. @Consorte - Nível 50\n"
            "3. @Guardião - Nível 45\n\n"
            "Suba no ranking usando `tenshi treinar`!"
        ),
        "cor": COR_DOURADO
    }
}


class EmbedTopics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_ativar_embed(self, message, args):
        """Ativa um embed de tópico no canal atual."""
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem ativar embeds.", COR_PERIGO))
            return

        if not args:
            # Listar tópicos disponíveis
            topicos = "\n".join(f"• `{nome}` - {info['titulo']}" for nome, info in TOPICOS_PREDEFINIDOS.items())
            descricao = f"**Tópicos disponíveis:**\n\n{topicos}\n\nUse: `tenshi ativar-embed [nome-do-topico]`"
            await message.channel.send(embed=_embed("📋 Tópicos Disponíveis", descricao, COR_DOURADO))
            return

        topico_nome = args[0].lower()
        if topico_nome not in TOPICOS_PREDEFINIDOS:
            await message.channel.send(embed=_embed("❌ Tópico Inválido", f"Tópico '{topico_nome}' não encontrado.", COR_PERIGO))
            return

        topico = TOPICOS_PREDEFINIDOS[topico_nome]
        embed = discord.Embed(title=topico["titulo"], description=topico["descricao"], color=topico["cor"])
        embed.set_footer(text=RODAPE_IMPERIAL)

        # Salvar configuração do canal
        data = _load_data()
        data[str(message.channel.id)] = {
            "topico": topico_nome,
            "ativado_por": str(message.author.id),
            "ativado_em": datetime.now(UTC).isoformat()
        }
        _save_data(data)

        await message.channel.send(embed=embed)
        await message.channel.send(embed=_embed("✅ Embed Ativado", f"Tópico '{topico_nome}' ativado neste canal.", COR_SUCESSO))

    async def handle_desativar_embed(self, message, args):
        """Desativa o embed do canal atual."""
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem desativar embeds.", COR_PERIGO))
            return

        data = _load_data()
        if str(message.channel.id) not in data:
            await message.channel.send(embed=_embed("❌ Nenhum Embed", "Este canal não tem um embed ativo.", COR_NEUTRO))
            return

        del data[str(message.channel.id)]
        _save_data(data)

        await message.channel.send(embed=_embed("✅ Embed Desativado", "O embed foi removido deste canal.", COR_SUCESSO))

    async def handle_criar_topico(self, message, args):
        """Cria um tópico personalizado."""
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem criar tópicos.", COR_PERIGO))
            return

        if len(args) < 2:
            await message.channel.send(embed=_embed("❌ Uso Incorreto", "Use: `tenshi criar-topico [nome] [título] [descrição]`", COR_NEUTRO))
            return

        nome = args[0].lower()
        titulo = " ".join(args[1:-1]) if len(args) > 2 else args[1]
        descricao = args[-1] if len(args) > 2 else "Sem descrição"

        data = _load_data()
        data["custom_" + nome] = {
            "titulo": titulo,
            "descricao": descricao,
            "cor": COR_DOURADO,
            "custom": True
        }
        _save_data(data)

        await message.channel.send(embed=_embed("✅ Tópico Criado", f"Tópico personalizado '{nome}' criado com sucesso.", COR_SUCESSO))

    async def handle_listar_topics(self, message, args):
        """Lista todos os tópicos disponíveis."""
        data = _load_data()
        topicos_predefinidos = "\n".join(f"• `{nome}` - {info['titulo']}" for nome, info in TOPICOS_PREDEFINIDOS.items())
        
        topicos_custom = ""
        for key, info in data.items():
            if key.startswith("custom_"):
                nome = key.replace("custom_", "")
                topicos_custom += f"• `{nome}` - {info['titulo']} (custom)\n"

        descricao = f"**Tópicos Predefinidos:**\n\n{topicos_predefinidos}\n\n"
        if topicos_custom:
            descricao += f"**Tópicos Personalizados:**\n\n{topicos_custom}\n\n"
        descricao += "Use: `tenshi ativar-embed [nome-do-topico]`"

        await message.channel.send(embed=_embed("📋 Todos os Tópicos", descricao, COR_DOURADO))

    async def on_ready(self):
        """Envia embeds para canais configurados ao iniciar."""
        await self.bot.wait_until_ready()
        data = _load_data()
        
        for channel_id, config in data.items():
            if channel_id.startswith("custom_"):
                continue  # Pular tópicos custom, são apenas definições
            
            try:
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    continue
                
                topico_nome = config["topico"]
                if topico_nome in TOPICOS_PREDEFINIDOS:
                    topico = TOPICOS_PREDEFINIDOS[topico_nome]
                    embed = discord.Embed(title=topico["titulo"], description=topico["descricao"], color=topico["cor"])
                    embed.set_footer(text=RODAPE_IMPERIAL)
                    
                    # Verificar se já existe embed recente
                    async for msg in channel.history(limit=10):
                        if msg.author == self.bot.user and msg.embeds:
                            break
                    else:
                        await channel.send(embed=embed)
            except Exception as e:
                print(f"[AVISO] Não foi possível enviar embed para canal {channel_id}: {e}")
