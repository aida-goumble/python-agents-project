import yfinance as yf


def calculer_portefeuille(input_str: str) -> str:
    """
    Calcule la valeur d'un portefeuille d'actions (yfinance).

    Entrée : "SYMBOLE:QUANTITE|SYMBOLE:QUANTITE"
    Exemple : "AAPL:2|MSFT:1"
    """
    raw = (input_str or "").strip()
    if not raw:
        return "Portefeuille vide."

    parts = [p.strip() for p in raw.split("|") if p.strip()]
    items: list[tuple[str, float]] = []
    for p in parts:
        if ":" not in p:
            return f"Format invalide: '{p}'. Attendu SYMBOLE:QUANTITE séparés par |"
        sym, qty = p.split(":", 1)
        sym = sym.strip().upper()
        try:
            q = float(qty.strip())
        except Exception:
            return f"Quantité invalide pour '{sym}': '{qty}'"
        if not sym:
            return "Symbole vide dans le portefeuille."
        items.append((sym, q))

    lines: list[str] = ["Portefeuille :"]
    total_today = 0.0
    total_prev = 0.0
    ok_count = 0

    for sym, qty in items:
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="2d", interval="1d")
            if hist is None or getattr(hist, "empty", True):
                lines.append(f"  - {sym}: données indisponibles")
                continue

            close_today = float(hist["Close"].iloc[-1])
            close_prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else close_today

            v_today = qty * close_today
            v_prev = qty * close_prev
            total_today += v_today
            total_prev += v_prev
            ok_count += 1

            if close_prev != 0:
                var_pct = ((close_today - close_prev) / close_prev) * 100
            else:
                var_pct = 0.0

            lines.append(
                f"  - {sym} x{qty:g} @ {close_today:.2f}$ = {v_today:,.2f}$ ({var_pct:+.2f}%)".replace(",", " ")
            )

        except Exception as e:
            lines.append(f"  - {sym}: erreur yfinance ({e})")

    if ok_count == 0:
        return "Aucune ligne exploitable (données marché indisponibles)."

    if total_prev != 0:
        global_var = ((total_today - total_prev) / total_prev) * 100
    else:
        global_var = 0.0

    lines.append("")
    lines.append(f"Total : {total_today:,.2f}$".replace(",", " "))
    lines.append(f"Variation globale (jour) : {global_var:+.2f}%")
    return "\n".join(lines)
