# actions/spotify_control.py
import json
import re
import sys
import subprocess
import platform
import time
from pathlib import Path

_OS = platform.system()

try:
    import pyautogui
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def _get_api_key() -> str:
    path = _get_base_dir() / "config" / "api_keys.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

def _run_applescript(script: str) -> tuple[str, bool]:
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return res.stdout.strip(), True
        return res.stderr.strip(), False
    except Exception as e:
        return str(e), False

def _search_spotify_track(query: str) -> str | None:
    """Uses Gemini Search to find the direct Spotify track URL for a query."""
    try:
        from google import genai
        client = genai.Client(api_key=_get_api_key())
        prompt = (
            f"Find the Spotify track URL for the song: '{query}'. "
            "Return only the raw URL (e.g., https://open.spotify.com/track/...) and absolutely nothing else. "
            "If you cannot find it, reply: NOT_FOUND"
        )
        for model_name in ["gemini-2.5-flash-lite", "gemini-2.5-flash"]:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"tools": [{"google_search": {}}]}
                )
                text = resp.text.strip() if resp.text else ""
                if "NOT_FOUND" not in text and "spotify.com/track/" in text:
                    match = re.search(r"https://open\.spotify\.com/track/[a-zA-Z0-9]+", text)
                    if match:
                        return match.group(0)
            except Exception as inner_e:
                print(f"[Spotify] ⚠️ Search with {model_name} failed: {inner_e}")
    except Exception as e:
        print(f"[Spotify] ⚠️ Gemini track search failed: {e}")
    return None

def spotify_control(parameters: dict, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "").lower().strip()
    query = params.get("query", "").strip()
    volume = params.get("volume_level")

    if not action:
        return "No action specified."

    if player:
        player.write_log(f"[Spotify] {action}")

    # Media shortcut keys fallback for Windows/Linux
    if _OS != "Darwin":
        if not _PYAUTOGUI:
            return "pyautogui is not installed. Action is not supported."
        if action in ("play", "pause", "play_pause"):
            pyautogui.press("playpause")
            return "Sent Play/Pause media key."
        elif action == "next":
            pyautogui.press("nexttrack")
            return "Sent Next Track media key."
        elif action == "previous":
            pyautogui.press("prevtrack")
            return "Sent Previous Track media key."
        elif action == "search_play" and query:
            subprocess.Popen(["open", f"spotify:search:{query}"])
            return f"Opened Spotify search page for: {query}"
        return f"Action '{action}' is only fully supported on macOS."

    # macOS Direct AppleScript Integration
    if action == "play_pause":
        out, ok = _run_applescript('tell application "Spotify" to playpause')
        return "Toggled play/pause." if ok else f"Failed to toggle playback: {out}"

    elif action == "play":
        out, ok = _run_applescript('tell application "Spotify" to play')
        return "Playing Spotify." if ok else f"Failed to play: {out}"

    elif action == "pause":
        out, ok = _run_applescript('tell application "Spotify" to pause')
        return "Paused Spotify." if ok else f"Failed to pause: {out}"

    elif action == "next":
        out, ok = _run_applescript('tell application "Spotify" to next track')
        return "Skipped to next track." if ok else f"Failed to skip: {out}"

    elif action == "previous":
        out, ok = _run_applescript('tell application "Spotify" to previous track')
        return "Went to previous track." if ok else f"Failed to go back: {out}"

    elif action == "volume":
        if volume is None:
            return "Volume level is required."
        vol = max(0, min(100, int(volume)))
        out, ok = _run_applescript(f'tell application "Spotify" to set sound volume to {vol}')
        return f"Set Spotify volume to {vol}%." if ok else f"Failed to set volume: {out}"

    elif action == "get_info":
        script = """
        tell application "Spotify"
            if it is running then
                try
                    set trackName to name of current track
                    set artistName to artist of current track
                    set albumName to album of current track
                    set playerState to player state as string
                    return "Track: " & trackName & "\\nArtist: " & artistName & "\\nAlbum: " & albumName & "\\nState: " & playerState
                on error
                    return "Spotify is running, but no track is currently loaded."
                end try
            else
                return "Spotify is not running."
            end if
        end tell
        """
        out, ok = _run_applescript(script)
        return out if ok else f"Failed to get track info: {out}"

    elif action == "search_play":
        if not query:
            return "Search query is required."
        
        # 1. Attempt Gemini Google search to find a direct track URI
        track_url = _search_spotify_track(query)
        if track_url:
            track_id = track_url.split("/track/")[-1].split("?")[0]
            uri = f"spotify:track:{track_id}"
            out, ok = _run_applescript(f'tell application "Spotify" to play track "{uri}"')
            if ok:
                return f"Directly playing: {query} (Spotify URI: {uri})"
        
        # 2. Fallback: open Spotify search page, focus it, and let Spotify play or search
        subprocess.Popen(["open", f"spotify:search:{query}"])
        # Give a moment to load
        time.sleep(1.5)
        # Focus and trigger keystroke fallback (press enter/play)
        focus_script = """
        tell application "Spotify" to activate
        delay 0.5
        tell application "System Events"
            tell process "Spotify"
                key code 125 -- Down arrow
                delay 0.3
                key code 36  -- Enter
            end tell
        end tell
        """
        _run_applescript(focus_script)
        return f"Opened Spotify search and attempted playback for: {query}"

    return f"Unknown action: {action}"
