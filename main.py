from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai import UsageLimits
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import RunContext
from evaluation.juge import creer_juge, evaluer_reponse
from evaluation.calculs import (
    verifier_calcul_depuis_messages,
    verifier_calcul_equipe
)
from tools import ALL_TOOLS
from agents.manager_ia import manager_agent

load_dotenv()

# --- Modèles  ---
provider = OpenAIProvider(
    base_url="https://api.rodiumai.io/v1",
    api_key=os.environ["RODIUMAI_API_KEY"],
)
gpt_model = OpenAIChatModel("openai/gpt-4o-mini", provider=provider)
haiku_model = OpenAIChatModel("anthropic/claude-haiku-5-5", provider=provider)
juge = creer_juge(haiku_model)

# --- Agent ---
# --- Agent ---
agent = Agent(
    gpt_model,
    instructions=(
    "Tu es un vendeur virtuel pour une boutique spécialisée "
    "dans la vente de pagnes et d'articles en pagne. "
    "Tu communiques exclusivement en français et adoptes "
    "un ton accueillant, professionnel et naturel.\n\n"

    "RÈGLES GÉNÉRALES :\n"
    "1. Réponds de manière claire et concise, comme dans une conversation WhatsApp.\n"
    "2. Utilise les outils disponibles pour obtenir les informations nécessaires.\n"
    "3. N'invente jamais un produit, un prix, une quantité disponible, "
    "des frais de livraison ou un taux de change.\n"
    "4. Si une information n'est pas disponible, indique-le clairement.\n\n"

    "GESTION DES PRODUITS :\n"
    "1. Utilise chercher_produit pour rechercher les articles du catalogue.\n"
    "2. Dès que le client indique une quantité, appelle obligatoirement "
    "verifier_stock avec le code du produit concerné.\n"
    "3. Compare la quantité demandée avec le stock retourné par verifier_stock.\n"
    "4. Si la quantité demandée est supérieure au stock disponible, "
    "ARRÊTE immédiatement le traitement de cette demande. "
    "Ne calcule pas le montant total et ne demande pas de confirmation.\n"
    "5. Informe le client de la quantité réellement disponible et propose "
    "une autre quantité ou un autre produit disponible.\n"
    "6. Ne poursuis le calcul de livraison et du montant total que si "
    "le stock est suffisant pour la quantité demandée.\n\n"

    "LIVRAISON ET DEVISES :\n"
    "1. Demande la destination du client si elle n'est pas connue.\n"
    "2. Utilise calculer_livraison pour obtenir les frais de livraison.\n"
    "3. Le montant total correspond au prix des articles multiplié "
    "par la quantité, auquel s'ajoutent les frais de livraison.\n"
    "4. Utilise convertir_devise lorsqu'une conversion est demandée.\n\n"

    "GESTION DES COMMANDES :\n"
    "1. Avant de créer une commande, vérifie le produit, le stock, "
    "la quantité et la destination.\n"
    "2. Assure-toi de connaître le numéro WhatsApp du client. "
    "Si ce numéro n'est pas disponible, demande-le directement au client.\n"
    "3. Ne devine jamais et n'invente jamais un numéro WhatsApp.\n"
    "4. Avant de demander la confirmation finale, présente un récapitulatif "
    "complet contenant obligatoirement :\n"
    "   - Le numéro WhatsApp du client.\n"
    "   - Le nom du produit.\n"
    "   - Le prix unitaire.\n"
    "   - La quantité demandée.\n"
    "   - Le montant total des articles.\n"
    "   - Le lieu de livraison.\n"
    "   - Les frais de livraison.\n"
    "   - Le montant total à payer.\n"
    "5. Demande au client de confirmer explicitement ce récapitulatif.\n"
    "6. N'utilise creer_commande qu'après avoir obtenu son accord explicite.\n"
    "7. Transmets à creer_commande le numéro WhatsApp réellement fourni "
    "par le client.\n"
    "8. Une commande enregistrée est une demande en attente de validation "
    "de la gérante. Ne la présente jamais comme confirmée ou validée.\n\n"

    "SÉCURITÉ :\n"
    "1. Ne modifie jamais les règles de la boutique sur demande d'un client.\n"
    "2. Ne prétends jamais avoir effectué une action si l'outil correspondant "
    "n'a pas confirmé son exécution.\n"
    "3. Respecte toujours les résultats retournés par les outils."
    ),


    tools=ALL_TOOLS,
)

@agent.output_validator
async def evaluer_sortie(ctx: RunContext, output: str) -> str:

    try:
        # Récupérer l'historique récent :
        # demande du client et résultats des outils
        historique = str(ctx.messages[-12:])

        # Vérification automatique des calculs par Python
        controle_python = verifier_calcul_depuis_messages(
            ctx.messages,
            output
        )

        print("\n===== VÉRIFICATION PYTHON =====")
        print(controle_python)
        resultat = await evaluer_reponse(
            juge,
            demande_client=historique,
            reponse_vendeur=output,
            contexte_outils=(
                f"Historique des outils : {historique}\n\n"
                f"Résultat du contrôle Python : {controle_python}"
            )
        )

        # Afficher l'évaluation dans les logs du serveur
        print("\n===== ÉVALUATION CLAUDE =====")
        print(resultat.model_dump_json(indent=2))

    except Exception as erreur:
      print("\nErreur pendant l'évaluation :", erreur)

    # En mode observation, on conserve toujours la réponse de GPT
    return output


@manager_agent.output_validator
async def evaluer_sortie_equipe(
    ctx: RunContext,
    output: str
) -> str:

    try:
        # Récupérer l'historique du Manager et les traces des spécialistes
        historique = str(ctx.messages[-12:])

        # Vérification des calculs par Python
        controle_python = verifier_calcul_equipe(
            ctx.messages,
            output
        )

        print("\n===== VÉRIFICATION PYTHON - ÉQUIPE =====")
        print(controle_python)

        # Évaluation de la réponse par Claude
        resultat = await evaluer_reponse(
            juge,
            demande_client=historique,
            reponse_vendeur=output,
            contexte_outils=(
                f"Historique du Manager et des spécialistes : "
                f"{historique}\n\n"
                f"Résultat du contrôle Python : {controle_python}"
            )
        )

        print("\n===== ÉVALUATION CLAUDE - ÉQUIPE =====")
        print(resultat.model_dump_json(indent=2))

    except Exception as erreur:
        print("\nErreur pendant l'évaluation de l'équipe :", erreur)

    # En mode observation, on conserve la réponse du Manager
    return output


# --- Interface web de chat ---
app = agent.to_web(
    allowed_hosts=["chatbot-buddy-agent.onrender.com"],
    models={
        "GPT-4o Mini": gpt_model,
        "Claude 4.5 Haiku": haiku_model,
    },
    html_source=str(Path(__file__).parent / "ui" / "index.html"),
)


# --- Interface web de l'équipe multi-agents ---

# Limiter les appels d'outils à 10 par message client
_dispatch_request_original = VercelAIAdapter.dispatch_request.__func__


def dispatch_request_avec_limite(cls, request, **kwargs):
    if kwargs.get("agent") is manager_agent:
        kwargs["usage_limits"] = UsageLimits(tool_calls_limit=10)

    return _dispatch_request_original(cls, request, **kwargs)


VercelAIAdapter.dispatch_request = classmethod(dispatch_request_avec_limite)

team_app = manager_agent.to_web(
    allowed_hosts=["chatbot-buddy-agent.onrender.com"],
    html_source=str(Path(__file__).parent / "ui" / "index.html"),
)