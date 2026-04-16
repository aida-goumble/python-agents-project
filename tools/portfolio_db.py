import os
from datetime import date

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import yfinance as yf


def _get_dsn() -> str | None:
    return os.getenv("DATABASE_URL")


def lire_positions_portefeuille(_: str = "") -> str:
    """Retourne les positions du portefeuille depuis PostgreSQL."""
    dsn = _get_dsn()
    if not dsn:
        return "Erreur : DATABASE_URL manquant (base de données non configurée)."

    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT symbol, quantity, avg_cost FROM portfolio_positions ORDER BY symbol;"
                )
                rows = cur.fetchall()

        if not rows:
            return "Aucune position en base."

        lines = ["Positions (DB) :"]
        compact = []
        for r in rows:
            sym = r["symbol"]
            qty = float(r["quantity"])
            avg = r.get("avg_cost")
            if avg is not None:
                lines.append(f"  - {sym}: {qty:g} (PRU {float(avg):.2f}$)")
            else:
                lines.append(f"  - {sym}: {qty:g}")
            compact.append(f"{sym}:{qty:g}")

        lines.append("")
        lines.append("Format outil portefeuille : " + "|".join(compact))
        return "\n".join(lines)

    except Exception as e:
        return f"Erreur base de données : {e}"


def _upsert_market_history(symbol: str, hist) -> None:
    dsn = _get_dsn()
    if not dsn:
        return

    rows = []
    for idx, row in hist.iterrows():
        day = idx.date() if hasattr(idx, "date") else None
        if day is None:
            continue
        close = float(row["Close"])
        volume = None
        try:
            volume = int(row.get("Volume", None))
        except Exception:
            volume = None
        rows.append((symbol, day, close, volume))

    if not rows:
        return

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO market_history (symbol, day, close, volume)
                VALUES %s
                ON CONFLICT (symbol, day) DO UPDATE SET
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume;
                """,
                rows,
            )


def actifs_les_plus_risques(input_str: str = "") -> str:
    """
    Classe les actifs du portefeuille par risque (volatilité des rendements journaliers).

    Entrée : "jours" (optionnel) ex "60".
    """
    days = 60
    if input_str and input_str.strip():
        try:
            days = int(input_str.strip())
        except Exception:
            return f"Paramètre invalide '{input_str}'. Attendu un nombre de jours (ex 60)."
    days = max(10, min(days, 365))

    dsn = _get_dsn()
    if not dsn:
        return "Erreur : DATABASE_URL manquant (base de données non configurée)."

    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT symbol, quantity FROM portfolio_positions ORDER BY symbol;")
                positions = cur.fetchall()

        if not positions:
            return "Aucune position en base."

        symbols = [p["symbol"].strip().upper() for p in positions]

        # Refresh cache
        for sym in symbols:
            hist = yf.Ticker(sym).history(period=f"{days + 10}d", interval="1d")
            if hist is None or getattr(hist, "empty", True):
                continue
            _upsert_market_history(sym, hist.tail(days + 5))

        # Compute vol 
        results = []
        with psycopg2.connect(dsn) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for sym in symbols:
                    cur.execute(
                        """
                        SELECT day, close
                        FROM market_history
                        WHERE symbol = %s
                        ORDER BY day DESC
                        LIMIT %s;
                        """,
                        (sym, days),
                    )
                    rows = list(reversed(cur.fetchall()))
                    closes = [float(r["close"]) for r in rows if r.get("close") is not None]
                    if len(closes) < 5:
                        continue

                    # Daily returns
                    rets = []
                    for i in range(1, len(closes)):
                        prev = closes[i - 1]
                        cur_close = closes[i]
                        if prev != 0:
                            rets.append((cur_close - prev) / prev)

                    if len(rets) < 4:
                        continue

                    mean = sum(rets) / len(rets)
                    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
                    vol = var ** 0.5
                    results.append((sym, vol))

        if not results:
            return "Impossible de calculer le risque (historique insuffisant / indisponible)."

        results.sort(key=lambda x: x[1], reverse=True)
        lines = [f"Actifs les plus risqués (volatilité sur ~{days}j) :"]
        for i, (sym, vol) in enumerate(results, 1):
            lines.append(f"  {i}. {sym} — volatilité: {vol*100:.2f}%")
        return "\n".join(lines)

    except Exception as e:
        return f"Erreur base de données : {e}"
