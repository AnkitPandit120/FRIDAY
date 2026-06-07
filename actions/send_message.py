import json
import subprocess
import sys
import time
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = 0.06
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False

def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def _get_os() -> str:
    try:
        cfg = json.loads(
            (_base_dir() / "config" / "api_keys.json").read_text(encoding="utf-8")
        )
        return cfg.get("os_system", "windows").lower()
    except Exception:
        return "windows"


def _require_pyautogui():
    if not _PYAUTOGUI:
        raise RuntimeError("PyAutoGUI not installed. Run: pip install pyautogui")


def _paste_text(text: str) -> None:
    _require_pyautogui()

    os_name = _get_os()
    paste_hotkey = ("command", "v") if os_name == "mac" else ("ctrl", "v")

    if _PYPERCLIP:
        pyperclip.copy(text)
        time.sleep(0.15)
        pyautogui.hotkey(*paste_hotkey)
        time.sleep(0.1)
    else:
        pyautogui.write(text, interval=0.03)


def _clear_and_paste(text: str) -> None:
    _require_pyautogui()
    os_name = _get_os()
    select_all = ("command", "a") if os_name == "mac" else ("ctrl", "a")
    pyautogui.hotkey(*select_all)
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)
    _paste_text(text)

def _open_app(app_name: str) -> bool:
    _require_pyautogui()
    os_name = _get_os()

    try:
        if os_name == "windows":
            pyautogui.press("win")
            time.sleep(0.5)
            _paste_text(app_name)
            time.sleep(0.6)
            pyautogui.press("enter")
            time.sleep(2.5)
            return True

        elif os_name == "mac":
            # Force focus using AppleScript first
            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to activate'])
            time.sleep(1.5)
            result = subprocess.run(
                ["open", "-a", app_name],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                result = subprocess.run(
                    ["open", "-a", f"{app_name}.app"],
                    capture_output=True, text=True, timeout=10,
                )
            time.sleep(1.0)
            return True

        else: 
            launched = False
            for launcher in [
                ["gtk-launch", app_name.lower()],
                [app_name.lower()],
            ]:
                try:
                    subprocess.Popen(
                        launcher,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    launched = True
                    break
                except FileNotFoundError:
                    continue
            time.sleep(2.5)
            return launched

    except Exception as e:
        print(f"[SendMessage] ⚠️ Could not open {app_name}: {e}")
        return False


def _open_browser_url(url: str) -> bool:
    import webbrowser
    try:
        webbrowser.open(url)
        time.sleep(4.0) 
        return True
    except Exception as e:
        print(f"[SendMessage] ⚠️ Could not open browser: {e}")
        return False

def _search_in_app(query: str) -> None:
    _require_pyautogui()
    os_name = _get_os()
    search_hotkey = ("command", "f") if os_name == "mac" else ("ctrl", "f")

    pyautogui.hotkey(*search_hotkey)
    time.sleep(0.5)
    _clear_and_paste(query)
    time.sleep(1.0)

import io
import re

def _is_phone_number(text: str) -> bool:
    cleaned = re.sub(r"[\s\-\+\(\)]", "", text)
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15

def _format_whatsapp_number(number: str) -> str:
    digits = re.sub(r"\D", "", number)
    if len(digits) == 10:
        return f"91{digits}"
    return digits

def _get_api_key() -> str:
    path = _base_dir() / "config" / "api_keys.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

def _resolve_contact_with_vision(app_name: str, receiver: str) -> dict:
    """Takes a screenshot of the app search results and uses Gemini to find match coordinates."""
    api_key = _get_api_key()
    if not api_key:
        return {}

    w, h = pyautogui.size()
    img = pyautogui.screenshot()
    img = img.resize((w, h))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    prompt = (
        f"This is a screenshot of a {w}x{h} pixel screen showing the application '{app_name}'. "
        f"We searched for the contact '{receiver}'. "
        f"Please analyze the search results shown in the sidebar/list. "
        f"Find all matching contact/group/chat names. "
        f"Respond with a JSON object in this format (no markdown code blocks, just the raw JSON): "
        f'{{"matches": ["Contact Name 1", "Contact Name 2"], "click_coords": [x, y]}} '
        f"where 'click_coords' is the center coordinates [x, y] of the first match (only if there is exactly one clear match, otherwise null)."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "matches": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "List of matching chat/contact/group names"
                        },
                        "click_coords": {
                            "type": "ARRAY",
                            "items": {"type": "INTEGER"},
                            "description": "[x, y] coordinates of the first match if exactly one match, or null"
                        }
                    },
                    "required": ["matches"]
                }
            }
        )
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"[SendMessage] ⚠️ Vision resolution failed: {e}")
        return {}

def _get_window_position(app_name: str):
    """Returns (x, y, width, height) of the app's first window using System Events."""
    result = subprocess.run(
        ["osascript", "-e",
         f'tell application "System Events" to tell process "{app_name}" to get {{position, size}} of window 1'],
        capture_output=True, text=True, timeout=5
    )
    if result.stdout.strip():
        try:
            parts = [int(x.strip()) for x in result.stdout.strip().split(",")]
            return parts[0], parts[1], parts[2], parts[3]
        except Exception:
            pass
    return None


