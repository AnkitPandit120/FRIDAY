# actions/clipboard_manager.py
import re
import json

try:
    import pyperclip
    _PYPERCLIP_OK = True
except ImportError:
    _PYPERCLIP_OK = False


def clipboard_control(parameters: dict, player=None) -> str:
    """
    Manages the system clipboard: copy, paste, clear, format, or extract information.
    """
    action = parameters.get("action", "").lower().strip()
    text = parameters.get("text", "")
    
    if player:
        player.write_log(f"[Clipboard] Action: {action}")

    if not _PYPERCLIP_OK:
        return "Sir, pyperclip is not installed. Please install it using pip install pyperclip."

    if not action:
        return "Sir, please specify an action ('get', 'set', 'clear', 'extract', or 'format')."

    try:
        if action == "set":
            if not text:
                return "Sir, please provide the text to copy to the clipboard."
            pyperclip.copy(text)
            return f"Successfully copied to clipboard: '{text[:60]}...'" if len(text) > 60 else f"Successfully copied to clipboard: '{text}'"

        elif action == "get":
            content = pyperclip.paste()
            if not content:
                return "Sir, the clipboard is currently empty."
            return f"Clipboard Content:\n{content}"

        elif action == "clear":
            pyperclip.copy("")
            return "Sir, the clipboard has been cleared."

        elif action == "extract":
            content = pyperclip.paste()
            if not content:
                return "Sir, clipboard is empty; nothing to extract."
            
            extract_type = parameters.get("extract_type", "").lower().strip()
            if not extract_type:
                return "Sir, please specify extract_type: 'emails', 'urls', or 'phones'."

            if extract_type == "emails":
                pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                matches = re.findall(pattern, content)
                if not matches:
                    return "No email addresses found in clipboard."
                return f"Found Emails:\n" + "\n".join(set(matches))

            elif extract_type == "urls":
                pattern = r"https?://[^\s]+"
                matches = re.findall(pattern, content)
                if not matches:
                    return "No URLs found in clipboard."
                return f"Found URLs:\n" + "\n".join(set(matches))

            elif extract_type == "phones":
                pattern = r"\+?\d[\d -]{7,}\d"
                matches = re.findall(pattern, content)
                if not matches:
                    return "No phone numbers found in clipboard."
                return f"Found Phone Numbers:\n" + "\n".join(set(matches))

            else:
                return f"Sir, extraction type '{extract_type}' is not supported. Use emails, urls, or phones."

        elif action == "format":
            content = pyperclip.paste()
            if not content:
                return "Sir, clipboard is empty; nothing to format."

            format_type = parameters.get("format_type", "").lower().strip()
            if not format_type:
                return "Sir, please specify format_type: 'trim', 'json', or 'clean'."

            if format_type == "trim":
                formatted = content.strip()
                pyperclip.copy(formatted)
                return f"Trimmed clipboard content:\n{formatted}"

            elif format_type == "json":
                try:
                    parsed = json.loads(content)
                    formatted = json.dumps(parsed, indent=4)
                    pyperclip.copy(formatted)
                    return f"Pretty-printed JSON copied to clipboard:\n{formatted[:200]}..."
                except Exception as e:
                    return f"Sir, clipboard content is not valid JSON. Error: {e}"

            elif format_type == "clean":
                # Remove tabs, multiple whitespaces/newlines
                formatted = re.sub(r"[ \t]+", " ", content)
                formatted = re.sub(r"\n+", "\n", formatted).strip()
                pyperclip.copy(formatted)
                return f"Cleaned clipboard content:\n{formatted}"

            else:
                return f"Sir, format type '{format_type}' is not supported. Use trim, json, or clean."

        else:
            return f"Unknown clipboard action: {action}"

    except Exception as e:
        return f"Sir, clipboard operation failed: {e}"
