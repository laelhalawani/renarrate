from typing import List, Dict, Optional
from difflib import get_close_matches

# preview voices here https://aistudio.google.com/generate-speech
VOICE_LIST: List[Dict[str, str]] = [
    {"name": "Zephyr", "description": "Bright, Higher pitch, Female"},
    {"name": "Puck", "description": "Upbeat, Middle pitch, Male"},
    {"name": "Charon", "description": "Informative, Lower pitch, Male"},
    {"name": "Kore", "description": "Firm, Middle pitch, Female"},
    {"name": "Fenrir", "description": "Excitable, Lower middle pitch, Male"},
    {"name": "Leda", "description": "Youthful, Higher pitch, Female"},
    {"name": "Orus", "description": "Firm, Lower middle pitch, Male"},
    {"name": "Aoede", "description": "Breezy, Middle pitch, Female"},
    {"name": "Callirrhoe", "description": "Easy-going, Middle pitch, Female"},
    {"name": "Autonoe", "description": "Bright, Middle pitch, Female"},
    {"name": "Enceladus", "description": "Breathy, Lower pitch, Male"},
    {"name": "Iapetus", "description": "Clear, Lower middle pitch, Male"},
    {"name": "Umbriel", "description": "Easy-going, Lower middle pitch, Male"},
    {"name": "Algieba", "description": "Smooth, Lower pitch, Male"},
    {"name": "Despina", "description": "Smooth, Middle pitch, Female"},
    {"name": "Erinome", "description": "Clear, Middle pitch, Female"},
    {"name": "Algenib", "description": "Gravelly, Lower pitch, Male"},
    {"name": "Rasalgethi", "description": "Informative, Middle pitch, Male"},
    {"name": "Laomedeia", "description": "Upbeat, Higher pitch, Female"},
    {"name": "Achernar", "description": "Soft, Higher pitch, Female"},
    {"name": "Alnilam", "description": "Firm, Lower middle pitch, Male"},
    {"name": "Schedar", "description": "Even, Lower middle pitch, Male"},
    {"name": "Gacrux", "description": "Mature, Middle pitch, Female"},
    {"name": "Pulcherrima", "description": "Forward, Middle pitch, Female"},
    {"name": "Achird", "description": "Friendly, Lower middle pitch, Male"},
    {"name": "Zubenelgenubi", "description": "Casual, Lower middle pitch, Male"},
    {"name": "Vindemiatrix", "description": "Gentle, Middle pitch, Female"},
    {"name": "Sadachbia", "description": "Lively, Lower pitch, Male"},
    {"name": "Sadaltager", "description": "Knowledgeable, Middle pitch, Male"},
    {"name": "Sulafat", "description": "Warm, Middle pitch, Female"},
]

def select_voice_by_id(id: int) -> str:
    """
    Selects a voice name by its index in VOICE_LIST and logs the selection.
    If the index is out of range, returns the first voice in the list.
    Args:
        id (int): Index of the voice (0-based).
    Returns:
        str: Selected voice name.
    """
    if 0 <= id < len(VOICE_LIST):
        voice = VOICE_LIST[id]
        print(f"Selected voice by id {id}: {voice['name']} ({voice['description']})")
        return voice["name"]
    print(f"Voice id {id} is out of range. Returning first available voice: {VOICE_LIST[0]['name']} ({VOICE_LIST[0]['description']})")
    return VOICE_LIST[0]["name"]

def select_voice_by_characteristic(description: str) -> str:
    """
    Selects the voice name with the most similar description (including gender, pitch, etc.) using fuzzy matching and logs the selection.
    If no match is found, returns the first voice in the list.
    Args:
        description (str): Description to match (e.g., 'Bright, Female').
    Returns:
        str: Selected voice name.
    """
    descriptions = [v["description"] for v in VOICE_LIST]
    matches = get_close_matches(description, descriptions, n=1, cutoff=0.6)
    if matches:
        for v in VOICE_LIST:
            if v["description"].lower() == matches[0].lower():
                print(f"Selected voice by characteristic '{description}': {v['name']} ({v['description']})")
                return v["name"]
    print(f"No close match found for characteristic '{description}' with cutoff. Retrying without cutoff...")
    matches = get_close_matches(description, descriptions, n=1, cutoff=0.0)
    if matches:
        for v in VOICE_LIST:
            if v["description"].lower() == matches[0].lower():
                print(f"Selected voice by characteristic (no cutoff) '{description}': {v['name']} ({v['description']})")
                return v["name"]
    print(f"No voice found matching characteristic '{description}' even without cutoff. Returning first available voice: {VOICE_LIST[0]['name']} ({VOICE_LIST[0]['description']})")
    return VOICE_LIST[0]["name"]

def select_voice_by_name(name: str) -> str:
    """
    Selects the voice name with the most similar name using fuzzy matching and logs the selection.
    If no match is found, returns the first voice in the list.
    Args:
        name (str): Name to match (e.g., 'Kore').
    Returns:
        str: Selected voice name.
    """
    names = [v["name"] for v in VOICE_LIST]
    matches = get_close_matches(name, names, n=1, cutoff=0.6)
    if matches:
        for v in VOICE_LIST:
            if v["name"].lower() == matches[0].lower():
                print(f"Selected voice by name '{name}': {v['name']} ({v['description']})")
                return v["name"]
    print(f"No close match found for name '{name}' with cutoff. Retrying without cutoff...")
    matches = get_close_matches(name, names, n=1, cutoff=0.0)
    if matches:
        for v in VOICE_LIST:
            if v["name"].lower() == matches[0].lower():
                print(f"Selected voice by name (no cutoff) '{name}': {v['name']} ({v['description']})")
                return v["name"]
    print(f"No voice found matching name '{name}' even without cutoff. Returning first available voice: {VOICE_LIST[0]['name']} ({VOICE_LIST[0]['description']})")
    return VOICE_LIST[0]["name"]
