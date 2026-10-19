# 🔧 SmartGarage — Chatbot intelligent d'assistance et de maintenance automobile
 
![Rasa](https://img.shields.io/badge/Rasa-3.6.20-5A17EE?logo=rasa&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-Reverse%20Proxy-009639?logo=nginx&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?logo=amazonaws&logoColor=white)

 
**SmartGarage** est un chatbot conversationnel en français qui assiste les propriétaires de véhicules dans leurs opérations de maintenance courante : bilan d'entretien selon le kilométrage, interprétation des voyants du tableau de bord, estimation des coûts et informations pratiques sur le garage. L'application est conteneurisée avec Docker et déployée sur le cloud (AWS EC2).
 
---
 
## 📑 Sommaire
 
- [Objectifs](#-objectifs)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Technologies utilisées](#-technologies-utilisées)
- [Pipeline NLU](#-pipeline-nlu)
- [Intentions et entités](#-intentions-et-entités)
- [Structure du projet](#-structure-du-projet)
- [Installation et lancement](#-installation-et-lancement)
- [Déploiement sur AWS EC2](#-déploiement-sur-aws-ec2)
- [Exemples de conversations](#-exemples-de-conversations)
- [Tests et validation](#-tests-et-validation)
- [Limites et perspectives](#-limites-et-perspectives)
- [Auteur](#-auteur)
---
 
## 🎯 Objectifs
 
- Fournir une assistance automobile disponible 24h/24 et 7j/7.
- Aider les utilisateurs à diagnostiquer les problèmes courants.
- Conseiller les conducteurs sur la maintenance préventive.
- Réduire le temps de recherche d'informations techniques.
- Déployer la solution dans un environnement virtualisé et cloud.
## ✨ Fonctionnalités
 
| Fonctionnalité | Description |
| --- | --- |
| 💬 **Conversation naturelle** | Compréhension du français (variations de formulation, fautes de frappe), maintien du contexte, gestion du hors-sujet. |
| 🚗 **Collecte des infos véhicule** | Formulaire conversationnel guidé : marque, modèle, année (1900-2026) et kilométrage, avec validation et relance en cas de valeur invalide. |
| 🛠️ **Bilan de maintenance** | Calcul automatique des entretiens dus ou à venir selon le kilométrage. |
| 🚨 **Diagnostic des voyants** | Explication des voyants selon leur couleur (rouge, orange, jaune, bleu, vert), niveau d'urgence et actions à entreprendre. |
| 💶 **Estimation tarifaire** | Fourchette de prix indicative pour les principales interventions. |
| 📅 **Infos garage & rendez-vous** | Horaires, coordonnées, adresse et modalités de prise de rendez-vous. |
 
### Intervalles de maintenance gérés
 
| Intervention | Intervalle |
| --- | --- |
| Vidange d'huile | 10 000 km |
| Rotation des pneus | 10 000 km |
| Filtre à air | 15 000 km |
| Bougies d'allumage | 30 000 km |
| Plaquettes de frein | 40 000 km |
| Courroie de distribution | 60 000 km |
 
### Estimation des coûts (indicative)
 
| Intervention | Prix |
| --- | --- |
| Vidange | 60 – 120 € |
| Rotation des pneus | 20 – 40 € |
| Remplacement des plaquettes | 150 – 300 € |
| Remplacement de la batterie | 100 – 250 € |
| Révision complète | 250 – 500 € |
 
## 🏗️ Architecture
 
Le système repose sur une **architecture microservices** en trois couches communiquant via HTTP REST :

```
┌──────────────┐   HTTP    ┌──────────────────┐   HTTP    ┌───────────────────┐
│   Frontend   │ ────────► │      Nginx       │ ────────► │    Rasa Server    │
│ HTML/CSS/JS  │           │ reverse proxy :80│ /webhooks │   (NLU + Core)    │
└──────────────┘           └──────────────────┘           │      :5005        │
                                                          └─────────┬─────────┘
                                                                    │ POST /webhook
                                                          ┌─────────▼─────────┐
                                                          │   Action Server   │
                                                          │ (Python, rasa-sdk)│
                                                          │      :5055        │
                                                          └───────────────────┘
```
 
- **Couche présentation** : interface web (HTML/CSS/JS) qui appelle `/webhooks/rest/webhook`.
- **Couche traitement** :
  - **Rasa Server** (port 5005) : héberge le modèle NLU et le moteur de dialogue.
  - **Action Server** (port 5055) : exécute la logique métier Python (actions personnalisées).
- **Nginx** : sert les fichiers statiques et fait office de reverse proxy vers Rasa.
### Flux d'une interaction
 
1. L'utilisateur envoie un message via l'interface.
2. Rasa le transmet au pipeline NLU, qui extrait l'intention et les entités.
3. Le gestionnaire de dialogue (Core) consulte stories, rules et politiques pour choisir l'action suivante.
4. Si l'action est une simple *utterance*, Rasa répond directement ; sinon il appelle l'Action Server.
5. La réponse est renvoyée à l'utilisateur et l'état de la conversation (tracker) est mis à jour.
## 🧰 Technologies utilisées
 
| Composant | Technologie | Justification |
| --- | --- | --- |
| Framework NLU / dialogue | **Rasa 3.6.20** | Open source, support du français, pipeline configurable |
| Modèle NLU | **DIETClassifier** | Léger, précis, intents + entités simultanés |
| Actions métier | **Python 3.10 + rasa-sdk** | Flexibilité, riche écosystème |
| Conteneurisation | **Docker + Docker Compose** | Portabilité, isolation, reproductibilité |
| Serveur web | **Nginx** | Fichiers statiques + reverse proxy |
| Frontend | **HTML / CSS / JavaScript** | Léger, sans framework |
| Cloud | **AWS EC2** (t2.micro, Ubuntu 24.04) | Free Tier adapté à un projet de démonstration |
 
**Outils de développement :** Visual Studio Code, Git / GitHub, Terminal Linux / WSL, MobaXterm.
 
## 🧠 Pipeline NLU
 
Le pipeline transforme le texte brut en intentions et entités structurées :
 
1. **WhitespaceTokenizer** : découpe en tokens.
2. **RegexFeaturizer** : détecte des motifs (années à 4 chiffres, kilométrages « km »…).
3. **LexicalSyntacticFeaturizer** : caractéristiques syntaxiques (position, casse, ponctuation).
4. **CountVectorsFeaturizer** (×2) : niveau mot + n-grammes de caractères (1 à 4) pour la robustesse aux fautes de frappe (« renalut » → « renault »).
5. **DIETClassifier** : transformer léger (100 epochs) — classification d'intention + extraction d'entités.
6. **EntitySynonymMapper** : normalisation des entités (« RENAULT » → « Renault »).
7. **FallbackClassifier** : si la confiance < 70 % ou ambiguïté < 10 %, déclenche `nlu_fallback` → `utter_default`.
**Politiques de dialogue :** `MemoizationPolicy`, `RulePolicy`, `TEDPolicy`.
 
## 🏷️ Intentions et entités
 
**Intentions**
 
| Catégorie | Intentions |
| --- | --- |
| Navigation conversationnelle | `greet`, `goodbye`, `affirm`, `deny`, `out_of_scope` |
| Diagnostic technique | `ask_oil_change`, `ask_tire_check`, `ask_brake_check`, `ask_battery_check`, `ask_warning_light` |
| Planification et maintenance | `ask_maintenance`, `ask_service_schedule`, `ask_price_estimate`, `ask_appointment` |
| Informationnelles | `ask_garage_hours`, `provide_vehicle_info` |
 
**Entités**
 
| Entité | Description |
| --- | --- |
| `vehicle_brand` | Marque du véhicule (Renault, BMW, Toyota…) |
| `vehicle_model` | Modèle du véhicule (Clio, Série 3, Corolla…) |
| `vehicle_year` | Année de fabrication (1900-2026) |
| `mileage` | Kilométrage actuel |
| `warning_light_color` | Couleur du voyant (rouge, orange, jaune, bleu, vert) |
 
**Actions personnalisées (`actions.py`)**
 
- `ValidateVehicleInfoForm` — validation des slots du formulaire
- `action_check_maintenance_due` — bilan de maintenance selon le kilométrage
- `action_estimate_service_cost` — estimation des coûts
- `action_diagnose_warning_light` — diagnostic des voyants
- `action_calculate_next_oil_change` — calcul de la prochaine vidange
## 📂 Structure du projet
 
```
smartgarage/
├── actions/
│   └── actions.py          # Actions personnalisées Rasa (logique métier)
├── data/
│   ├── nlu.yml             # Données d'entraînement NLU
│   ├── stories.yml         # Scénarios de dialogue
│   └── rules.yml           # Règles de dialogue déterministes
├── frontend/
│   └── index.html          # Interface web du chatbot
├── config.yml              # Pipeline NLU et politiques de dialogue
├── domain.yml              # Intents, entités, slots, réponses, formulaire
├── endpoints.yml           # URL de l'Action Server (http://action_server:5055/webhook)
├── Dockerfile              # Image de l'Action Server (rasa/rasa-sdk:3.6.2)
├── docker-compose.yml      # Orchestration des 3 services
├── nginx.conf              # Reverse proxy + fichiers statiques
├── requirements.txt        # Dépendances Python (rasa-sdk)
└── README.md
```

> ℹ️ Adaptez cette arborescence à l'organisation réelle de votre dépôt.
 
## 🚀 Installation et lancement
 
### Prérequis
 
- [Docker](https://docs.docker.com/get-docker/) et Docker Compose
- [Git](https://git-scm.com/)
- Environ 2 Go de RAM disponibles pour l'entraînement du modèle
### 1. Cloner le dépôt
 
```bash
git clone https://github.com/sofiane-jell/Project-chatboot-smart-garage
cd Project-chatboot-smart-garage
```
 
### 2. Entraîner le modèle Rasa
 
```bash
docker run --rm -v "$(pwd)":/app rasa/rasa:3.6.20 train
```
 
### 3. Lancer les services
 
```bash
docker compose up -d --build
```
 
Trois conteneurs sont démarrés :
 
| Service | Rôle | Port |
| --- | --- | --- |
| `rasa` | Serveur conversationnel (API REST) | 5005 |
| `action_server` | Actions personnalisées (Rasa SDK) | 5055 |
| `nginx` | Frontend + reverse proxy | 80 |
 
### 4. Accéder à l'application
 
Ouvrez votre navigateur sur **http://localhost** .
 
### 5. Tester l'API directement
 
```bash
curl -X POST http://localhost/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "bonjour"}'
```
 
### Commandes utiles
 
```bash
docker compose ps              # État des conteneurs
docker compose logs rasa       # Logs du serveur Rasa
docker compose down            # Arrêter les services
```
 
## ☁️ Déploiement sur AWS EC2
 
Le projet a été déployé sur une instance **AWS EC2 t2.micro** (Ubuntu 24.04) : 2 vCPU Intel Xeon Platinum 8259CL @ 2.5 GHz, ~908 Mo de RAM, accès SSH et IP publique.
 
Étapes principales :
 
1. Créer l'instance EC2 et ouvrir les ports nécessaires (SSH 22, HTTP 80) dans le groupe de sécurité.
2. Se connecter en SSH (par exemple avec MobaXterm) et installer Docker.
3. **Ajouter 2 Go de swap**, indispensable pour entraîner le modèle sur une machine à mémoire limitée :
```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
```
4. Cloner le dépôt, entraîner le modèle puis lancer `docker compose up -d --build`.
5. Accéder à l'application via l'IP publique de l'instance.
### Problèmes rencontrés et solutions
 
| Problème | Solution |
| --- | --- |
| Modèle corrompu | Réentraînement du modèle |
| Manque de RAM pendant l'entraînement | Ajout de 2 Go de swap |
| Mauvaise URL Rasa dans le frontend (`localhost:5005`) | Utilisation d'une URL relative proxifiée par Nginx |
 
## 💡 Exemples de conversations
 
| Scénario | Message utilisateur | Comportement du bot |
| --- | --- | --- |
| Bilan de maintenance | « entretien » | Lance `vehicle_info_form` (marque, modèle, année, km) puis affiche le bilan complet |
| Vidange | « quand faire la vidange ? » | Donne les intervalles recommandés et propose de calculer la prochaine vidange |
| Voyant lumineux | « j'ai un voyant orange » | Identifie la couleur et fournit les recommandations |
| Estimation de coût | « combien coûte une vidange ? » | Fourchette de prix + coordonnées du garage |
| Hors sujet | Question non liée à l'automobile | Répond poliment que le bot est spécialisé en maintenance véhicule |
 
> 📸 *Vous pouvez ajouter ici des captures d'écran de l'interface dans un dossier `docs/` ou `screenshots/`.*
 
## ✅ Tests et validation
 
- **Tests fonctionnels** : 5 scénarios (bilan, vidange, voyant, coût, hors-sujet).
- **Conteneurs** : `docker compose ps` — `rasa`, `action_server` et `nginx` actifs.
- **API** : requête `curl` vers `/webhooks/rest/webhook`.
- **Logs** : `docker compose logs rasa` — message « Rasa server is up and running » et absence d'erreur de chargement du modèle.
### Exigences non fonctionnelles visées
 
- Temps de réponse < 2 s ; accuracy NLU > 85 %.
- Disponibilité de 99 %, redémarrage automatique via `restart: unless-stopped`.
- Architecture modulaire (séparation `data/`, `actions/`, `domain.yml`, `config.yml`).
- Services isolés dans un réseau Docker interne.
- Portabilité Windows / Linux / macOS via Docker.
## 🔭 Limites et perspectives
 
**Limites actuelles**
 
- Corpus d'entraînement de taille réduite.
- Pas de persistance des données conversationnelles.
**Pistes d'amélioration**
 
- Enrichir les données d'entraînement NLU.
- Intégrer une base de données persistante.
- Utiliser des modèles de langage plus avancés (LLM).
- Passer à une orchestration Kubernetes (autoscaling du Rasa Server) et sécuriser les échanges en TLS.
## 👤 Auteur
 
**Sofiane Jellouli** — Master ISI
---
 
## 📚 Références
 
- [Rasa Open Source Documentation](https://rasa.com/docs/)
- [Docker Documentation](https://docs.docker.com)
- [Amazon EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [NGINX Documentation](https://nginx.org/en/docs/)
- [Python 3 Documentation](https://docs.python.org/3/)
 
