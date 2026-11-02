# 🛍️ Chatbot IA – Assistant commercial pour une boutique de pagnes

## 1. Présentation du projet

Ce projet consiste à développer un assistant commercial basé sur l'intelligence artificielle, destiné à une boutique de vente de pagnes et à terme connecté à WhatsApp.

L'objectif est de permettre aux clients d'obtenir des informations sur les produits, de vérifier leur disponibilité, de calculer les frais de livraison et de préparer des commandes.

L'assistant doit également respecter plusieurs règles :
- Ne jamais inventer les prix, les quantités disponibles ou les frais de livraison.
- Vérifier les informations auprès des outils avant de les communiquer au client.
- Proposer une alternative lorsqu'un produit est indisponible.
- Calculer le montant total à partir du prix des articles et des frais de livraison.
- Ne jamais enregistrer une commande sans l'accord explicite du client.
- Soumettre chaque commande à la validation du responsable de la boutique.

Le projet est réalisé progressivement en trois paliers.

## 2. Technologies utilisées

- **Python** : langage de programmation.
- **Pydantic AI** : création et orchestration des agents IA.
- **RodiumAI** : accès aux modèles de langage.
- **Claude Haiku 4.5** : modèle utilisé pour l'équipe multi-agents.
- **GPT-4o Mini** : modèle utilisé pour l'agent simple de référence.
- **FastAPI / Uvicorn** : exécution de l'application web.
- **JSON** : stockage local du catalogue et des commandes.
- **Open Exchange Rates API (ExchangeRate-API)** : conversion de devises.
- **GitHub** : gestion et partage du code source.

## 3. Architecture du projet

Le projet comporte deux approches :

### 3.1. Architecture avec un agent simple

Un seul agent reçoit la demande du client, analyse son besoin et utilise directement les outils nécessaires pour lui répondre.

Il peut notamment :
- Rechercher un produit.
- Vérifier le stock.
- Calculer les frais de livraison.
- Convertir une devise.
- Préparer et enregistrer une commande selon les conditions définies.

Cette architecture permet de centraliser les responsabilités dans un seul agent.

### 3.2. Architecture multi-agents

Une deuxième architecture répartit les responsabilités entre plusieurs agents spécialisés.

Le Manager reçoit la demande du client et délègue les tâches aux spécialistes.

| Agent | Responsabilité |
|---|---|
| Manager | Comprend la demande, coordonne les spécialistes et gère le processus de commande. |
| Vendeur | Recherche les produits et vérifie leur disponibilité en stock. |
| Logisticien | Calcule les frais de livraison selon la zone. |
| Rédacteur | Prépare une réponse claire et adaptée au format WhatsApp. |

Le Manager centralise les informations obtenues et demande au Rédacteur de préparer la réponse finale.

## 4. Outils disponibles

Le projet dispose de cinq outils principaux :

| Outil | Fonction |
|---|---|
| `chercher_produit` | Recherche un produit dans le catalogue. |
| `verifier_stock` | Vérifie la disponibilité et récupère les informations de prix et de stock. |
| `calculer_livraison` | Calcule les frais de livraison selon la zone. |
| `convertir_devise` | Convertit un montant entre différentes devises à partir d'une API externe. |
| `creer_commande` | Enregistre une commande après vérification des conditions nécessaires. |

Un outil complémentaire, `valider_commande`, permet au responsable de confirmer ou de refuser une commande en attente.

## 5. Organisation des fichiers

```text
project/
│
├── main.py
├── modeles.py
├── manager.py
├── boutique_data.json
├── requirements.txt
│
├── tools/
│   ├── __init__.py
│   └── boutique.py
│
├── evaluation/
│   ├── __init__.py
│   ├── calculs.py
│   └── juge.py
│
├── agents/
│   ├── __init__.py
│   ├── vendeur.py
│   ├── logisticien.py
│   ├── redacteur.py
│   └── manager_ia.py
│
├── ui/
│   └── index.html
│
└── trace_execution_palier2.txt
```

### Description des principaux fichiers

- `main.py` : initialise les applications et les agents.
- `modeles.py` : configure les modèles de langage.
- `manager.py` : contient les éléments liés à la gestion du projet.
- `boutique_data.json` : contient les données du catalogue et les commandes.
- `tools/boutique.py` : regroupe les outils de la boutique.
- `evaluation/calculs.py` : effectue les vérifications mathématiques.
- `evaluation/juge.py` : évalue la qualité des réponses.
- `agents/` : contient les différents agents spécialisés.
- `ui/index.html` : définit l'interface web.
- `trace_execution_palier2.txt` : présente une trace réelle d'exécution de l'équipe multi-agents.

## 6. Palier 1 – Création de l'agent commercial

Le premier palier consiste à mettre en place un agent commercial capable de répondre aux demandes des clients en utilisant les outils de la boutique.

### Travaux réalisés

- Définition du rôle et des consignes de l'agent.
- Mise en place des cinq outils principaux.
- Vérification des informations avant leur communication au client.
- Enchaînement autonome de plusieurs appels d'outils.
- Mise en place d'une limite de 10 appels d'outils par demande pour l'architecture multi-agents.
- Affichage des appels d'outils et de leurs résultats dans l'interface.

### Résultat

L'agent est capable d'enchaîner plusieurs opérations pour traiter une demande, notamment rechercher un produit, vérifier son stock et calculer les frais de livraison.

## 7. Palier 2 – Évaluation et architecture multi-agents

Le deuxième palier vise à améliorer l'organisation de l'agent et à mettre en place des mécanismes de contrôle.

### 7.1. Validation humaine

