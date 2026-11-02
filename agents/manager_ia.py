
from pydantic_ai import Agent, RunContext
import json
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from modeles import gpt_model
from agents.vendeur import vendeur_agent
from agents.logisticien import logisticien_agent
from agents.redacteur import redacteur_agent
from tools.boutique import creer_commande

def formater_resultat_specialiste(resultat):
    appels = []
    resultats = []

    for message in resultat.all_messages():
        for part in message.parts:

            if isinstance(part, ToolCallPart):
                appels.append({
                    "outil": part.tool_name,
                    "parametres": part.args_as_dict()
                })

            elif isinstance(part, ToolReturnPart):
                if part.outcome == "success":
                    resultats.append({
                        "outil": part.tool_name,
                        "resultat": str(part.content)
                    })

    return json.dumps({
        "reponse": resultat.output,
        "appels_outils": appels,
        "resultats_outils": resultats
    }, ensure_ascii=False)

manager_agent = Agent(
    gpt_model,
    name="manager",
    instructions=(
        "Tu es le Manager IA d'une boutique spécialisée dans "
        "la vente de pagnes et d'articles en pagne.\n\n"

        "Ta mission est de coordonner les agents spécialisés "
        "pour répondre aux demandes des clients.\n\n"

        "ORGANISATION DU TRAVAIL :\n"
        "1. Analyse la demande du client.\n"
        "2. Lorsque la demande concerne un produit, sollicite "
        "le Vendeur IA pour rechercher le produit et vérifier le stock.\n"
        "3. Lorsque la demande concerne une livraison, sollicite "
        "le Logisticien IA pour calculer les frais.\n"
        "4. Ne considère jamais une information comme vérifiée "
        "si elle ne provient pas des outils ou des spécialistes.\n"
        "5. Rassemble les informations obtenues.\n"
        "6. Transmets les informations nécessaires au Rédacteur IA "
        "pour qu'il prépare la réponse finale.\n"
        "7. Retourne au client la réponse produite par le Rédacteur IA.\n\n"

        "RÈGLES IMPORTANTES :\n"
        "- Ne fabrique jamais de prix, de stock ou de frais de livraison.\n"
        "- Si le stock est insuffisant, ne poursuis pas le traitement "
        "comme si la quantité était disponible.\n"
        "- Ne demande pas au Rédacteur IA d'inventer les informations manquantes.\n"
        "- Ne valide jamais toi-même une commande.\n"
        "- Une commande nécessite l'accord du client puis la validation "
        "de la gérante.\n"
        "- Communique exclusivement en français."

        "GESTION DES COMMANDES :\n"
        "- Lorsqu'un client demande uniquement un prix ou un devis, ne crée aucune commande."
        "- Une commande ne peut être enregistrée qu'après un accord explicite du client."
        "- Avant d'appeler enregistrer_commande, tu dois disposer de toutes les informations suivantes :"
        "1. Le numéro WhatsApp du client."
        "2. Le code produit exact obtenu auprès du Vendeur IA."
        "3. La quantité demandée."
        "4. La destination de livraison."
        "5. L'accord explicite du client."
        "- Si une information manque, demande-la au client. Ne l'invente jamais."
        "- Après l'accord du client, appelle enregistrer_commande avec les informations vérifiées."
        "- Attends le résultat de l'outil avant d'annoncer que la commande est enregistrée."
        "- Si l'outil retourne une erreur, informe le client sans prétendre que la commande a été créée."
        "- Si l'enregistrement réussit, communique l'identifiant de la commande et son statut réel : en attente de validation de la gérante."
        "- Ne prétends jamais qu'une commande a été approuvée par la gérante sans confirmation effective."
        "- Demande ensuite au Rédacteur IA de formuler la réponse finale à partir du résultat réel de l'outil."
        "COMMUNICATION AVEC LE CLIENT :\n"
        "- Ne raconte jamais les étapes de ton travail.\n"
        "- Ne décris jamais les outils que tu vas utiliser ou que tu viens d'utiliser.\n"
        "- Ne dis pas « Je vais vérifier », « Laissez-moi rechercher », "
        "« Je prépare maintenant votre devis » ou toute phrase similaire.\n"
        "- Ne donne aucun message intermédiaire pour annoncer une action.\n"
        "- Effectue les recherches, vérifications et calculs nécessaires "
        "avant de rédiger ta réponse.\n"
        "- Lorsque toutes les informations sont disponibles, demande au "
        "Rédacteur de préparer une seule réponse complète.\n"
        "- Transmets au client uniquement cette réponse finale.\n"
        "- Reste naturel, professionnel et concis, comme un vendeur sur WhatsApp.\n"
    ),
)


# Délégation au Vendeur IA
@manager_agent.tool
async def consulter_vendeur(
    ctx: RunContext,
    demande: str,
) -> str:
    """Demande au Vendeur IA de rechercher un produit et de vérifier le stock."""

    resultat = await vendeur_agent.run(
        demande,
        usage=ctx.usage,
        usage_limits=ctx.usage_limits
    )

    return formater_resultat_specialiste(resultat)


# Délégation au Logisticien IA
@manager_agent.tool
async def consulter_logisticien(
    ctx: RunContext,
    demande: str,
) -> str:
    """Demande au Logisticien IA de calculer les frais de livraison."""

    resultat = await logisticien_agent.run(
        demande,
        usage=ctx.usage,
        usage_limits=ctx.usage_limits
    )

    return formater_resultat_specialiste(resultat)


# Délégation au Rédacteur IA
@manager_agent.tool
async def consulter_redacteur(
    ctx: RunContext,
    informations: str,
) -> str:
    """Demande au Rédacteur IA de composer la réponse finale au client."""

    resultat = await redacteur_agent.run(
        informations,
        usage=ctx.usage,
        usage_limits=ctx.usage_limits
    )

    return resultat.output

# Enregistrement d'une commande
@manager_agent.tool
async def enregistrer_commande(
    ctx: RunContext,
    client_whatsapp: str,
    produit_id: str,
    quantite: int,
    zone: str,
    accord_client: bool,
) -> str:
    """Enregistre une commande après accord explicite du client."""

    return creer_commande(
        client_whatsapp=client_whatsapp,
        produit_id=produit_id,
        quantite=quantite,
        zone=zone,
        accord_client=accord_client,
    )