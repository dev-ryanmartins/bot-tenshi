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


SITE_URL = "https://c5d65469-a79e-48a4-aa38-def706fcc844-00-3g7sob5uug1rk.janeway.replit.dev"

AJUDA_TEXTO = f"""
{SEP}
**🏛️ PERGAMINHOS IMPERIAIS DE TENSHI**
*Prefixo: `Tenshi,`  •  RP de texto narrativo  •  7 Motores de IA*
🌐 **Site oficial:** {SITE_URL}
{SEP}

**🎭 Identidade & Perfil**
`status` `ficha` `criar-ficha` `pegada [tema]` `inventario` `conquistas` `especies` `viajar [local]` `local`

**✨ Poderes de RP**
`poderes` `meus-poderes`

**⚡ Jornada Imperial**
`treinar [ação]` `missao` `meditar` `descansar` `interagir [ação]` `dado [d4/d6/d10/d20/d100]`
`trabalhar` `emprego` `profissao [classe]` `clima`

**📖 LoreMaster IA** *(Gerado por IA)*
`cronica [militar/politico/esoterico/mafia/enterprise]`
`evento-lore` `oraculo [pergunta]` `falar [NPC]` `lore-historico` `quadro-avisos`

**🔮 Místico**
`tarot` `runa` `astros` `destino @user` `sacrificio [item]` `ritual-protecao`

**⚔️ Combate Narrativo**
`duelo @user` `aceitar-duelo` `basquete @user` `futebol @user` `dado [tipo]`
`invocar-chefe [criatura]` *(admin)* `invasao` *(admin)*

**💰 Economia & Comércio**
`carteira` `mercado` `mercado-negro` `comprar [item]` `leilao [item]` `sorteio-real` `trabalhar` `emprego`

**🏦 Banco & Finanças**
`banco` `depositar [v]` `sacar [v]` `transferir @user [v]` `emprestimo [v]` `pagar-divida` `historico`
`poupanca [v]` `comprar-acoes [v]` `seguro-vida` `aposentar`

**🏠 Propriedades & Condomínio**
`casas` `minha-casa` `vender-casa` `portaria` `residencia` `convidar @user` `expulsar @user`
`devolver-casa` `moradores` `relaxar` `fofoca` `trancar-casa` `destrancar-casa`

**🚗 Garagem, Esportes & Pets**
`garagem` `vender-veiculo` `abastecer [v]` `basquete @user` `futebol @user`
`pet-shop` `meu-pet` `vender-pet` `pool-party` *(admin)*

**💑 Social & Cotidiano**
`casar @user` `divorcio` `lavanderia` `sintetizar [item]` `cartaz [filme]`
`psicologo [texto]` `beber [bebida]` `jornal-cotidiano` `correio` `estacoes`
`entrevista [cargo]` `socorrer @user` `vdd`

**🕵️ Crime & Inteligência**
`assaltar @user` `mercado-negro-beco` `subornar-porteiro @user`
`grampear-call` `iniciar-festa [local]` `registrar-perola [msg]`

**⚖️ Jurídico & Clero**
`ficha-criminal @user` `warn @user` `perdoar-aviso @user` `mandado @user`
`pagar-fianca` `imunidade-diplomatica` `padre [rito]` `sindicancia @user`
`laudo-medico` `desintoxicacao` `doacao-sangue` `diagnostico-ia`

**🌍 Geopolítica & Estado**
`dominar [canal]` `territorio` `rebeliao` `visto` `cidadania` `exilio @user`
`auditoria-bancaria` `necrolo` `aposentar` `buscar-protocolo`
`set-era [nome]` `era` `decreto-marcial [ação]` `aconselhar-estrategia [sit.]`

**🏗️ Infraestrutura Crítica**
`status-energia` `inflacao` `comprar-acoes [v]` `poupanca [v]`
`checar-cameras` `biometria` `rastrear-perfil @user` `enviar-carga [tipo]`
`titulo-propriedade` `alugar-comercio`

**🎓 Tenshi Academy**
`matricular [mat.]` `trancar-matricula [mat.]` `presenca [mat.]` `iniciar-aula [mat.]`
`ler-apostila [mat.]` `prestar-exame [mat.]` `historico-escolar` `segunda-via-diploma`
`entrar-clube [nome]` `cofre-clube`

**🏢 Empresa**
`empresa criar/info/contratar/demitir/funcionarios/pagar`

**👨‍👩‍👧 Família, Máfia & Facções**
`familia criar/entrar/info/membros/missao/depositar` `entrar [facção]` `ranking`

**🛡️ Moderação Imperial** *(Admin)*
`decreto [msg]` `promover @user [cargo]` `punir-audacia @user` `julgamento @user`
`masmorra-prender @user [min]` `exilar @user` `anistia-real` `trancar-portoes`
`tesouro [v]` `veto [ação]` `ban` `kick` `mute [min]` `clear [n]` `warn @user`

**👑 Prerrogativas Soberanas** *(Imperador)*
`emitir-moeda` `confiscar-fortuna` `congelar-banco` `perdoar-divida` `isencao-fiscal`
`set-status @user` `apagar-ficha` `conceder-item` `imortalidade`
`estado-de-sitio` `dissolver-mafia` `anistia-geral` `exilio-supremo`
`atualizar-diretriz` `apagar-memoria-ia` `forcar-cronica` `censo-imperial`
`reset-era` `irradiar [msg]` `congelar-economia` `exportar-banco` `desligar`

**🔧 Utilitários**
`top` `servidor` `ping` `backup` `status-ia` `aniversario` `ajuda`
{SEP}
*🌐 Guia completo: {SITE_URL}*
*{RODAPE_IMPERIAL}*
"""
