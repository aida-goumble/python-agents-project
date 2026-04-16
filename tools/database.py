import os

import psycopg2
from psycopg2.extras import RealDictCursor


def _get_dsn() -> str | None:
    return os.getenv("DATABASE_URL")


def _query_one(sql: str, params: tuple) -> dict | None:
    dsn = _get_dsn()
    if not dsn:
        return None

    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None


def rechercher_client(query: str) -> str:
    """Recherche un client par nom ou ID (ex: C001) via PostgreSQL."""
    query = (query or "").strip()
    if not query:
        return "Aucun client trouvé pour : ''"

    dsn = _get_dsn()
    if not dsn:
        return "Erreur : DATABASE_URL manquant (base de données non configurée)."

    try:
        # 1) recherche par ID 
        row = _query_one(
            "SELECT id, nom, solde_compte, type_compte FROM clients WHERE id = %s;",
            (query.upper(),),
        )
        if not row:
            # 2) recherche par nom 
            row = _query_one(
                """
                SELECT id, nom, solde_compte, type_compte
                FROM clients
                WHERE nom ILIKE %s
                ORDER BY id
                LIMIT 1;
                """,
                (f"%{query}%",),
            )

        if not row:
            return f"Aucun client trouvé pour : '{query}'"

        return (
            f"Client : {row['nom']} | Solde : {float(row['solde_compte']):.2f} € "
            f"| Type de compte : {row['type_compte']}"
        )
    except Exception as e:
        return f"Erreur base de données : {e}"


def rechercher_produit(query: str) -> str:
    """Recherche un produit par nom ou ID via PostgreSQL. Retourne prix HT, TVA, TTC, stock."""
    query = (query or "").strip()
    if not query:
        return "Aucun produit trouvé pour : ''"

    dsn = _get_dsn()
    if not dsn:
        return "Erreur : DATABASE_URL manquant (base de données non configurée)."

    try:
        row = _query_one(
            "SELECT id, nom, prix_ht, stock FROM produits WHERE id = %s;",
            (query.upper(),),
        )
        if not row:
            row = _query_one(
                """
                SELECT id, nom, prix_ht, stock
                FROM produits
                WHERE nom ILIKE %s
                ORDER BY id
                LIMIT 1;
                """,
                (f"%{query}%",),
            )

        if not row:
            return f"Aucun produit trouvé pour : '{query}'"

        prix_ht = float(row["prix_ht"])
        tva = prix_ht * 0.20
        prix_ttc = prix_ht + tva
        return (
            f"Produit : {row['nom']} | Prix HT : {prix_ht:.2f} € "
            f"| TVA : {tva:.2f} € | Prix TTC : {prix_ttc:.2f} € | Stock : {int(row['stock'])}"
        )
    except Exception as e:
        return f"Erreur base de données : {e}"


def lister_tous_les_clients(query: str = "") -> str:
    """Retourne la liste complète de tous les clients (PostgreSQL)."""
    dsn = _get_dsn()
    if not dsn:
        return "Erreur : DATABASE_URL manquant (base de données non configurée)."

    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, nom, type_compte, solde_compte FROM clients ORDER BY id;"
                )
                rows = cur.fetchall()

        result = "Liste des clients :\n"
        for r in rows:
            result += (
                f"  {r['id']} : {r['nom']} | {r['type_compte']} | Solde : {float(r['solde_compte']):.2f} €\n"
            )
        return result
    except Exception as e:
        return f"Erreur base de données : {e}"
