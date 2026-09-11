"""
Verificador de Violações — Detecta comportamentos que violam as regras imperiais.
Integra-se ao assistente de IA para filtrar mensagens automaticamente.
"""

import re
from typing import Optional, Tuple

# Padrões de violação
SPAM_PATTERNS = [
    r"(.)\1{8,}",  # Caractere repetido 9+ vezes
]

PROFANITY_WORDS = [
    "fuck", "shit", "asshole", "bitch", "damn", "crap",
    # Adicione palavras ofensivas conforme necessário
]

# Padrões de conteúdo prejudicial/violento
HARMFUL_PATTERNS = [
    r"(?i)(suicid|auto harm|self harm|kill yourself|kys)",
    r"(?i)(hate|racist|sexist|discriminat)",  # Discurso de ódio
    r"(?i)(exploit|hack|cheat|cracking)",  # Atividades ilícitas
]

# Emojis suspeitos (usados para spam)
SPAM_EMOJIS_THRESHOLD = 10  # Se mais de 10 emojis, é spam


def _count_profanity(text: str) -> int:
    """Conta palavras profanas na mensagem."""
    text_lower = text.lower()
    count = 0
    for word in PROFANITY_WORDS:
        count += len(re.findall(rf"\b{word}\b", text_lower))
    return count


def _check_spam_patterns(text: str) -> bool:
    """Verifica padrões de spam."""
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def _check_harmful_patterns(text: str) -> bool:
    """Verifica conteúdo prejudicial."""
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def _count_emojis(text: str) -> int:
    """Conta emojis Unicode na mensagem."""
    emoji_pattern = re.compile(
        "["
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+",
        flags=re.UNICODE
    )
    return len(emoji_pattern.findall(text))


def check_violation(text: str) -> Tuple[bool, Optional[str], str]:
    """
    Verifica se uma mensagem viola as regras.
    
    Parâmetros:
        text: conteúdo da mensagem
    
    Retorna:
        Tuple[é_violação, tipo_violação, motivo]
        - é_violação: bool indicando se há violação
        - tipo_violação: string do tipo (None se não houver violação)
        - motivo: descrição legível da violação
    """
    
    if not text or len(text) < 2:
        return False, None, ""
    
    # Verificar spam
    if _check_spam_patterns(text):
        return True, "spam", "Padrão de spam detectado (caracteres repetidos)"
    
    # Contar emojis
    emoji_count = _count_emojis(text)
    if emoji_count > SPAM_EMOJIS_THRESHOLD:
        return True, "spam", f"Spam de emojis detectado ({emoji_count} emojis)"
    
    # Verificar conteúdo prejudicial
    if _check_harmful_patterns(text):
        return True, "conteudo_prejudicial", "Conteúdo prejudicial ou violento detectado"
    
    # Verificar profanidade
    profanity_count = _count_profanity(text)
    if profanity_count > 0:
        return True, "profanidade", f"Linguagem ofensiva detectada ({profanity_count} instância(s))"
    
    # Verificar caps lock excessivo (mais de 70% em maiúsculas)
    if len(text) > 5:
        uppercase_count = sum(1 for c in text if c.isupper())
        uppercase_ratio = uppercase_count / len(text)
        if uppercase_ratio > 0.7:
            return True, "spam", "Caps lock excessivo detectado"
    
    return False, None, ""


def get_violation_severity(violation_type: Optional[str]) -> int:
    """
    Retorna a severidade de uma violação (0-10).
    
    Parâmetros:
        violation_type: tipo de violação
    
    Retorna:
        int com score de severidade
    """
    severity_map = {
        "spam": 3,
        "profanidade": 5,
        "conteudo_prejudicial": 10,
        "publicidade": 6,
        "link_suspeito": 7,
    }
    return severity_map.get(violation_type, 1)


def should_auto_warn(violation_type: Optional[str]) -> bool:
    """
    Determina se uma violação deve gerar aviso automático.
    
    Parâmetros:
        violation_type: tipo de violação
    
    Retorna:
        bool indicando se deve registrar aviso automático
    """
    # Apenas violações graves geram avisos automáticos
    auto_warn_types = {"conteudo_prejudicial", "profanidade"}
    return violation_type in auto_warn_types
