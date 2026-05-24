import discord
import os

# ── Imperador ─────────────────────────────────────────────────────────────────
IMPERADOR_ID = 619302798751694849

PREFIXO = "tenshi,"
COOLDOWN_TREINO = 30 * 60
COOLDOWN_MISSAO = 60 * 60

# ── Paletas por pegada ────────────────────────────────────────────────────────
CORES_PEGADA = {
    "imperial":   0x2B0A3D,   # roxo profundo
    "familia":    0x6B0000,   # vinho escuro
    "mafia":      0x0D0D0D,   # preto absoluto
    "enterprise": 0x0A1628,   # azul marinho
}

CORES_DESTAQUE = {
    "imperial":   0x8A2BE2,   # violeta brilhante
    "familia":    0xC0392B,   # vermelho
    "mafia":      0x2C2C2C,   # cinza escuro
    "enterprise": 0x1B4F72,   # azul aço
}

EMOJI_PEGADA = {
    "imperial":   "🏛️",
    "familia":    "👨‍👩‍👧",
    "mafia":      "🖤",
    "enterprise": "🏢",
}

NOME_PEGADA = {
    "imperial":   "Império de Tenshi",
    "familia":    "Família",
    "mafia":      "Máfia",
    "enterprise": "Tenshi Enterprise",
}

# ── Separadores decorativos ───────────────────────────────────────────────────
SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SEP_LIGHT = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
RODAPE_IMPERIAL = "⚜️ Desenvolvido por Alloy Tenshi, O Imperador"


def embed_imperial(titulo: str, descricao: str, cor: int = 0x2B0A3D) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


def embed_pegada(titulo: str, descricao: str, pegada: str = "imperial") -> discord.Embed:
    cor = CORES_PEGADA.get(pegada, 0x2B0A3D)
    emoji = EMOJI_PEGADA.get(pegada, "🏛️")
    nome = NOME_PEGADA.get(pegada, "Tenshi")
    embed = discord.Embed(title=f"{emoji} {titulo}", description=descricao, color=cor)
    embed.set_footer(text=f"{emoji} {nome}  •  {RODAPE_IMPERIAL}")
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


def barra_progresso(atual: int, maximo: int, tamanho: int = 12) -> str:
    if maximo == 0:
        return "░" * tamanho
    preenchido = int((atual / maximo) * tamanho)
    return "█" * preenchido + "░" * (tamanho - preenchido)


AJUDA_TEXTO = f"""
{SEP}
**🏛️ PERGAMINHOS IMPERIAIS DE TENSHI**
*Prefixo: `Tenshi,`  •  RP de texto narrativo*
{SEP}

**🎭 Identidade & Perfil**
`status` `ficha` `pegada [tema]` `inventario` `conquistas`

**⚡ Jornada Imperial**
`treinar [ação narrativa]` `missao` `meditar` `descansar`
`oraculo [pergunta]` `clima`

**💰 Economia & Comércio**
`carteira` `banco` `depositar` `sacar` `transferir @user`
`mercado` `mercado-negro` `trabalhar` `leilao [item]`
`emprestimo` `pagar-divida` `historico`

**🏠 Propriedades & Condomínio**
`casas` `minha-casa` `vender-casa`
`portaria` `residencia` `convidar @user` `expulsar @user`
`devolver-casa` `moradores` `relaxar` `fofoca`

**🏢 Tenshi Enterprise**
`empresa criar/info/contratar/demitir/funcionarios/pagar`

**👨‍👩‍👧 Família & Máfia**
`familia criar/entrar/info/membros/missao/depositar`

**⚔️ Facções**
`entrar [facção]` `ranking`

**🔮 Místico**
`tarot` `runa` `astros` `destino @user` `sacrificio`

**⚔️ Combate Narrativo**
`duelo @user` `aceitar-duelo` `invocar-chefe [criatura]`
`apostar [v] @user` `dado [d6/d20]`

**📖 LoreMaster IA**
`cronica [militar/politico/esoterico/mafia/enterprise]`
`evento-lore` `falar [NPC]` `lore-historico`

**🛡️ Moderação Imperial**
`julgamento @user` `masmorra-prender @user [tempo]`
`exilar @user` `anistia-real` `decreto [msg]`
`promover @user [cargo]` `punir-audacia @user`
`clear [n]` `ban` `kick` `mute`

**🔧 Utilitários**
`top` `servidor` `ping` `backup` `ajuda`
{SEP}
*{RODAPE_IMPERIAL}*
"""
