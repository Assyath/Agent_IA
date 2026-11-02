from tools.boutique import CATALOGUE
import re
import json
from pydantic_ai.messages import (
    ToolCallPart,
    ToolReturnPart,
    ModelRequest,
    ModelResponse
)

def verifier_calcul_commande(
    produit_id: str,
    quantite: int,
    zone: str,
    montant_articles_annonce: float,
    frais_livraison_annonces: float,
    total_annonce: float
) -> dict:
    """
    Vérifie les montants annoncés par l'agent vendeur.
    Les montants attendus sont recalculés à partir du catalogue.
    """

    erreurs = []

    # Vérifier le produit
    produit = CATALOGUE.get(produit_id.strip().lower())

    if produit is None:
        return {
            "valide": False,
            "erreurs": ["Produit introuvable dans le catalogue."]
        }

    # Vérifier la quantité
    if isinstance(quantite, bool) or not isinstance(quantite, int) or quantite <= 0:
        return {
            "valide": False,
            "erreurs": ["Quantité invalide."]
        }

    # Recalculer le montant des articles
    montant_attendu = produit["prix"] * quantite

    # Recalculer les frais de livraison
    zone_clean = zone.lower().strip()

    if "cotonou" in zone_clean:
        livraison_attendue = 1000
    elif "calavi" in zone_clean:
        livraison_attendue = 2000
    elif "porto" in zone_clean:
        livraison_attendue = 1500
    else:
        livraison_attendue = 5000

    # Recalculer le total
    total_attendu = montant_attendu + livraison_attendue

    # Comparer les montants annoncés
    if montant_articles_annonce != montant_attendu:
        erreurs.append("Le montant des articles est incorrect.")

    if frais_livraison_annonces != livraison_attendue:
        erreurs.append("Les frais de livraison sont incorrects.")

    if total_annonce != total_attendu:
        erreurs.append("Le montant total est incorrect.")

    return {
        "valide": len(erreurs) == 0,
        "montant_articles_attendu": montant_attendu,
        "frais_livraison_attendus": livraison_attendue,
        "total_attendu": total_attendu,
        "erreurs": erreurs
    }

def verifier_calcul_depuis_messages(messages, reponse):

    appels = {}
    resultats = {}

    # Récupérer les appels et résultats des outils
    for message in messages:
        for part in message.parts:

            if isinstance(part, ToolCallPart):
                appels[part.tool_name] = part.args_as_dict()

            elif isinstance(part, ToolReturnPart):
                if part.outcome == "success":
                    resultats[part.tool_name] = str(part.content)

    # Vérifier que les outils nécessaires ont fonctionné
    if "verifier_stock" not in resultats:
        return {
            "verifiable": False,
            "raison": "Vérification du stock absente."
        }

    if "calculer_livraison" not in resultats:
        return {
            "verifiable": False,
            "raison": "Calcul de livraison absent."
        }

    produit_id = appels.get("verifier_stock", {}).get("produit_id")
    zone = appels.get("calculer_livraison", {}).get("zone")

    if not produit_id or not zone:
        return {
            "verifiable": False,
            "raison": "Informations du produit ou de la livraison manquantes."
        }

    # Extraire les montants de la réponse du vendeur
    def extraire_montant(libelles):

        for libelle in libelles:
            motif = rf"\*{{0,2}}{re.escape(libelle)}\*{{0,2}}\s*:\s*([\d\s\u00a0.,]+)\s*XOF"

            correspondance = re.search(
                motif,
                reponse,
                re.IGNORECASE
            )

            if correspondance:
                valeur = re.sub(r"\D", "", correspondance.group(1))
                return int(valeur)

        return None

    quantite_match = re.search(
        r"\*{0,2}Quantité(?: demandée)?\*{0,2}\s*:\s*(\d+)",
        reponse,
        re.IGNORECASE
    )  

    montant_articles = extraire_montant([
        "Montant total des articles",
        "Montant des articles"
    ])

    frais_livraison = extraire_montant([
        "Frais de livraison"
    ])

    total = extraire_montant([
        "Montant total à payer",
        "Total à payer"
    ])

    if not quantite_match or None in (
        montant_articles,
        frais_livraison,
        total
    ):
        return {
            "verifiable": False,
            "raison": "Les montants nécessaires ne sont pas tous présents dans la réponse."
        }

    # Lancer la vérification mathématique existante
    resultat = verifier_calcul_commande(
        produit_id=produit_id,
        quantite=int(quantite_match.group(1)),
        zone=zone,
        montant_articles_annonce=montant_articles,
        frais_livraison_annonces=frais_livraison,
        total_annonce=total
    )

    return {
        "verifiable": True,
        **resultat
    }



