import discord
import os

IMPERADOR_ID_STR = os.environ.get("IMPERADOR_ID", "0")
try:
    IMPERADOR_ID = int(IMPERADOR_ID_STR)
except ValueError:
    IMPERADOR_ID = 0

PREFIXO = "tenshi,"
COOLDOWN_TREINO = 30 * 60
COOLDOWN_MISSAO = 60 * 60

# Cores por pegada
CORES_PEGADA = {
    "imperial": 0x4B0082,
    "familia":  0x8B0000,
    "mafia":    0x1C1C1C,
    "enterprise": 0x1E3A5F,
}

# Emojis de status por pegada
EMOJI_PEGADA = {
    "imperial":   "🏛️",
    "familia":    "👨‍👩‍👧",
    "mafia":      "🔫",
    "enterprise": "🏢",
}

NOME_PEGADA = {
    "imperial":   "Império de Tenshi",
    "familia":    "Família",
    "mafia":      "Máfia",
    "enterprise": "Tenshi Enterprise",
}


def embed_imperial(titulo: str, descricao: str, cor: int = 0x4B0082) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text="🏛️ Império de Tenshi • Que a glória seja eterna")
    return embed


def embed_pegada(titulo: str, descricao: str, pegada: str = "imperial") -> discord.Embed:
    cor = CORES_PEGADA.get(pegada, 0x4B0082)
    emoji = EMOJI_PEGADA.get(pegada, "🏛️")
    nome = NOME_PEGADA.get(pegada, "Tenshi")
    embed = discord.Embed(title=f"{emoji} {titulo}", description=descricao, color=cor)
    embed.set_footer(text=f"{emoji} {nome}")
    return embed


def calcular_nivel(xp: int):
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
Prefixo: `Tenshi,`

**⚔️ RPG & Perfil**
`status` · `treinar` · `missao` · `interagir [ação] [@user]`
`ficha` · `pegada [imperial/familia/mafia/enterprise]`

**💰 Financeiro Imperial**
`carteira` · `banco` · `depositar [v]` · `sacar [v]`
`transferir @user [v]` · `emprestimo [v]` · `pagar-divida [v]`
`historico`

**🏠 Sistema de Casas**
`casas` · `minha-casa` · `vender-casa`

**🏢 Tenshi Enterprise (Gestão)**
`empresa criar [nome]` · `empresa info`
`empresa contratar @user [cargo] [salario]`
`empresa demitir @user` · `empresa funcionarios`
`empresa pagar` · `empresa depositar [v]`

**👨‍👩‍👧 Família & Máfia**
`familia criar [nome] [familia/mafia]`
`familia entrar [id]` · `familia info` · `familia membros`
`familia depositar [v]`

**⚔️ Facções**
`entrar [facção]` · `ranking`

**🔮 Místico**
`tarot` · `runa`

**⚔️ Duelos PvP**
`duelo @user [aposta]` · `aceitar-duelo`

**🛒 Loja**
`loja` · `comprar [id]`

**📖 LoreMaster (IA)**
`cronica [militar/politico/esoterico]` · `evento-lore`

**🛡️ Moderação**
`ban` · `kick` · `mute` · `clear [n]` · `decreto [msg]`

**👑 Especiais**
`invasao` (ADM) · `ping` · `ajuda`
"""
