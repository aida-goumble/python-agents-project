import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from tools.api_publique import convertir_devise
from tools.calculs import (
    calculer_interets_composes,
    calculer_marge,
    calculer_mensualite_pret,
    calculer_tva,
)
from tools.database import rechercher_client, rechercher_produit
from tools.finance import obtenir_cours_action, obtenir_cours_crypto
from tools.portefeuille import calculer_portefeuille
from tools.portfolio_db import actifs_les_plus_risques, lire_positions_portefeuille
from tools.recommandation import recommander_produits
from tools.texte import extraire_mots_cles, formater_rapport, resumer_texte


def _tool_calculer_tva(prix_ht: float, taux_tva: float) -> str:
    return calculer_tva(f"{prix_ht},{taux_tva}")


def _tool_calculer_interets(capital: float, taux_annuel: float, annees: int) -> str:
    return calculer_interets_composes(f"{capital},{taux_annuel},{annees}")


def _tool_calculer_marge(prix_vente: float, cout_achat: float) -> str:
    return calculer_marge(f"{prix_vente},{cout_achat}")


def _tool_calculer_mensualite(capital: float, taux_annuel: float, duree_mois: int) -> str:
    return calculer_mensualite_pret(f"{capital},{taux_annuel},{duree_mois}")


def _tool_convertir_devise(montant: float, devise_source: str, devise_cible: str) -> str:
    return convertir_devise(f"{montant},{devise_source},{devise_cible}")


def _tool_recommander_produits(budget: float, categorie: str = "Toutes", type_compte: str = "Standard") -> str:
    return recommander_produits(f"{budget},{categorie},{type_compte}")


def _tool_calculer_portefeuille(positions: str) -> str:
    return calculer_portefeuille(positions)


def _tool_lire_positions_portefeuille() -> str:
    return lire_positions_portefeuille("")


def _tool_actifs_les_plus_risques(jours: int = 60) -> str:
    return actifs_les_plus_risques(str(jours))


def construire_tools(allow_python_repl: bool | None = None):
    from langchain_core.tools import StructuredTool  # type: ignore

    tools = [
        # ── Outil 1 : Base de données ────────────────────────────────
        StructuredTool.from_function(
            rechercher_client,
            name="rechercher_client",
            description="Recherche un client par nom ou ID (ex: C001).",
        ),
        StructuredTool.from_function(
            rechercher_produit,
            name="rechercher_produit",
            description="Recherche un produit par nom ou ID.",
        ),
        # ── Outil 2 : Données financières ───────────────────────────
        StructuredTool.from_function(
            obtenir_cours_action,
            name="cours_action",
            description="Cours boursier d'une action (symbole ex AAPL, MSFT).",
        ),
        StructuredTool.from_function(
            obtenir_cours_crypto,
            name="cours_crypto",
            description="Cours d'une crypto (symbole ex BTC, ETH).",
        ),
        # ── Outil 3 : Calculs financiers ────────────────────────────
        StructuredTool.from_function(
            _tool_calculer_tva,
            name="calculer_tva",
            description="Calcule TVA et prix TTC.",
        ),
        StructuredTool.from_function(
            _tool_calculer_interets,
            name="calculer_interets",
            description="Intérêts composés.",
        ),
        StructuredTool.from_function(
            _tool_calculer_marge,
            name="calculer_marge",
            description="Marge commerciale.",
        ),
        StructuredTool.from_function(
            _tool_calculer_mensualite,
            name="calculer_mensualite",
            description="Mensualité de prêt.",
        ),
        # ── Outil 4 : API publique ──────────────────────────────────
        StructuredTool.from_function(
            _tool_convertir_devise,
            name="convertir_devise",
            description="Conversion de devises (API Frankfurter).",
        ),
        # ── Outil 5 : Texte ─────────────────────────────────────────
        StructuredTool.from_function(
            resumer_texte,
            name="resumer_texte",
            description="Résume un texte et donne des statistiques.",
        ),
        StructuredTool.from_function(
            extraire_mots_cles,
            name="extraire_mots_cles",
            description="Extrait les mots-clés d'un texte.",
        ),
        StructuredTool.from_function(
            formater_rapport,
            name="formater_rapport",
            description="Formate en rapport (Cle1:Val1|Cle2:Val2).",
        ),
        # ── Outil 6 : Recommandation ────────────────────────────────
        StructuredTool.from_function(
            _tool_recommander_produits,
            name="recommander_produits",
            description="Recommande des produits selon budget / catégorie / type de compte.",
        ),
        # ── Outil 7 : Portefeuille (B1) ─────────────────────────────
        StructuredTool.from_function(
            _tool_calculer_portefeuille,
            name="calculer_portefeuille",
            description="Calcule la valeur d'un portefeuille (positions: 'AAPL:2|MSFT:1').",
        ),
        # ── Outil D1 : DB portefeuille ─────────────────────────────
        StructuredTool.from_function(
            _tool_lire_positions_portefeuille,
            name="lire_positions_portefeuille",
            description="Lit les positions depuis PostgreSQL.",
        ),
        StructuredTool.from_function(
            _tool_actifs_les_plus_risques,
            name="actifs_les_plus_risques",
            description="Classe les actifs du portefeuille par risque (volatilité).",
        ),
    ]

    # ── Outil A3 : Recherche web (Tavily) ───────────────────────────
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults  # type: ignore

        if os.getenv("TAVILY_API_KEY"):
            tools.append(
                TavilySearchResults(
                    k=5,
                    description=(
                        "Recherche web (Tavily) pour répondre à des questions ouvertes: "
                        "actualités financières, informations sur une entreprise, contexte récent."
                    ),
                )
            )
    except Exception:
        pass

    # pour python repl actif par defaut si il est pas nul dans le .env
    if allow_python_repl is None:
        allow_python_repl = True

    if allow_python_repl:
        try:
            from langchain_experimental.tools import PythonREPLTool 

            python_repl = PythonREPLTool()
            python_repl.description = (
                "Exécute du code Python pour des calculs complexes non couverts par les autres outils. "
                "Entrée : code Python valide sous forme de chaîne."
            )
            tools.append(python_repl)
        except Exception:
            pass

    return tools