def verifier_calcul_equipe(messages, reponse):
    reponse = re.sub(r"[*_`]", "", reponse)

    appels_stock = []
    resultats_stock = []
    resultats_livraison = []
    zones_livraison = []

    # Récupérer les traces des spécialistes
    for message in messages:
        for part in message.parts:
            if not isinstance(part, ToolReturnPart):
                continue

            if part.outcome != "success":
                continue

            if part.tool_name not in (
                "consulter_vendeur",
                "consulter_logisticien"
            ):
                continue

            try:
                donnees = json.loads(str(part.content))
            except (json.JSONDecodeError, TypeError):
                continue

            for appel in donnees.get("appels_outils", []):
                if appel["outil"] == "verifier_stock":
                    appels_stock.append(appel["parametres"])

                elif appel["outil"] == "calculer_livraison":
                    zones_livraison.append(
                        appel["parametres"].get("zone")
                    )

            for resultat in donnees.get("resultats_outils", []):
                if resultat["outil"] == "verifier_stock":
                    resultats_stock.append(resultat["resultat"])

                elif resultat["outil"] == "calculer_livraison":
                    resultats_livraison.append(resultat["resultat"])

    # Vérifier la présence des traces
    if not appels_stock or not resultats_stock:
        return {
            "verifiable": False,
            "raison": "Vérification du stock absente."
        }

    if not zones_livraison or not resultats_livraison:
        return {
            "verifiable": False,
            "raison": "Calcul de livraison absent."
        }

    # Récupérer les quantités de chaque produit dans le devis
    quantites = re.findall(
        r"(?im)^\s*Quantité\s*:\s*(\d+)",
        reponse
    )

    quantites = [int(q) for q in quantites]

    if len(quantites) != len(appels_stock):
        return {
            "verifiable": False,
            "raison": (
                f"Nombre de quantités ({len(quantites)}) différent "
                f"du nombre de produits vérifiés ({len(appels_stock)})."
            )
        }

    # Calculer le montant attendu pour tous les produits
    montant_articles_attendu = 0
    quantite_totale = 0

    for appel, quantite in zip(appels_stock, quantites):
        produit_id = appel.get("produit_id")

        if not produit_id or produit_id not in CATALOGUE:
            return {
                "verifiable": False,
                "raison": f"Produit introuvable dans le catalogue : {produit_id}."
            }

        prix_unitaire = CATALOGUE[produit_id]["prix"]

        montant_articles_attendu += prix_unitaire * quantite
        quantite_totale += quantite

    # Extraire les montants du devis
    def extraire_montant(libelles):
        for libelle in libelles:
            motif = (
                rf"(?im)^\s*{re.escape(libelle)}"
                rf"\s*:\s*([\d\s\u00a0\u202f.,]+)\s*XOF"
            )

            correspondance = re.search(motif, reponse)

            if correspondance:
                valeur = re.sub(r"\D", "", correspondance.group(1))
                return int(valeur)

        return None

    montant_articles_annonce = extraire_montant([
        "Montant des articles",
        "Montant total des articles",
        "Montant articles",
        "Sous-total"
    ])

    frais_livraison_annonces = extraire_montant([
        "Frais de livraison",
        "Frais livraison"
    ])

    total_annonce = extraire_montant([
        "Montant total à payer",
        "Montant total",
        "Total à payer",
        "Total"
    ])

    # Extraire les frais de livraison retournés par le Logisticien
    resultat_livraison = str(resultats_livraison[-1])

    montants_livraison = re.findall(
        r"(\d[\d\s\u00a0\u202f.,]*)\s*XOF",
        resultat_livraison,
        re.IGNORECASE
    )

    if montants_livraison:
        frais_livraison_attendus = int(
            re.sub(r"\D", "", montants_livraison[-1])
        )
    else:
        frais_livraison_attendus = None

    # Vérification des extractions
    if None in (
        montant_articles_annonce,
        frais_livraison_annonces,
        total_annonce,
        frais_livraison_attendus
    ):
        return {
            "verifiable": False,
            "raison": (
                f"Extraction incomplète : quantité totale={quantite_totale}, "
                f"articles annoncés={montant_articles_annonce}, "
                f"livraison annoncée={frais_livraison_annonces}, "
                f"livraison outil={frais_livraison_attendus}, "
                f"total={total_annonce}."
            )
        }

    # Vérification mathématique
    erreurs = []

    if montant_articles_annonce != montant_articles_attendu:
        erreurs.append("Le montant des articles est incorrect.")

    if frais_livraison_annonces != frais_livraison_attendus:
        erreurs.append("Les frais de livraison ne correspondent pas au résultat du Logisticien.")

    total_attendu = (
        montant_articles_attendu + frais_livraison_attendus
    )

    if total_annonce != total_attendu:
        erreurs.append("Le montant total est incorrect.")

    return {
        "verifiable": True,
        "valide": len(erreurs) == 0,
        "quantite_totale": quantite_totale,
        "montant_articles_attendu": montant_articles_attendu,
        "montant_articles_annonce": montant_articles_annonce,
        "frais_livraison_attendus": frais_livraison_attendus,
        "frais_livraison_annonces": frais_livraison_annonces,
        "total_attendu": total_attendu,
        "total_annonce": total_annonce,
        "erreurs": erreurs
    }