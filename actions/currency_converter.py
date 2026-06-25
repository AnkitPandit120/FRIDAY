# actions/currency_converter.py
import requests

# Hardcoded fallback rates relative to USD in case API is offline / no internet
_FALLBACK_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "INR": 83.50,
    "JPY": 158.0,
    "CAD": 1.37,
    "AUD": 1.51,
    "TRY": 32.50,
    "CNY": 7.25,
    "CHF": 0.89,
}

def currency_converter(parameters: dict, player=None) -> str:
    """
    Performs real-time currency conversions or retrieves latest exchange rates.
    """
    action = parameters.get("action", "convert").lower().strip()
    
    if player:
        player.write_log(f"[Currency] Action: {action}")

    if action == "rates":
        base = parameters.get("from", "USD").upper().strip()
        try:
            url = f"https://open.er-api.com/v6/latest/{base}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                common_currencies = ["USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD", "TRY", "CNY", "CHF"]
                rates_lines = []
                for curr in common_currencies:
                    if curr in rates and curr != base:
                        rates_lines.append(f"  1 {base} = {rates[curr]:.4f} {curr}")
                rates_str = "\n".join(rates_lines)
                return f"Sir, current exchange rates relative to {base}:\n{rates_str}"
            else:
                raise RuntimeError(f"API returned status {response.status_code}")
        except Exception as e:
            # Fallback to local rates
            rates_lines = []
            # Calculate rates relative to the requested base currency from fallback table
            base_usd_rate = _FALLBACK_RATES.get(base)
            if not base_usd_rate:
                # If requested base is not in fallback list, use USD as base
                base = "USD"
                base_usd_rate = 1.0
            
            for curr, usd_rate in _FALLBACK_RATES.items():
                if curr != base:
                    # target rate relative to base = (target rate relative to USD) / (base rate relative to USD)
                    converted_rate = usd_rate / base_usd_rate
                    rates_lines.append(f"  1 {base} = {converted_rate:.4f} {curr} (Fallback)")
            rates_str = "\n".join(rates_lines)
            return (
                f"Sir, I couldn't reach the exchange rate API ({e}). "
                f"Here are the fallback exchange rates for {base}:\n{rates_str}"
            )

    elif action == "convert":
        amount_str = parameters.get("value", "1")
        try:
            amount = float(amount_str)
        except ValueError:
            return f"Sir, '{amount_str}' is not a valid numeric amount."

        from_curr = parameters.get("from", "USD").upper().strip()
        to_curr = parameters.get("to", "EUR").upper().strip()

        if from_curr == to_curr:
            return f"Sir, {amount:.2f} {from_curr} is equal to {amount:.2f} {to_curr}."

        try:
            # Attempt fetching live conversion
            url = f"https://open.er-api.com/v6/latest/{from_curr}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                if to_curr in rates:
                    converted = amount * rates[to_curr]
                    return f"Sir, {amount:.2f} {from_curr} is approximately {converted:.2f} {to_curr} (1 {from_curr} = {rates[to_curr]:.4f} {to_curr})."
                else:
                    raise KeyError(f"Target currency '{to_curr}' not found in API response.")
            else:
                raise RuntimeError(f"API status {response.status_code}")
        except Exception as e:
            # Fallback to local rates
            from_usd = _FALLBACK_RATES.get(from_curr)
            to_usd = _FALLBACK_RATES.get(to_curr)

            if not from_usd or not to_usd:
                missing = from_curr if not from_usd else to_curr
                return f"Sir, I couldn't fetch live rates and '{missing}' is not in my fallback rates database."

            # value in USD = amount / from_usd_rate
            # value in to_curr = value in USD * to_usd_rate
            converted = (amount / from_usd) * to_usd
            rate = to_usd / from_usd
            return (
                f"Sir, using offline rates database: "
                f"{amount:.2f} {from_curr} is approximately {converted:.2f} {to_curr} "
                f"(1 {from_curr} = {rate:.4f} {to_curr})."
            )

    else:
        return f"Unknown currency action: {action}"
