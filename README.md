# TP Projet — Agent LangChain

## Prérequis

- Python 3.10+
- Docker + docker compose (pour PostgreSQL)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

```bash
cp .env.example .env
# puis renseigner au moins OPENAI_API_KEY, et si besoin TAVILY_API_KEY
```

## Base de données (PostgreSQL)

Démarrer PostgreSQL :

```bash
docker compose up -d
```

Initialiser les tables et insérer les données :

```bash
python init_db.py
```

## Lancer en CLI

```bash
python main.py
```

## Interface Streamlit

```bash
streamlit run app.py
```

## API REST (FastAPI)

```bash
uvicorn api:app --reload
```

Exemple :

```bash
curl -X POST http://127.0.0.1:8000/api/agent/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Quels sont mes actifs les plus risqués ?"}'
```

## Notes

- `PythonREPLTool` est activé (exécution de code Python arbitraire).