def _import_agent_bits():
    AgentExecutor = None
    create_openai_tools_agent = None

    for attempt in (
        ("langchain.agents", "AgentExecutor", "create_openai_tools_agent"),
        ("langchain_openai.agents", None, "create_openai_tools_agent"),
        ("langchain_classic.agents", "AgentExecutor", "create_openai_tools_agent"),
    ):
        module_name, exec_name, create_name = attempt
        try:
            module = __import__(module_name, fromlist=[n for n in (exec_name, create_name) if n])
            if exec_name:
                AgentExecutor = getattr(module, exec_name)
            create_openai_tools_agent = getattr(module, create_name)
            if AgentExecutor is not None and create_openai_tools_agent is not None:
                return AgentExecutor, create_openai_tools_agent
        except Exception:
            continue

    if AgentExecutor is None:
        from langchain_classic.agents import AgentExecutor as _AgentExecutor  

        AgentExecutor = _AgentExecutor

    if create_openai_tools_agent is None:
        raise ImportError("create_openai_tools_agent introuvable. Vérifier les dépendances LangChain.")

    return AgentExecutor, create_openai_tools_agent


def _import_memory():
    try:
        from langchain_classic.memory import ConversationBufferMemory 

        return ConversationBufferMemory
    except Exception:
        pass
    #fallback
    try:
        from langchain.memory import ConversationBufferMemory  

        return ConversationBufferMemory
    except Exception:
        pass

    raise ImportError("ConversationBufferMemory introuvable. Vérifier les dépendances LangChain.")


def _build_prompt():
    try:
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  

        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Tu es un assistant financier intelligent. Utilise les outils si nécessaire pour répondre aux questions.",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
    except Exception:
        from langchain_classic import hub  

        return hub.pull("hwchase17/openai-tools-agent")


def creer_agent(allow_python_repl: bool | None = None):
    """Crée et retourne un agent LangChain configuré avec mémoire (C2)."""
    load_dotenv()

    tools = construire_tools(allow_python_repl=allow_python_repl)

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    ConversationBufferMemory = _import_memory()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    AgentExecutor, create_openai_tools_agent = _import_agent_bits()
    prompt = _build_prompt()

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
    )

    return agent_executor


def interroger_agent(agent, question: str):
    """Envoie une question à l'agent et affiche la réponse finale."""
    print(f"\n{'='*60}")
    print(f"Question : {question}")
    print("=" * 60)
    result = agent.invoke({"input": question})
    print(f"\nRéponse finale : {result['output']}")
    return result
