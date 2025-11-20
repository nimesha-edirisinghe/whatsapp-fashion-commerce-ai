"""Language detection utilities."""

import re


def detect_language(text: str) -> str:
    """
    Detect language from message content.

    Simple heuristic-based detection using character patterns
    and common words.

    Args:
        text: Message text

    Returns:
        ISO 639-1 language code (default: "en")
    """
    if not text:
        return "en"

    text_lower = text.lower()

    # Spanish indicators
    spanish_patterns = [
        r"[áéíóúüñ¿¡]",  # Spanish accents and punctuation
        r"\b(hola|gracias|por favor|buenos|buenas|qué|cómo|dónde|cuánto|tiene|tienen|quiero|busco|necesito)\b",
    ]
    spanish_score = sum(
        1 for pattern in spanish_patterns
        if re.search(pattern, text_lower)
    )

    # French indicators
    french_patterns = [
        r"[àâçéèêëîïôùûü]",  # French accents
        r"\b(bonjour|merci|s'il vous plaît|je voudrais|comment|où|combien|avez-vous|cherche)\b",
    ]
    french_score = sum(
        1 for pattern in french_patterns
        if re.search(pattern, text_lower)
    )

    # Portuguese indicators
    portuguese_patterns = [
        r"[ãõçáàâéêíóôú]",  # Portuguese accents
        r"\b(olá|obrigado|por favor|bom dia|boa tarde|como|onde|quanto|tem|tenho|quero|preciso)\b",
    ]
    portuguese_score = sum(
        1 for pattern in portuguese_patterns
        if re.search(pattern, text_lower)
    )

    # German indicators
    german_patterns = [
        r"[äöüß]",  # German special characters
        r"\b(hallo|danke|bitte|guten|wie|wo|wieviel|haben|möchte|suche|brauche)\b",
    ]
    german_score = sum(
        1 for pattern in german_patterns
        if re.search(pattern, text_lower)
    )

    # Italian indicators
    italian_patterns = [
        r"[àèéìíîòóùú]",  # Italian accents
        r"\b(ciao|grazie|per favore|buongiorno|come|dove|quanto|avete|vorrei|cerco)\b",
    ]
    italian_score = sum(
        1 for pattern in italian_patterns
        if re.search(pattern, text_lower)
    )

    # Find highest scoring language
    scores = {
        "es": spanish_score,
        "fr": french_score,
        "pt": portuguese_score,
        "de": german_score,
        "it": italian_score,
    }

    max_score = max(scores.values())
    if max_score > 0:
        for lang, score in scores.items():
            if score == max_score:
                return lang

    # Default to English
    return "en"


def get_language_name(code: str) -> str:
    """
    Get full language name from code.

    Args:
        code: ISO 639-1 language code

    Returns:
        Language name
    """
    names = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "pt": "Portuguese",
        "de": "German",
        "it": "Italian",
    }
    return names.get(code, "English")
