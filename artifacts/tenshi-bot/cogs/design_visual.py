"""Módulo de Design Visual Imperial - Estética Inspirada em Bots Famosos"""

import discord
from datetime import datetime
from typing import Optional, List

# Paleta de Cores Imperial (inspirada em bots premium)
class CoresImperial:
    """Paleta de cores premium para embeds"""
    DOURADO = 0xFFD700
    DOURADO_ESCURO = 0xB8860B
    DOURADO_CLARO = 0xFFEC8B
    
    SUCESSO = 0x00FF7F
    SUCESSO_ESCURO = 0x006400
    
    PERIGO = 0xFF4500
    PERIGO_ESCURO = 0x8B0000
    
    INFO = 0x1E90FF
    INFO_ESCURO = 0x00008B
    
    ROXO = 0x9B59B6
    ROSA = 0xE91E63
    
    CINZA = 0x2C3E50
    CINZA_CLARO = 0x95A5A6
    
    NEUTRO = 0x607D8B


# Emojis Decorativos por Categoria
class EmojisImperial:
    """Emojis temáticos para cada categoria"""
    USUARIO = "👤"
    ECONOMIA = "💰"
    RPG = "⚔️"
    MODERACAO = "🛡️"
    FAMILIA = "👨‍👩‍👧"
    PERFIL = "🎭"
    EVENTOS = "🎪"
    MUSICA = "🎵"
    JOGOS = "🎮"
    ESTATISTICAS = "📊"
    
    SUCESSO = "✅"
    ERRO = "❌"
    AVISO = "⚠️"
    INFO = "ℹ️"
    ESTRELA = "⭐"
    COROA = "👑"
    FOGO = "🔥"
    BRILHO = "✨"
    SETA = "➡️"
    CHECK = "☑️"


def criar_embed_moderno(
    titulo: str,
    descricao: str,
    cor: int = CoresImperial.DOURADO,
    emoji_titulo: str = "",
    thumbnail_url: Optional[str] = None,
    image_url: Optional[str] = None,
    autor: Optional[str] = None,
    autor_icon: Optional[str] = None,
    campos: Optional[List[tuple]] = None,
    footer_text: Optional[str] = None
) -> discord.Embed:
    """
    Cria embed moderno inspirado em bots premium como MEE6 e Dyno.
    
    Args:
        titulo: Título do embed
        descricao: Descrição principal
        cor: Cor do embed (padrão: dourado)
        emoji_titulo: Emoji para prefixar no título
        thumbnail_url: URL da imagem thumbnail
        image_url: URL da imagem principal
        autor: Nome do autor
        autor_icon: URL do ícone do autor
        campos: Lista de tuplas (nome, valor, inline)
        footer_text: Texto do rodapé
    """
    embed = discord.Embed(
        title=f"{emoji_titulo} {titulo}" if emoji_titulo else titulo,
        description=descricao,
        color=cor,
        timestamp=datetime.utcnow()
    )
    
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    
    if image_url:
        embed.set_image(url=image_url)
    
    if autor:
        embed.set_author(name=autor, icon_url=autor_icon)
    
    if campos:
        for nome, valor, inline in campos:
            embed.add_field(name=nome, value=valor, inline=inline)
    
    if footer_text:
        embed.set_footer(text=footer_text)
    
    return embed


def criar_embed_com_barras(
    titulo: str,
    descricao: str,
    barras: List[tuple],
    cor: int = CoresImperial.DOURADO,
    emoji_titulo: str = ""
) -> discord.Embed:
    """
    Cria embed com barras de progresso visuais.
    
    Args:
        titulo: Título do embed
        descricao: Descrição principal
        barras: Lista de tuplas (nome, valor_atual, valor_maximo, emoji)
        cor: Cor do embed
        emoji_titulo: Emoji do título
    """
    campos_barras = []
    
    for nome, atual, maximo, emoji in barras:
        if maximo > 0:
            porcentagem = min(100, (atual / maximo) * 100)
            barra_cheia = "█"
            barra_vazia = "░"
            tamanho_barra = 20
            preenchido = int(tamanho_barra * (porcentagem / 100))
            
            barra_visual = (barra_cheia * preenchido + barra_vazia * (tamanho_barra - preenchido))
            campos_barras.append(
                (f"{emoji} {nome}", f"{barra_visual} **{atual}/{maximo}** ({porcentagem:.1f}%)", False)
            )
    
    return criar_embed_moderno(
        titulo=titulo,
        descricao=descricao,
        cor=cor,
        emoji_titulo=emoji_titulo,
        campos=campos_barras
    )


