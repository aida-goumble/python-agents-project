import os
from datetime import date

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv


CLIENTS = {
    "C001": {
        "nom": "Marie Dupont",
        "email": "marie.dupont@email.fr",
        "ville": "Paris",
        "solde_compte": 15420.50,
        "type_compte": "Premium",
        "date_inscription": "2021-03-15",
        "achats_total": 8750.00,
    },
    "C002": {"nom": "Jean Martin", "solde_compte": 3200.00, "type_compte": "Standard"},
    "C003": {"nom": "Sophie Bernard", "solde_compte": 28900.00, "type_compte": "VIP"},
    "C004": {"nom": "Lucas Petit", "solde_compte": 750.00, "type_compte": "Standard"},
}

PRODUITS = {
    "P001": {"nom": "Ordinateur portable Pro", "prix_ht": 899.00, "stock": 45},
    "P002": {"nom": "Souris ergonomique", "prix_ht": 49.90, "stock": 120},
    "P003": {"nom": "Bureau réglable", "prix_ht": 350.00, "stock": 18},
    "P004": {"nom": "Casque audio sans fil", "prix_ht": 129.00, "stock": 67},
    "P005": {"nom": "Écran 27 pouces 4K", "prix_ht": 549.00, "stock": 30},
}

SEED_POSITIONS = [
    # symbol, quantity, avg_cost (optional)
    ("AAPL", 5, 170.0),
    ("MSFT", 2, 380.0),
    ("GOOGL", 3, 150.0),
]


def _parse_iso_date(s: str | None) -> date | None:
    if not s:
        return None
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def main() -> None:
    load_dotenv()
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL manquant. Copiez .env.example -> .env et renseigne DATABASE_URL")

    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                # A1 tables
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS clients (
                        id TEXT PRIMARY KEY,
                        nom TEXT NOT NULL,
                        email TEXT,
                        ville TEXT,
                        solde_compte NUMERIC NOT NULL DEFAULT 0,
                        type_compte TEXT NOT NULL,
                        date_inscription DATE,
                        achats_total NUMERIC
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS produits (
                        id TEXT PRIMARY KEY,
                        nom TEXT NOT NULL,
                        prix_ht NUMERIC NOT NULL,
                        stock INTEGER NOT NULL DEFAULT 0
                    );
                    """
                )

                # D1 tables
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS portfolio_positions (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        quantity NUMERIC NOT NULL,
                        avg_cost NUMERIC
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS market_history (
                        symbol TEXT NOT NULL,
                        day DATE NOT NULL,
                        close NUMERIC NOT NULL,
                        volume BIGINT,
                        PRIMARY KEY(symbol, day)
                    );
                    """
                )

                # Seed clients
                client_rows = []
                for cid, c in CLIENTS.items():
                    client_rows.append(
                        (
                            cid,
                            c.get("nom"),
                            c.get("email"),
                            c.get("ville"),
                            float(c.get("solde_compte", 0.0)),
                            c.get("type_compte"),
                            _parse_iso_date(c.get("date_inscription")),
                            float(c.get("achats_total", 0.0)) if c.get("achats_total") is not None else None,
                        )
                    )

                execute_values(
                    cur,
                    """
                    INSERT INTO clients (id, nom, email, ville, solde_compte, type_compte, date_inscription, achats_total)
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        nom = EXCLUDED.nom,
                        email = EXCLUDED.email,
                        ville = EXCLUDED.ville,
                        solde_compte = EXCLUDED.solde_compte,
                        type_compte = EXCLUDED.type_compte,
                        date_inscription = EXCLUDED.date_inscription,
                        achats_total = EXCLUDED.achats_total;
                    """,
                    client_rows,
                )

                # Seed produits
                produit_rows = [(pid, p["nom"], float(p["prix_ht"]), int(p["stock"])) for pid, p in PRODUITS.items()]
                execute_values(
                    cur,
                    """
                    INSERT INTO produits (id, nom, prix_ht, stock)
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        nom = EXCLUDED.nom,
                        prix_ht = EXCLUDED.prix_ht,
                        stock = EXCLUDED.stock;
                    """,
                    produit_rows,
                )

                # Seed positions 
                cur.execute("DELETE FROM portfolio_positions;")
                execute_values(
                    cur,
                    "INSERT INTO portfolio_positions (symbol, quantity, avg_cost) VALUES %s;",
                    SEED_POSITIONS,
                )

    except psycopg2.OperationalError as e:
        raise SystemExit(
            "Impossible de se connecter à PostgreSQL.\n"
        ) from e

    print("OK: tables créées + données initiales insérées.")


if __name__ == "__main__":
    main()
