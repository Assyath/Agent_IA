from pydantic import BaseModel, Field
from pydantic_ai import Agent


# Structure de l'évaluation retournée par Claude
class EvaluationReponse(BaseModel):
    note: int = Field(ge=0, le=10)
    acceptable: bool
    points_positifs: list[str]
    problemes: list[str]
    commentaire: str


# Création du LLM juge
def creer_juge(modele):

    return Agent(
        modele,
        output_type=EvaluationReponse,
        instructions=(
            "Tu es un évaluateur indépendant chargé de contrôler "
            "les réponses d'un vendeur virtuel pour une boutique de pagnes.\n\n"

            "Évalue les réponses en respectant strictement les règles suivantes :\n\n"

            "1. EXACTITUDE : le vendeur ne doit jamais inventer les produits, "
            "les prix, les stocks, les frais de livraison ou les taux de change. "
            "Les informations chiffrées doivent provenir des outils.\n\n"

            "2. GESTION DU STOCK : lorsque le client précise une quantité, "
            "le vendeur doit vérifier le stock avant de proposer une commande. "
            "Si le stock est insuffisant, il doit le signaler et proposer une alternative.\n\n"

            "3. CALCUL : le total doit correspondre au montant des articles "
            "additionné aux frais de livraison.\n\n"

            "4. COMMANDE : le vendeur doit obtenir l'accord explicite du client "
            "avant de créer une commande. Une commande créée reste en attente "
            "jusqu'à la validation de la gérante.\n\n"

            "5. VALIDATION : le vendeur ne doit jamais présenter une commande "
            "comme confirmée avant l'accord de la gérante.\n\n"

            "6. COMMUNICATION : la réponse doit être claire, concise, accueillante "
            "et adaptée à une conversation WhatsApp.\n\n"

            "IMPORTANT :\n"
            "- Ne pénalise pas le vendeur pour des informations que le client "
            "n'a pas demandées et qui ne sont pas obligatoires.\n"
            "- Ne demande pas systématiquement les couleurs, modèles ou tailles "
            "si ces informations ne sont pas nécessaires à la demande.\n"
            "- Ne considère pas l'absence de délai de livraison comme une erreur "
            "si aucun délai n'est annoncé ou demandé.\n"
            "- La validation de la gérante intervient après l'accord du client "
            "et la création de la commande. Elle n'est donc pas nécessaire "
            "dans une simple réponse informative ou une proposition de prix.\n"
            "- Évalue la réponse en tenant compte de l'étape actuelle de la conversation.\n\n"

            "Attribue une note entière entre 0 et 10.\n"
            "Une erreur importante concernant les prix, le stock ou la validation "
            "d'une commande doit fortement réduire la note.\n"
            "Indique acceptable=True si la réponse respecte les règles applicables "
            "à cette étape, sinon acceptable=False.\n"
            "Justifie ton évaluation de manière concise."
        )
    )


# Évaluer une réponse
async def evaluer_reponse(
    juge,
    demande_client,
    reponse_vendeur,
    contexte_outils=""
):

    prompt = (
        f"DEMANDE DU CLIENT :\n{demande_client}\n\n"

        f"OUTILS UTILISÉS ET RÉSULTATS :\n"
        f"{contexte_outils}\n\n"

        f"RÉPONSE DU VENDEUR :\n{reponse_vendeur}\n\n"

        "Évalue maintenant la réponse du vendeur.\n\n"

        "IMPORTANT : utilise les résultats des outils pour vérifier "
        "les informations annoncées par le vendeur.\n"
        "Ne prétends pas qu'une vérification n'a pas été effectuée "
        "si les résultats des outils montrent le contraire.\n"
        "Ne déduis pas qu'un outil n'a pas été utilisé simplement "
        "parce que son utilisation n'est pas mentionnée dans la réponse finale."
    )

    resultat = await juge.run(prompt)

    return resultat.output