Une commande ne peut pas être enregistrée sans l'accord explicite du client.

Après son enregistrement, elle reste en attente de validation du responsable de la boutique.

Le responsable peut accepter ou refuser la commande.

Le stock est vérifié une nouvelle fois avant l'acceptation et n'est déduit qu'après validation.

### 7.2. Stockage des données

Les informations du catalogue et les commandes sont conservées dans un fichier JSON.

Cela permet de retrouver les produits, leurs prix, les quantités disponibles et les commandes enregistrées.

### 7.3. Évaluation des réponses

Deux mécanismes de contrôle ont été mis en place :

- **Contrôle Python :** vérification des montants des articles, des frais de livraison et du total à payer.
- **Évaluation par un modèle IA :** utilisation d'un évaluateur pour examiner la qualité et la pertinence des réponses.

Le contrôle Python fonctionne sur les cas testés avec un seul produit. L'extraction des informations pour certains devis comportant plusieurs produits reste perfectible.

### 7.4. Équipe multi-agents

Le Manager délègue les tâches aux trois spécialistes : Vendeur, Logisticien et Rédacteur.

Cette organisation permet de séparer les responsabilités et de structurer le traitement des demandes.

### 7.5. Trace d'exécution

Une trace d'exécution est disponible dans le fichier :

`trace_execution_palier2.txt`

Elle présente un scénario de demande client portant sur deux produits :
- Recherche et vérification des produits par le Vendeur.
- Calcul des frais de livraison par le Logisticien.
- Préparation du devis par le Rédacteur.
- Transmission de la réponse finale par le Manager.

Cette trace permet d'observer l'enchaînement des interventions des agents et les résultats obtenus.

### 7.6. Comparaison entre les deux architectures

Les tests réalisés ont permis d'observer les différences suivantes :

| Critère | Agent simple – GPT-4o Mini | Équipe multi-agents – Claude Haiku 4.5 |
|---|---|---|
| Organisation | Un seul agent centralise les tâches. | Les responsabilités sont réparties entre plusieurs agents. |
| Utilisation des outils | Appels directs aux outils. | Délégation aux agents spécialisés. |
| Coût en crédits RodiumAI | Plus faible. | Plus élevé. |
| Rapidité | Légèrement plus rapide. | Temps de réponse proche de l'agent simple. |
| Complexité | Architecture plus simple. | Architecture plus complexe. |
| Modularité | Responsabilités centralisées. | Responsabilités séparées par spécialité. |

**Analyse :**

L'agent simple présente un avantage en matière de consommation de crédits et de simplicité. Il peut également être légèrement plus rapide.

L'équipe multi-agents offre une meilleure séparation des responsabilités et une architecture plus modulaire. Toutefois, elle nécessite davantage d'échanges entre les agents et entraîne une consommation plus importante de crédits RodiumAI.

**Conclusion du palier 2 :**

Pour le cas d'utilisation de cette boutique, l'agent simple est plus intéressant si l'on privilégie la simplicité, la rapidité et la maîtrise des coûts.

L'architecture multi-agents reste intéressante pour expérimenter une organisation plus structurée et faciliter l'évolution du projet.

## 8. Palier 3 – Intégration WhatsApp et déploiement

Ce dernier palier a pour objectif de rendre l'assistant accessible aux clients depuis WhatsApp.

### Travaux prévus

- Connexion d'un numéro WhatsApp de test à l'aide de Green API.
- Déploiement de l'agent sur Cloudflare Workers.
- Gestion des clés API à l'aide de secrets.
- Utilisation du stockage Cloudflare pour les données.
- Mise en place d'un webhook pour recevoir les messages des clients et leur envoyer les réponses de l'agent.
- Gestion des doublons afin d'éviter le traitement répété d'un même message.
- Réponse immédiate au webhook.
- Mise en place de protections contre les tentatives de manipulation de l'agent.
- Validation des commandes par le responsable directement depuis WhatsApp.

### Résultat attendu

Un client doit pouvoir échanger avec l'assistant depuis WhatsApp, obtenir des informations sur les produits, préparer une commande et attendre la validation du responsable depuis son téléphone.

**Cette partie sera complétée après la réalisation des travaux du Palier 3.**

## 9. Configuration et lancement du projet

### Prérequis

- Python installé.
- Un environnement virtuel Python.
- Une clé API RodiumAI.
- Les dépendances du projet.

### Installation

Cloner le dépôt :

```bash
git clone https://github.com/Assyath/Agent_IA.git
cd Chatbot
```

Créer un environnement virtuel :

```bash
python3 -m venv venv
```

Activer l'environnement :

```bash
source venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Créer un fichier `.env` à la racine du projet et y ajouter la clé API :

```env
RODIUMAI_API_KEY=votre_cle_api
```

Ne jamais publier ce fichier ou exposer une clé API dans le dépôt GitHub.

### Lancement

L'application multi-agents peut être lancée avec Uvicorn :

```bash
uvicorn main:team_app --reload
```

## 10. Perspectives d'amélioration

Plusieurs améliorations pourront être apportées au projet :

- Améliorer l'extraction des données des devis comportant plusieurs produits.
- Renforcer les mécanismes de validation des réponses.
- Améliorer la gestion des erreurs et des demandes incomplètes.
- Finaliser l'intégration WhatsApp.
- Renforcer la sécurité et la gestion des commandes.
- Améliorer le suivi des commandes et la persistance des données.

## 11. Auteur

Projet réalisé dans le cadre du Bootcamp RodiumAI.

**GitHub :** [Assyath/Chatbot](https://github.com/Assyath/Chatbot)