from difflib import get_close_matches

from typing import Literal

LANGUAGES = [
    ("ar-EG", "Arabic (Egyptian)"),
    ("bn-BD", "Bengali (Bangladesh)"),
    ("nl-NL", "Dutch (Netherlands)"),
    ("en-IN", "English (India)"),
    ("en-US", "English (US)"),
    ("fr-FR", "French (France)"),
    ("de-DE", "German (Germany)"),
    ("hi-IN", "Hindi (India)"),
    ("id-ID", "Indonesian (Indonesia)"),
    ("it-IT", "Italian (Italy)"),
    ("ja-JP", "Japanese (Japan)"),
    ("ko-KR", "Korean (Korea)"),
    ("mr-IN", "Marathi (India)"),
    ("pl-PL", "Polish (Poland)"),
    ("pt-BR", "Portuguese (Brazil)"),
    ("ro-RO", "Romanian (Romania)"),
    ("ru-RU", "Russian (Russia)"),
    ("es-US", "Spanish (US)"),
    ("ta-IN", "Tamil (India)"),
    ("te-IN", "Telugu (India)"),
    ("th-TH", "Thai (Thailand)"),
    ("tr-TR", "Turkish (Turkey)"),
    ("uk-UA", "Ukrainian (Ukraine)"),
    ("vi-VN", "Vietnamese (Vietnam)"),
]


def select_language_by_name(name: str) -> str:
    """
    Returns the language code for the closest matching language name using fuzzy matching.
    Args:
        name (str): The display name to match (e.g., 'Polish (Poland)').
    Returns:
        str: The language code (e.g., 'pl-PL').
    Raises:
        ValueError: If no close match is found for the language name.
    """
    names = [display for code, display in LANGUAGES]
    matches = get_close_matches(name, names, n=1, cutoff=0.0)
    if matches:
        for code, display in LANGUAGES:
            if display.lower() == matches[0].lower():
                print(f"Selected language by name '{name}': {code} ({display})")
                return code
    raise ValueError(f"No close match found for language name '{name}'.")