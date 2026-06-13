# text_crypto.py
import base64
import hashlib
import random
import string


def text_crypto(
    parameters: dict,
    player=None,
) -> str:
    """
    Performs hashing, base64 coding, case converting, character/word statistics,
    or generates a strong password/passphrase.
    """
    action = parameters.get("action", "").lower().strip()
    text = parameters.get("text", "")
    
    if player:
        player.write_log(f"[TextCrypto] Action: {action}")

    if not action:
        return "Sir, please specify an action for the text cryptography tool."

    if action == "hash":
        algo = parameters.get("algorithm", "sha256").lower().strip()
        if not text:
            return "Sir, please provide the text to hash."
        
        encoded_text = text.encode("utf-8")
        if algo == "md5":
            res = hashlib.md5(encoded_text).hexdigest()
        elif algo == "sha1":
            res = hashlib.sha1(encoded_text).hexdigest()
        elif algo == "sha256":
            res = hashlib.sha256(encoded_text).hexdigest()
        else:
            return f"Sir, the algorithm '{algo}' is not supported. Use md5, sha1, or sha256."
        return f"Hash ({algo}): {res}"

    elif action in ("encode_base64", "base64_encode"):
        if not text:
            return "Sir, please provide the text to encode."
        res = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        return f"Base64 Encoded: {res}"

    elif action in ("decode_base64", "base64_decode"):
        if not text:
            return "Sir, please provide the base64 string to decode."
        try:
            res = base64.b64decode(text.encode("utf-8")).decode("utf-8")
            return f"Base64 Decoded: {res}"
        except Exception as e:
            return f"Sir, I failed to decode the base64 string. Error: {e}"

    elif action in ("case_convert", "change_case"):
        mode = parameters.get("mode", "upper").lower().strip()
        if not text:
            return "Sir, please provide the text to convert."
        if mode == "upper":
            res = text.upper()
        elif mode == "lower":
            res = text.lower()
        elif mode == "title":
            res = text.title()
        elif mode == "swap":
            res = text.swapcase()
        else:
            return f"Sir, the case mode '{mode}' is not supported. Use upper, lower, title, or swap."
        return f"Converted text:\n{res}"

    elif action in ("stats", "word_count"):
        if not text:
            return "Sir, please provide the text to analyze."
        chars = len(text)
        words = len(text.split())
        lines = len(text.splitlines())
        return f"Text Stats: {words} words, {chars} characters, {lines} lines."

    elif action in ("generate_password", "password"):
        length = int(parameters.get("length", 16))
        # Ensure password length is safe
        length = max(6, min(length, 128))
        
        include_upper = parameters.get("uppercase", True)
        include_digits = parameters.get("digits", True)
        include_special = parameters.get("special", True)

        chars = string.ascii_lowercase
        if include_upper:
            chars += string.ascii_uppercase
        if include_digits:
            chars += string.digits
        if include_special:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        res = "".join(random.choice(chars) for _ in range(length))
        return f"Generated Password: {res}"

    else:
        return f"Sir, the action '{action}' is unrecognized in text cryptography."
