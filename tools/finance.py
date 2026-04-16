import random

import yfinance as yf


CRYPTOS = {
    "BTC": {"nom": "Bitcoin", "prix_base": 67500.00},
    "ETH": {"nom": "Ethereum", "prix_base": 3200.00},
    "SOL": {"nom": "Solana", "prix_base": 175.00},
}


def obtenir_cours_action(symbole: str) -> str:
    """Retourne le cours réel d'une action (yfinance) + variation du jour + volume."""
    symbole = (symbole or "").strip().upper()
    if not symbole:
        return "Action '' non trouvée."

    try:
        ticker = yf.Ticker(symbole)
        hist = ticker.history(period="2d", interval="1d")
        if hist is None or getattr(hist, "empty", True):
            return f"Action '{symbole}' non trouvée."

        close_today = float(hist["Close"].iloc[-1])
        close_prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else close_today

        if close_prev != 0:
            variation_pct = ((close_today - close_prev) / close_prev) * 100
        else:
            variation_pct = 0.0

        volume = None
        if "Volume" in hist.columns and len(hist["Volume"]) > 0:
            try:
                volume = int(hist["Volume"].iloc[-1])
            except Exception:
                volume = None

        tendance = "📈" if variation_pct >= 0 else "📉"
        msg = f"{symbole} {tendance} : {close_today:.2f} $ ({variation_pct:+.2f}%)"
        if volume is not None:
            msg += f" | Volume: {volume:,}".replace(",", " ")
        return msg

    except Exception as e:
        return f"Erreur yfinance pour '{symbole}' : {e}"


def obtenir_cours_crypto(symbole: str) -> str:
    """Retourne le cours simulé d'une crypto avec sa variation (+/-3%)."""
    symbole = symbole.strip().upper()
    if symbole not in CRYPTOS:
        return f"Cryptos '{symbole}' non trouvée."
    crypto = CRYPTOS[symbole]
    variation_pct = random.uniform(-3.0, 3.0)  # Variation aléatoire
    cours = crypto["prix_base"] * (1 + variation_pct / 100)
    tendance = "📈" if variation_pct >= 0 else "📉"
    return f"{symbole} {tendance} : {cours:.2f} $ ({variation_pct:+.2f}%)"