def criar_embed_categoria(
    categoria: str,
    titulo: str,
    descricao: str,
    thumbnail_url: Optional[str] = None
) -> discord.Embed:
    """
    Cria embed temático por categoria com cores específicas.
    """
    categorias = {
        "usuarios": (CoresImperial.ROXO, EmojisImperial.USUARIO),
        "economia": (CoresImperial.SUCESSO, EmojisImperial.ECONOMIA),
        "rpg": (CoresImperial.PERIGO, EmojisImperial.RPG),
        "moderacao": (CoresImperial.PERIGO_ESCURO, EmojisImperial.MODERACAO),
        "familia": (CoresImperial.ROSA, EmojisImperial.FAMILIA),
        "perfil": (CoresImperial.ROXO, EmojisImperial.PERFIL),
        "eventos": (CoresImperial.SUCESSO_ESCURO, EmojisImperial.EVENTOS),
        "musica": (CoresImperial.INFO, EmojisImperial.MUSICA),
        "jogos": (CoresImperial.INFO_ESCURO, EmojisImperial.JOGOS),
        "estatisticas": (CoresImperial.CINZA_CLARO, EmojisImperial.ESTATISTICAS),
    }
    
    cor, emoji = categorias.get(categoria.lower(), (CoresImperial.DOURADO, EmojisImperial.ESTRELA))
    
    return criar_embed_moderno(
        titulo=titulo,
        descricao=descricao,
        cor=cor,
        emoji_titulo=emoji,
        thumbnail_url=thumbnail_url
    )


def criar_embed_sucesso(titulo: str, descricao: str) -> discord.Embed:
    """Cria embed de sucesso com cor verde."""
    return criar_embed_moderno(
        titulo=titulo,
        descricao=descricao,
        cor=CoresImperial.SUCESSO,
        emoji_titulo=EmojisImperial.SUCESSO
    )


def criar_embed_erro(titulo: str, descricao: str) -> discord.Embed:
    """Cria embed de erro com cor vermelha."""
    return criar_embed_moderno(
        titulo=titulo,
        descricao=descricao,
        cor=CoresImperial.PERIGO,
        emoji_titulo=EmojisImperial.ERRO
    )


def criar_embed_aviso(titulo: str, descricao: str) -> discord.Embed:
    """Cria embed de aviso com cor amarela."""
    return criar_embed_moderno(
        titulo=titulo,
        descricao=descricao,
        cor=CoresImperial.DOURADO,
        emoji_titulo=EmojisImperial.AVISO
    )


def criar_embed_info(titulo: str, descricao: str) -> discord.Embed:
    """Cria embed informativo com cor azul."""
    return criar_embed_moderno(
        titulo=titulo,
        descricao=descricao,
        cor=CoresImperial.INFO,
        emoji_titulo=EmojisImperial.INFO
    )


def formatar_numero_grande(numero: int) -> str:
    """Formata números grandes com sufixos (K, M, B)."""
    if numero >= 1_000_000_000:
        return f"{numero / 1_000_000_000:.2f}B"
    elif numero >= 1_000_000:
        return f"{numero / 1_000_000:.2f}M"
    elif numero >= 1_000:
        return f"{numero / 1_000:.2f}K"
    return str(numero)


def criar_lista_decorativa(itens: List[str], emoji: str = "•") -> str:
    """Cria lista visual com emojis."""
    return "\n".join(f"{emoji} {item}" for item in itens)


def criar_separador(titulo: str = "", estilo: str = "═") -> str:
    """Cria separador visual."""
    if titulo:
        return f"\n{estilo * 10} {titulo} {estilo * 10}\n"
    return f"\n{estilo * 25}\n"