def _click_first_search_result(app_name: str) -> bool:
    """Click the first search result in the sidebar using window-relative coordinates.

    For WhatsApp on macOS:
    - The sidebar runs from x_start to ~x_start+370
    - The search bar is at ~y_start+100
    - 'Chats' header is at ~y_start+170
    - First chat result is at ~y_start+210
    Returns True if click was performed, False otherwise.
    """
    win = _get_window_position(app_name)
    if not win:
        return False
    wx, wy, ww, wh = win
    # The first chat result in search is roughly 210px from top, 210px from left
    click_x = wx + 210
    click_y = wy + 210
    print(f"[SendMessage] Clicking first search result at ({click_x}, {click_y})")
    pyautogui.click(click_x, click_y)
    time.sleep(1.0)
    return True


def _desktop_send(app_name: str, receiver: str, message: str) -> str:
    if not _open_app(app_name):
        return f"Could not open {app_name}."

    time.sleep(1.0)

    if app_name.lower() == "whatsapp" and _is_phone_number(receiver):
        formatted_num = _format_whatsapp_number(receiver)
        url = f"whatsapp://send?phone={formatted_num}"
        print(f"[SendMessage] Opening direct WhatsApp chat URI: {url}")
        subprocess.Popen(["open", url])
        time.sleep(2.0)
    else:
        _search_in_app(receiver)
        time.sleep(1.2)

        # Resolve contact using Vision AI
        res = _resolve_contact_with_vision(app_name, receiver)
        matches = res.get("matches", [])
        coords = res.get("click_coords")
        print(f"[SendMessage] Vision matches: {matches}, click_coords: {coords}")

        if len(matches) > 1:
            names = ", ".join(f"'{m}'" for m in matches)
            return f"Multiple contacts found: {names}. Which one would you like to send the message to?"

        if coords and len(coords) == 2:
            # Vision AI found exact coordinates — click them
            pyautogui.click(coords[0], coords[1])
            time.sleep(0.8)
        else:
            # Fallback: click the first result in the sidebar using window-relative coordinates.
            # This is more reliable than pressing Enter (which opens the previously active chat).
            if not _click_first_search_result(app_name):
                # Last resort: press Enter
                pyautogui.press("enter")
                time.sleep(0.8)

    _paste_text(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)
    return f"Message sent to {receiver} via {app_name}."

def _send_whatsapp(receiver: str, message: str) -> str:
    return _desktop_send("WhatsApp", receiver, message)

def _send_telegram(receiver: str, message: str) -> str:
    return _desktop_send("Telegram", receiver, message)

def _send_signal(receiver: str, message: str) -> str:
    return _desktop_send("Signal", receiver, message)


def _send_discord(receiver: str, message: str) -> str:
    return _desktop_send("Discord", receiver, message)


def _send_instagram(receiver: str, message: str) -> str:
    _require_pyautogui()

    if not _open_browser_url("https://www.instagram.com/direct/new/"):
        return "Could not open Instagram in browser."

    _paste_text(receiver)
    time.sleep(1.5)

    pyautogui.press("down")
    time.sleep(0.3)
    pyautogui.press("enter")   
    time.sleep(0.4)

    for _ in range(4):
        pyautogui.press("tab")
        time.sleep(0.15)
    pyautogui.press("enter")
    time.sleep(2.0)

    _paste_text(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)

    return f"Message sent to {receiver} via Instagram."


def _send_messenger(receiver: str, message: str) -> str:
    _require_pyautogui()

    if not _open_browser_url("https://www.messenger.com/"):
        return "Could not open Messenger in browser."


    _search_in_app(receiver)
    time.sleep(0.5)
    pyautogui.press("down")
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(1.0)

    _paste_text(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)

    return f"Message sent to {receiver} via Messenger."

_PLATFORM_MAP = [
    ({"whatsapp", "wp", "wapp"},              _send_whatsapp),
    ({"telegram", "tg"},                      _send_telegram),
    ({"instagram", "ig", "insta"},            _send_instagram),
    ({"signal"},                               _send_signal),
    ({"discord"},                              _send_discord),
    ({"messenger", "facebook", "fb"},         _send_messenger),
]


def _resolve_platform(platform_str: str):
    key = platform_str.lower().strip()
    for keywords, handler in _PLATFORM_MAP:
        if any(k in key for k in keywords):
            return handler
    return lambda r, m: _desktop_send(platform_str.strip().title(), r, m)


def send_message(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params       = parameters or {}
    receiver     = params.get("receiver", "").strip()
    message_text = params.get("message_text", "").strip()
    platform     = params.get("platform", "whatsapp").strip()
    confirmed    = params.get("confirmed", False)

    if not receiver:
        return "Please specify a recipient."
    if not message_text:
        return "Please specify the message content."
    if not _PYAUTOGUI:
        return "PyAutoGUI is not installed — cannot control the desktop."

    # Ask for confirmation via Friday's voice if not already confirmed by user in previous turn
    if not confirmed:
        result = f"CONFIRMATION_REQUIRED: Ask the user: 'Do you want me to send the message \"{message_text}\" to {receiver} via {platform}?'"
        print(f"[SendMessage] 🛑 {result}")
        if player:
            player.write_log(f"[msg] {result}")
        return result

    preview = message_text[:50] + ("…" if len(message_text) > 50 else "")
    print(f"[SendMessage] 📨 {platform} → {receiver}: {preview}")
    if player:
        player.write_log(f"[msg] {platform} → {receiver}")

    try:
        handler = _resolve_platform(platform)
        result  = handler(receiver, message_text)
    except Exception as e:
        result = f"Could not send message: {e}"

    print(f"[SendMessage] {'✅' if 'sent' in result.lower() else '❌'} {result}")
    if player:
        player.write_log(f"[msg] {result}")

    return result