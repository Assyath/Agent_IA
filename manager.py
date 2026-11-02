from tools.boutique import COMMANDES, valider_commande


def afficher_commandes_en_attente():

    commandes = [
        commande for commande in COMMANDES
        if commande["statut"] == "En attente de validation de la gérante"
    ]

    if not commandes:
        print("\nAucune commande en attente.")
        return

    print("\n===== COMMANDES EN ATTENTE =====")

    for commande in commandes:
        print("\nIdentifiant :", commande["id"])
        print("Client :", commande["client"])
        print("Produit :", commande["produit"])
        print("Quantité :", commande["quantite"])
        print("Destination :", commande["zone"])
        print("Total :", commande["total"], "XOF")

    print("\n================================")


def menu_gerante():

    while True:

        print("\n===== ESPACE GÉRANTE =====")
        print("1. Consulter les commandes en attente")
        print("2. Traiter une commande")
        print("3. Quitter")

        choix = input("\nVotre choix : ").strip()

        if choix == "1":
            afficher_commandes_en_attente()

        elif choix == "2":

            afficher_commandes_en_attente()

            commande_id = input(
                "\nIdentifiant de la commande : "
            ).strip().upper()

            decision = input(
                "Accepter (A) ou refuser (R) ? "
            ).strip().lower()

            if decision == "a":
                resultat = valider_commande(commande_id, "accepter")
                print("\n", resultat)

            elif decision == "r":
                resultat = valider_commande(commande_id, "refuser")
                print("\n", resultat)

            else:
                print("\nChoix invalide.")

        elif choix == "3":
            print("\nFermeture de l'espace gérante.")
            break

        else:
            print("\nChoix invalide.")


if __name__ == "__main__":
    menu_gerante()