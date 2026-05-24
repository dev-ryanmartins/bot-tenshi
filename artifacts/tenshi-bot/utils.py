import discord
import os

# ID do Imperador Alloy — será lido do ambiente ou pode ser definido aqui
# Coloque o ID do Discord do dono do servidor nas secrets como IMPERADOR_ID
IMPERADOR_ID_STR = os.environ.get("IMPERADOR_ID", "0")
try:
    IMPERADOR_ID = int(IMPERADOR_ID_STR)
except ValueError:
    IMPERADOR_ID = 0

# Prefixo personalizado do bot
PREFIXO = "tenshi,"

# Cooldowns em segundos
COOLDOWN_TREINO = 30 * 60    # 30 minutos
COOLDOWN_MISSAO = 60 * 60    # 1 hora


def embed_imperial(titulo: str, descricao: str, cor: int = 0x4B0082) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text="🏛️ Império de Tenshi • Que a glória seja eterna")
    return embed


def calcular_nivel(xp: int) -> tuple[int, int]:
    nivel = 1
    xp_necessario = 100
    xp_restante = xp
    while xp_restante >= xp_necessario:
        xp_restante -= xp_necessario
        nivel += 1
        xp_necessario = int(xp_necessario * 1.5)
    return nivel, xp_necessario - xp_restante


AJUDA_TEXTO = """
**🏛️ COMANDOS DO IMPÉRIO DE TENSHI**

Use o prefixo `Tenshi,` antes de qualquer comando.

**⚔️ RPG & Perfil**
• `Tenshi, status` — Ver seu perfil imperial
• `Tenshi, treinar` — Treinar e ganhar poder (cooldown: 30min)
• `Tenshi, missao` — Aceitar uma missão imperial
• `Tenshi, interagir [ação] [@usuario]` — Interações de roleplay (saudar, proclamar, reverenciar)

**💰 Economia Imperial**
• `Tenshi, carteira` — Ver suas moedas imperiais
• `Tenshi, loja` — Ver o mercado imperial
• `Tenshi, comprar [id]` — Comprar um item da loja

**⚔️ Facções**
• `Tenshi, entrar [facção]` — Entrar em uma facção
• `Tenshi, ranking` — Ranking das facções rivais

**🔮 Místico**
• `Tenshi, tarot` — Carta de tarot diária (a cada 20h)
• `Tenshi, runa` — Runa ancestral diária (a cada 20h)

**⚔️ Duelos PvP**
• `Tenshi, duelo @usuario [aposta]` — Desafiar alguém
• `Tenshi, aceitar-duelo` — Aceitar um desafio

**📖 LoreMaster (IA)**
• `Tenshi, cronica [militar/politico/esoterico]` — Narrativa de RPG com IA
• `Tenshi, evento-lore` — Profecia imperial (ADM)

**🛡️ Moderação (requer permissões)**
• `Tenshi, ban @usuario [motivo]` — Banir
• `Tenshi, kick @usuario [motivo]` — Expulsar
• `Tenshi, mute @usuario` — Silenciar
• `Tenshi, clear [quantidade]` — Limpar mensagens

**👑 Imperador Alloy**
• `Tenshi, decreto [mensagem]` — Emitir um decreto imperial

*Digite `Tenshi, ajuda` para ver esta mensagem.*
"""
