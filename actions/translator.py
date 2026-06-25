# actions/translator.py
import json
import sys
from pathlib import Path
from google import genai
from google.genai import types

def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def _get_api_key() -> str:
    path = _get_base_dir() / "config" / "api_keys.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

def translator(parameters: dict, player=None) -> str:
    """
    Translates text between languages or detects the language of a text block using Gemini.
    """
    action = parameters.get("action", "translate").lower().strip()
    text = parameters.get("text", "").strip()

    if player:
        player.write_log(f"[Translator] Action: {action}")

    if not text:
        return "Sir, please provide the text to process."

    try:
        api_key = _get_api_key()
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"Sir, I couldn't load the Gemini API key for translation: {e}"

    if action == "translate":
        target = parameters.get("to", "English").strip()
        prompt = (
            f"You are a professional translator. Translate the following text into {target}. "
            "Maintain the tone, style, and formatting of the original text. "
            "Output ONLY the translated text, with no notes, explanations, or extra commentary.\n\n"
            f"Text to translate:\n{text}"
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            translation = response.text.strip()
            return f"Translation (to {target}):\n{translation}"
        except Exception as e:
            return f"Sir, translation failed: {e}"

    elif action in ("detect", "detect_language"):
        prompt = (
            "You are a language detection system. Analyze the following text and detect its language. "
            "Output the response in the format: 'Detected Language: [Name of Language] (confidence: [X]%)'. "
            "Output ONLY this line, with absolutely no extra text.\n\n"
            f"Text:\n{text}"
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            detection = response.text.strip()
            return detection
        except Exception as e:
            return f"Sir, language detection failed: {e}"

    else:
        return f"Unknown translator action: {action}"
