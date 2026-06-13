# weather_report.py
import urllib.parse
import webbrowser
import requests


def weather_action(
    parameters: dict,
    player=None,
    session_memory=None,
) -> str:
    """
    Gives the weather report to the user by fetching live data from wttr.in.
    Falls back to opening a Google search in the browser if the API is offline.
    """
    city = parameters.get("city")
    when = parameters.get("time", "today")

    if not city or not isinstance(city, str) or not city.strip():
        msg = "Sir, the city is missing for the weather report."
        _log(msg, player)
        return msg

    city = city.strip()
    when = (when or "today").strip()

    search_query = f"weather in {city} {when}"
    google_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"

    # Try wttr.in live weather API first (only for 'today' or current weather)
    if when == "today" or "now" in when.lower():
        try:
            _log(f"Fetching live weather for {city} from wttr.in...", player)
            # wttr.in format=j1 returns full JSON structure
            encoded_city = urllib.parse.quote(city)
            api_url = f"https://wttr.in/{encoded_city}?format=j1"
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get("current_condition", [{}])[0]
                temp_c = current.get("temp_C")
                temp_f = current.get("temp_F")
                weather_desc = current.get("weatherDesc", [{}])[0].get("value")
                humidity = current.get("humidity")
                wind_speed = current.get("windspeedKmph")
                
                # Retrieve location name resolved by wttr.in
                nearest_area = data.get("nearest_area", [{}])[0]
                area_name = nearest_area.get("areaName", [{}])[0].get("value", city)
                country = nearest_area.get("country", [{}])[0].get("value", "")
                
                full_location = f"{area_name}, {country}" if country else area_name

                msg = (
                    f"Sir, current weather in {full_location} is {weather_desc}. "
                    f"Temperature is {temp_c}°C ({temp_f}°F), humidity is {humidity}%, "
                    f"and wind speed is {wind_speed} km/h."
                )
                _log(msg, player)

                if session_memory:
                    try:
                        session_memory.set_last_search(query=search_query, response=msg)
                    except Exception:
                        pass

                return msg
            else:
                _log(f"wttr.in returned status code {response.status_code}. Falling back to browser.", player)
        except Exception as e:
            _log(f"Could not fetch live weather ({e}). Falling back to browser.", player)

    # Browser Fallback
    try:
        opened = webbrowser.open(google_url)
        if not opened:
            raise RuntimeError("webbrowser.open returned False")
    except Exception as e:
        msg = f"Sir, I couldn't open the browser for the weather report: {e}"
        _log(msg, player)
        return msg

    msg = f"Showing the weather for {city}, {when} in your browser, sir."
    _log(msg, player)

    if session_memory:
        try:
            session_memory.set_last_search(query=search_query, response=msg)
        except Exception:
            pass

    return msg


def _log(message: str, player=None) -> None:
    print(f"[Weather] {message}")
    if player:
        try:
            player.write_log(f"JARVIS: {message}")
        except Exception:
            pass