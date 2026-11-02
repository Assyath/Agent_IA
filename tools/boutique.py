
import httpx
import json
from pathlib import Path

# =====================================================
# 1. CHARGEMENT DES DONNÉES DE LA BOUTIQUE
# =====================================================

FICHIER_DONNEES = Path(__file__).parent.parent / "boutique_data.json"


def charger_donnees():
    """Charge le catalogue et les commandes depuis le fichier JSON."""

    with open(FICHIER_DONNEES, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


donnees = charger_donnees()

CATALOGUE = donnees["catalogue"]
COMMANDES = donnees["commandes"]

def sauvegarder_donnees():
    """Enregistre le catalogue et les commandes dans le fichier JSON."""

    donnees = {
        "catalogue": CATALOGUE,
        "commandes": COMMANDES
    }

    with open(FICHIER_DONNEES, "w", encoding="utf-8") as fichier:
        json.dump(donnees, fichier, ensure_ascii=False, indent=4)


# =====================================================
# 2. RECHERCHER UN PRODUIT
# =====================================================

def chercher_produit(mot_cle: str) -> str:
    """Recherche un produit dans le catalogue."""

    if not mot_cle or not mot_cle.strip():
        return "Veuillez préciser le nom du produit recherché."

    resultats = []

    for code, info in CATALOGUE.items():

        if mot_cle.lower().strip() in info["nom"].lower():
            disponibilite = (
                "Disponible"
                if info["stock"] > 0
                else "Rupture de stock"
            )

            resultats.append(
                f"Code : {code} | "
                f"Nom : {info['nom']} | "
                f"Prix : {info['prix']} XOF | "
                f"Disponibilité : {disponibilite}"
            )

    if resultats:
        return "\n".join(resultats)

    return "Aucun produit correspondant trouvé au marché Dantokpa."


# =====================================================
# 3. VÉRIFIER LE STOCK ET LE PRIX
# =====================================================

def verifier_stock(produit_id: str) -> str:
    """Vérifie le prix et la disponibilité d'un produit."""

    if not produit_id:
        return "Veuillez fournir un code produit."

    produit = CATALOGUE.get(produit_id.strip().lower())

    if produit is None:
        return "Code produit introuvable dans le système."

    if produit["stock"] > 0:
        disponibilite = f"{produit['stock']} pièce(s) disponible(s)."
    else:
        disponibilite = "Produit en rupture de stock."

    return (
        f"Produit : {produit['nom']} | "
        f"Prix unitaire : {produit['prix']} XOF | "
        f"Stock : {disponibilite}"
    )


# =====================================================
# 4. CALCULER LES FRAIS DE LIVRAISON
# =====================================================

def calculer_livraison(zone: str) -> str:
    """Calcule les frais de livraison selon la destination."""

    if not zone or not zone.strip():
        return "Veuillez préciser votre ville ou quartier."

    zone_clean = zone.lower().strip()

    if "cotonou" in zone_clean:
        frais = 1000

    elif "calavi" in zone_clean:
        frais = 2000

    elif "porto" in zone_clean:
        frais = 1500

    else:
        frais = 5000

    return f"Frais de livraison : {frais} XOF"


# =====================================================
# 5. CONVERTIR LES DEVISES AVEC EXCHANGE RATE API
# =====================================================

def convertir_devise(montant_xof: float, devise_cible: str) -> str:
    """
    Convertit un montant XOF vers une autre devise.
    Utilise ExchangeRate-API (endpoint Open Access).
    """

    devises_supportees = {"EUR", "USD", "CAD", "XOF"}

    if montant_xof < 0:
        return "Le montant ne peut pas être négatif."

    if not devise_cible:
        return "Veuillez préciser la devise cible."

    devise = devise_cible.strip().upper()

    if devise not in devises_supportees:
        return (
            f"Devise {devise} non autorisée. "
            "Devises disponibles : EUR, USD, CAD et XOF."
        )

    if devise == "XOF":
        return f"{montant_xof:.2f} XOF"

    # XOF est la devise de référence
    url = "https://open.er-api.com/v6/latest/XOF"

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

        if data.get("result") != "success":
            return "Impossible de récupérer les taux de change."

        taux = data.get("rates", {}).get(devise)

        if taux is None:
            return f"Le taux de change pour {devise} est indisponible."

        montant_converti = montant_xof * taux

        date_maj = data.get(
            "time_last_update_utc",
            "Date inconnue"
        )

        return (
            f"{montant_xof:.2f} XOF = "
            f"{montant_converti:.2f} {devise} | "
            f"Taux : {taux} | "
            f"Dernière mise à jour : {date_maj}"
        )

    except httpx.TimeoutException:
        return "Délai dépassé lors de la connexion à l'API."

    except httpx.HTTPStatusError as e:
        return f"Erreur HTTP de l'API : {e.response.status_code}"

    except httpx.RequestError:
        return "Impossible de contacter l'API des devises."

    except (ValueError, TypeError):
        return "Erreur lors du traitement des données de change."


# =====================================================
# 6. CRÉER UNE COMMANDE
# =====================================================


def creer_commande(
    client_whatsapp: str,
    produit_id: str,
    quantite: int,
    zone: str,
    accord_client: bool
) -> str:
    """
    Enregistre une demande de commande après accord du client.
    La commande reste en attente de validation de la gérante.
    """

    # 1. Vérifier le numéro WhatsApp
    if not client_whatsapp or not client_whatsapp.strip():
        return "Numéro WhatsApp du client manquant."

    # 2. Vérifier la quantité
    if isinstance(quantite, bool) or not isinstance(quantite, int) or quantite <= 0:
        return "La quantité doit être un entier positif."

    # 3. Vérifier le lieu de livraison
    if not zone or not zone.strip():
        return "Veuillez préciser le lieu de livraison."

    # 4. Vérifier l'accord du client
    if accord_client is not True:
        return "La commande ne peut pas être enregistrée sans l'accord du client."

    # 5. Vérifier le produit
    produit_id = produit_id.strip().lower()
    produit = CATALOGUE.get(produit_id)

    if produit is None:
        return "Code produit introuvable."

    # 6. Vérifier le stock
    if quantite > produit["stock"]:
        return (
            f"Stock insuffisant. "
            f"Seulement {produit['stock']} pièce(s) disponible(s)."
        )

    # 7. Calculer les frais de livraison
    zone_clean = zone.lower().strip()

    if "cotonou" in zone_clean:
        frais_livraison = 1000
    elif "calavi" in zone_clean:
        frais_livraison = 2000
    elif "porto" in zone_clean:
        frais_livraison = 1500
    else:
        frais_livraison = 5000

    # 8. Calculer le montant total
    montant_articles = produit["prix"] * quantite
    total = montant_articles + frais_livraison

    # 9. Générer un identifiant unique
    commande_id = f"CMD-{len(COMMANDES) + 1:04d}"
    
    # 10. Enregistrer la demande
    commande = {
        "id": commande_id,
        "client": client_whatsapp.strip(),
        "produit_id": produit_id,
        "produit": produit["nom"],
        "quantite": quantite,
        "zone": zone.strip(),
        "montant_articles": montant_articles,
        "frais_livraison": frais_livraison,
        "total": total,
        "statut": "En attente de validation de la gérante"
    }

    COMMANDES.append(commande)
    sauvegarder_donnees()

    return (
        "Demande de commande enregistrée !\n"
        f"Identifiant : {commande['id']}\n"
        f"Client : {commande['client']}\n"
        f"Produit : {commande['produit']}\n"
        f"Quantité : {quantite}\n"
        f"Destination : {commande['zone']}\n"
        f"Articles : {montant_articles} XOF\n"
        f"Livraison : {frais_livraison} XOF\n"
        f"Total : {total} XOF\n"
        f"Statut : {commande['statut']}"
    )

# =====================================================
# 7. VALIDER OU REFUSER UNE COMMANDE
# =====================================================

def valider_commande(commande_id: str, decision: str) -> str:
    """
    Permet à la gérante d'accepter ou de refuser une commande.
    Le stock est déduit uniquement en cas d'acceptation.
    """

    if not commande_id or not commande_id.strip():
        return "Veuillez fournir un identifiant de commande."

    decision = decision.strip().lower()

    if decision not in {"accepter", "refuser"}:
        return "Décision invalide. Choisissez 'accepter' ou 'refuser'."

    # Rechercher la commande
    commande = next(
        (c for c in COMMANDES if c["id"] == commande_id.strip()),
        None
    )

    if commande is None:
        return "Commande introuvable."

    # Vérifier que la commande est encore en attente
    if commande["statut"] != "En attente de validation de la gérante":
        return f"Cette commande a déjà été traitée : {commande['statut']}."

    produit = CATALOGUE[commande["produit_id"]]

    if decision == "accepter":

        # Vérifier une nouvelle fois le stock
        if commande["quantite"] > produit["stock"]:
            commande["statut"] = "Refusée - Stock insuffisant"
            sauvegarder_donnees()

            return (
                "Impossible d'accepter la commande.\n"
                "Le stock disponible est désormais insuffisant."
            )

        # Déduire le stock
        produit["stock"] -= commande["quantite"]

        commande["statut"] = "Acceptée - Commande confirmée"

        sauvegarder_donnees()

        return (
            f"Commande {commande_id} acceptée !\n"
            f"Client : {commande['client']}\n"
            f"Nouveau stock : {produit['stock']} pièce(s)."
        )

    # Refuser la commande
    commande["statut"] = "Refusée par la gérante"

    sauvegarder_donnees()

    return f"Commande {commande_id} refusée. Le stock reste inchangé."