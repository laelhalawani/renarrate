from typing import List, Dict, Optional
from flow.models.voices import ElevenLabsVoice
from difflib import get_close_matches

VOICE_LIST: List[Dict[str, str]] = [
    {
        "name": "Aria",
        "id": "9BWtsMINqrJLrRacOk9x",
        "description": "A middle-aged female with an African-American accent. Calm with a hint of rasp."
    },
    {
        "name": "Sarah",
        "id": "EXAVITQu4vr4xnSDxMaL",
        "description": "Young adult woman with a confident and warm, mature quality and a reassuring, professional tone."
    },
    {
        "name": "Laura",
        "id": "FGY2WhTYpPnrIDTdsKH5",
        "description": "This young adult female voice delivers sunny enthusiasm with a quirky attitude."
    },
    {
        "name": "Charlie",
        "id": "IKne3meq5aSn9XLyUdCD",
        "description": "A young Australian male with a confident and energetic voice."
    },
    {
        "name": "George",
        "id": "JBFqnCBsd6RMkjVDRZzb",
        "description": "Warm resonance that instantly captivates listeners."
    },
    {
        "name": "Callum",
        "id": "N2lVS1w4EtoT3dr4eOWO",
        "description": "Deceptively gravelly, yet unsettling edge."
    },
    {
        "name": "River",
        "id": "SAz9YHcvj6GT2YYXdXww",
        "description": "A relaxed, neutral voice ready for narrations or conversational projects."
    },
    {
        "name": "Liam",
        "id": "TX3LPaxmHKxFdv7VOQHJ",
        "description": "A young adult with energy and warmth - suitable for reels and shorts."
    },
    {
        "name": "Charlotte",
        "id": "XB0fDUnXU5powFXDhCwa",
        "description": "Sensual and raspy, she's ready to voice your temptress in video games."
    },
    {
        "name": "Alice",
        "id": "Xb7hH8MSUJpSbSDYk0k2",
        "description": "Clear and engaging, friendly woman with a British accent suitable for e-learning."
    },
    {
        "name": "Matilda",
        "id": "XrExE9yKIg1WjnnlVkGX",
        "description": "A professional woman with a pleasing alto pitch. Suitable for many use cases."
    },
    {
        "name": "Will",
        "id": "bIHbv24MWmeRgasZH58o",
        "description": "Conversational and laid back."
    },
    {
        "name": "Jessica",
        "id": "cgSgspJ2msm6clMCkdW9",
        "description": "Young and popular, this playful American female voice is perfect for trendy content."
    },
    {
        "name": "Eric",
        "id": "cjVigY5qzO86Huf0OWal",
        "description": "A smooth tenor pitch from a man in his 40s - perfect for agentic use cases."
    },
    {
        "name": "Chris",
        "id": "iP95p4xoKVk53GoZ742B",
        "description": "Natural and real, this down-to-earth voice is great across many use-cases."
    },
    {
        "name": "Brian",
        "id": "nPczCjzI2devNBz1zQrb",
        "description": "Middle-aged man with a resonant and comforting tone. Great for narrations and advertisements."
    },
    {
        "name": "Daniel",
        "id": "onwK4e9ZLuTAKqWW03F9",
        "description": "A strong voice perfect for delivering a professional broadcast or news story."
    },
    {
        "name": "Lily",
        "id": "pFZP5JQG7iQjIQuC4Bku",
        "description": "Velvety British female voice delivers news and narrations with warmth and clarity."
    },
    {
        "name": "Bill",
        "id": "pqHfZKP75CvOlQylNhV4",
        "description": "Friendly and comforting voice ready to narrate your stories."
    }
]


def voice_dict_to_voice(voice_dict: Dict[str, str]) -> ElevenLabsVoice:
	"""
	Converts a dictionary representation of a voice to an ElevenLabsVoice instance.
	Args:
		voice_dict (Dict[str, str]): Dictionary containing voice information.
	Returns:
		ElevenLabsVoice: Instance of ElevenLabsVoice with the provided information.
	"""
	return ElevenLabsVoice(name=voice_dict["name"], id=voice_dict["id"], description=voice_dict["description"])


def select_voice_by_id(id: int) -> ElevenLabsVoice:
	"""
	Selects a voice by its index in VOICE_LIST and logs the selection.
	If the index is out of range, returns the first voice in the list.
	Args:
		id (int): Index of the voice (0-based).
	Returns:
		ElevenLabsVoice: Selected voice instance.
	"""
	if 0 <= id < len(VOICE_LIST):
		voice = VOICE_LIST[id]
		print(f"Selected voice by id {id}: {voice['name']} ({voice['description']})")
	else:
		# If the index is out of range, return the first voice in the list
		print(f"Voice id {id} is out of range. Returning first available voice: {VOICE_LIST[0]['name']} ({VOICE_LIST[0]['description']})")
		voice = VOICE_LIST[0]
	
	return voice_dict_to_voice(voice)


def select_voice_by_characteristic(description: str) -> ElevenLabsVoice:
    """
    Selects the voice with the most similar description (including accent, age, etc.) using fuzzy matching and logs the selection.
    If no match is found, returns the first voice in the list.
    Args:
        description (str): Description to match (e.g., 'African-American accent').
    Returns:
        ElevenLabsVoice: Selected voice instance.
    """
    descriptions = [v["description"] for v in VOICE_LIST]
    matches = get_close_matches(description, descriptions, n=1, cutoff=0.6)
    if matches:
        for v in VOICE_LIST:
            if v["description"].lower() == matches[0].lower():
                print(f"Selected voice by characteristic '{description}': {v['name']} ({v['description']})")
                voice = v
    else:
        print(f"No close match found for characteristic '{description}' with cutoff. Retrying without cutoff...")
        matches = get_close_matches(description, descriptions, n=1, cutoff=0.0)
        if matches:
            for v in VOICE_LIST:
                if v["description"].lower() == matches[0].lower():
                    print(f"Selected voice by characteristic (no cutoff) '{description}': {v['name']} ({v['description']})")
                    voice = v
        else:
            print(f"No voice found matching characteristic '{description}' even without cutoff. Returning first available voice: {VOICE_LIST[0]['name']} ({VOICE_LIST[0]['description']})")
            voice = VOICE_LIST[0]
    return voice_dict_to_voice(voice)


def select_voice_by_name(name: str) -> ElevenLabsVoice:
    """
    Selects the voice with the most similar name using fuzzy matching and logs the selection.
    If no match is found, returns the first voice in the list.
    Args:
        name (str): Name to match (e.g., 'Aria').
    Returns:
        ElevenLabsVoice: Selected voice instance.
    """
    names = [v["name"] for v in VOICE_LIST]
    matches = get_close_matches(name, names, n=1, cutoff=0.6)
    if matches:
        for v in VOICE_LIST:
            if v["name"].lower() == matches[0].lower():
                print(f"Selected voice by name '{name}': {v['name']} ({v['description']})")
                voice = v
    else:
        print(f"No close match found for name '{name}' with cutoff. Retrying without cutoff...")
        matches = get_close_matches(name, names, n=1, cutoff=0.0)
        if matches:
            for v in VOICE_LIST:
                if v["name"].lower() == matches[0].lower():
                    print(f"Selected voice by name (no cutoff) '{name}': {v['name']} ({v['description']})")
                    voice = v
        else:
            print(f"No voice found matching name '{name}' even without cutoff. Returning first available voice: {VOICE_LIST[0]['name']} ({VOICE_LIST[0]['description']})")
            voice = VOICE_LIST[0]
    return voice_dict_to_voice(voice)
