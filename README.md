# Pipeline de Données Cryptomonnaies - Airflow + Spark + PostgreSQL

## Table des matières

- [Présentation du projet](#présentation-du-projet)
- [Architecture du système](#architecture-du-système)
- [Technologies utilisées](#technologies-utilisées)
- [Prérequis](#prérequis)
- [Installation de A à Z](#installation-de-a-à-z)
- [Structure du projet](#structure-du-projet)
- [Configuration](#configuration)
- [Démarrage du système](#démarrage-du-système)
- [Les DAGs Airflow](#les-dags-airflow)
- [Utilisation](#utilisation)
- [Monitoring et Logs](#monitoring-et-logs)
- [Troubleshooting](#troubleshooting)
- [Auteurs](#auteurs)

---

## Présentation du projet

Ce projet implémente un **pipeline de données automatisé** pour collecter, traiter et analyser en temps réel les données des cryptomonnaies depuis l'API CoinCap. Le système orchestre l'extraction, la transformation et le chargement (ETL) des données avec Apache Airflow, traite les données avec Apache Spark (Scala), et stocke le tout dans une base PostgreSQL.

### Objectifs

- Collecter automatiquement les données des cryptomonnaies toutes les 30 minutes
- Traiter et transformer les données avec Apache Spark
- Stocker les données dans PostgreSQL pour analyse
- Monitorer les performances et détecter les anomalies
- Envoyer des alertes automatiques par email
- Générer des rapports quotidiens

---

## Architecture du système

```
┌─────────────────────────────────────────────────────────────────┐
│                     APACHE AIRFLOW                              │
│                 (Orchestration & Scheduling)                    │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ├─────► DAG 1: crypto_data_pipeline (30 min)
              │       ├─ Check API CoinCap
              │       ├─ Check Database Connection
              │       ├─ Cleanup Old Data (7 days)
              │       ├─ Spark Processing (Scala)
              │       ├─ Verify Results
              │       ├─ Data Quality Check
              │       ├─ Generate Daily Report
              │       └─ Send Email Notification
              │
              └─────► DAG 2: crypto_monitoring (hourly)
                      ├─ Check Top 10 Cryptos
                      ├─ Detect Anomalies
                      └─ Send Alerts

         ┌────────────────┐
         │  CoinCap API   │
         │ (Data Source)  │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │  Apache Spark  │
         │   (Scala JAR)  │
         │   Processing   │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │   PostgreSQL   │
         │   (Storage)    │
         └────────────────┘
```

---

## Technologies utilisées

| Technologie | Version | Utilisation |
|-------------|---------|-------------|
| **Apache Airflow** | 2.10.2 | Orchestration des pipelines |
| **Apache Spark** | 3.x | Traitement distribué des données (Scala) |
| **PostgreSQL** | 14+ | Base de données relationnelle |
| **Python** | 3.12 | Langage principal pour Airflow |
| **Scala** | 2.13 | Job Spark |
| **Pandas** | 2.3+ | Analyse de données Python |
| **psycopg2** | 2.9+ | Connecteur PostgreSQL |
| **requests** | 2.32+ | Requêtes HTTP API |

### API externe
- **CoinCap API v2** : Source de données des cryptomonnaies (https://api.coincap.io/v2)

---

## Prérequis

### Logiciels requis

1. **Python 3.12+**
   ```bash
   python3 --version
   ```

2. **PostgreSQL 14+**
   ```bash
   psql --version
   ```

3. **Java 11+** (pour Spark)
   ```bash
   java -version
   ```

4. **Apache Spark** (inclus dans le projet via le JAR)

5. **Git** (pour cloner le projet)

---

## Installation de A à Z

### Étape 1 : Cloner le projet

```bash
cd ~/Documents
git clone <votre-repo>
cd spark_airflow
```

### Étape 2 : Créer et activer l'environnement virtuel Python

```bash
# Créer l'environnement virtuel
python3 -m venv airflow_env

# Activer l'environnement
source airflow_env/bin/activate
```

### Étape 3 : Installer Apache Airflow et dépendances

**Option 1 : Installation rapide avec requirements.txt**
```bash
# Définir la variable d'environnement pour Airflow
export AIRFLOW_HOME=$(pwd)

# Installer toutes les dépendances
pip install -r requirements.txt
```

**Option 2 : Installation manuelle**
```bash
# Définir la variable d'environnement pour Airflow
export AIRFLOW_HOME=$(pwd)

# Installer Airflow
pip install "apache-airflow==2.10.2" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.2/constraints-3.12.txt"

# Installer les providers nécessaires
pip install apache-airflow-providers-apache-spark==4.1.0
pip install apache-airflow-providers-postgres==5.5.1

# Installer les dépendances Python supplémentaires
pip install pandas psycopg2-binary requests streamlit plotly
```

### Étape 4 : Initialiser la base de données Airflow

```bash
# Initialiser la base de données Airflow (SQLite par défaut)
airflow db init
```

### Étape 5 : Créer un utilisateur admin Airflow

```bash
airflow users create \
    --username admin \
    --firstname Komi \
    --lastname Missiamenou \
    --role Admin \
    --email komimissiamenou97@gmail.com \
    --password admin
```

### Étape 6 : Configurer PostgreSQL

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Dans le shell PostgreSQL, créer la base de données
CREATE DATABASE crypto_db;

# Se connecter à la base
\c crypto_db

# Exécuter le script de création des tables
\i scripts/bd.sql

# Quitter
\q
```

### Étape 7 : Configurer les variables Airflow

Dans l'interface web Airflow (après démarrage), aller dans **Admin → Variables** et ajouter :

| Key | Value | Description |
|-----|-------|-------------|
| `coincap_url` | `https://api.coincap.io/v2/assets` | URL de l'API CoinCap |
| `postgres_url` | `jdbc:postgresql://localhost:5432/crypto_db` | URL JDBC PostgreSQL |
| `pg_user` | `postgres` | Utilisateur PostgreSQL |
| `pg_password` | `postgres` | Mot de passe PostgreSQL |

### Étape 8 : Configurer les connexions Airflow

Dans **Admin → Connections**, ajouter :

#### Connection PostgreSQL
- **Conn Id** : `postgres_default`
- **Conn Type** : `Postgres`
- **Host** : `localhost`
- **Database** : `crypto_db`
- **Login** : `postgres`
- **Password** : `postgres`
- **Port** : `5432`

#### Connection Spark
- **Conn Id** : `spark_default`
- **Conn Type** : `Spark`
- **Host** : `local[*]`
- **Extra** : `{"deploy-mode": "client"}`

---

## Structure du projet

```
spark_airflow/
│
├── airflow_env/                    # Environnement virtuel Python
│   ├── bin/
│   ├── lib/
│   └── pyvenv.cfg
│
├── dags/                           # DAGs Airflow
│   ├── dag_import_data.py         # Pipeline principal (30 min)
│   └── dag_monitoring_data.py     # Monitoring (hourly)
│
├── jars/                           # JARs Spark
│   └── crypto-spark-processor.jar # Job Spark Scala compilé
│
├── config/                         # Fichiers de configuration
│   └── config.properties          # Configuration CoinCap + PostgreSQL
│
├── scripts/                        # Scripts SQL
│   └── bd.sql                     # Schéma de la base de données
│
├── logs/                           # Logs Airflow (généré automatiquement)
│   └── scheduler/
│
├── airflow.cfg                     # Configuration Airflow
├── airflow.db                      # Base SQLite Airflow
└── README.md                       # Ce fichier
```

---

## Configuration

### 1. Configuration CoinCap API

Le fichier `config/config.properties` contient :

```properties
# Configuration CoinCap API
COINCAP_API_KEY=e16134f9b6ec6787a1e70bee66c5ee26dbe2f4c4b8171ffeda56bb05c1d5cfba
COINCAP_BASE_URL=https://api.coincap.io/v2

# Configuration PostgreSQL
POSTGRES_URL=jdbc:postgresql://localhost:5432/crypto_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### 2. Configuration Email (optionnel)

Pour recevoir les notifications par email, modifier `airflow.cfg` :

```ini
[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = votre-email@gmail.com
smtp_password = votre-mot-de-passe-app
smtp_port = 587
smtp_mail_from = votre-email@gmail.com
```

**Note** : Pour Gmail, créer un "Mot de passe d'application" dans les paramètres de sécurité.

---

## 🎬 Démarrage du système

### Option 1 : Démarrage manuel (2 terminaux)

#### Terminal 1 - Webserver Airflow
```bash
cd /Users/komidoveneymissiamenou/Documents/Master\ 1\ DIT/DataEnge/spark_airflow
source airflow_env/bin/activate
export AIRFLOW_HOME=$(pwd)
airflow webserver --port 8080
```

#### Terminal 2 - Scheduler Airflow
```bash
cd /Users/komidoveneymissiamenou/Documents/Master\ 1\ DIT/DataEnge/spark_airflow
source airflow_env/bin/activate
export AIRFLOW_HOME=$(pwd)
airflow scheduler
```

### Option 2 : Démarrage en arrière-plan

```bash
# Démarrer le webserver en arrière-plan
nohup airflow webserver --port 8080 > logs/webserver.log 2>&1 &

# Démarrer le scheduler en arrière-plan
nohup airflow scheduler > logs/scheduler.log 2>&1 &
```

### Accéder à l'interface Airflow

Ouvrir le navigateur : **http://localhost:8080**

**Identifiants** :
- Username : `admin`
- Password : `admin`

---

## Les DAGs Airflow

### DAG 1 : `crypto_data_pipeline`

**Fréquence** : Toutes les 30 minutes

**Workflow** :
```
start
  ├─► check_coincap_api          (Vérifier l'API CoinCap)
  └─► check_database_connection  (Vérifier PostgreSQL)
       ↓
  cleanup_old_data               (Nettoyer données > 7 jours)
       ↓
  spark_crypto_processing        (Job Spark Scala - Traitement)
       ↓
  verify_spark_results           (Vérifier résultats Spark)
       ↓
  verify_data_quality            (Contrôle qualité Top 10)
       ↓
  generate_daily_report          (Générer rapport quotidien)
       ↓
  send_success_email             (Email de notification)
       ↓
  end
```

**Fonctionnalités** :
- Collecte des données des cryptos depuis CoinCap
- Traitement avec Spark (transformation, nettoyage)
- Stockage dans PostgreSQL
- Vérification de la qualité des données
- Génération de rapports
- Notifications email

### DAG 2 : `crypto_monitoring`

**Fréquence** : Toutes les heures

**Workflow** :
```
start
  ↓
check_top_10_cryptos            (Analyser Top 10)
  ↓
detect_anomalies                (Détection d'anomalies)
  ↓
send_alert_if_needed            (Alerte si nécessaire)
  ↓
end
```

**Fonctionnalités** :
- Surveillance des variations importantes (> 10%)
- Détection d'anomalies
- Alertes automatiques par email

---

## Dashboard Streamlit

### Accéder au Dashboard

Le projet inclut un **dashboard interactif Streamlit** pour visualiser vos données crypto en temps réel !

#### Démarrage rapide

**Option 1 : Script automatique**
```bash
./run_dashboard.sh
```

**Option 2 : Manuel**
```bash
cd /Users/komidoveneymissiamenou/Documents/Master\ 1\ DIT/DataEnge/spark_airflow
source airflow_env/bin/activate
streamlit run dashboard.py
```

#### Accès au Dashboard

Une fois lancé, ouvrez votre navigateur : **http://localhost:8501**

### Fonctionnalités du Dashboard

Le dashboard propose plusieurs visualisations :

#### Top 3 Cryptomonnaies
- Affichage en temps réel des 3 meilleures cryptos
- Prix actuel et variation 24h avec couleurs (vert/rouge)

#### Statistiques Globales
- **Market Cap Total** : Capitalisation totale du marché
- **Variation Moyenne 24h** : Performance moyenne de toutes les cryptos
- **Cryptos en hausse/baisse** : Compteurs en temps réel

#### Graphiques Interactifs
1. **Graphique en barres** : Variation 24h du Top 10
2. **Graphique circulaire** : Répartition du Market Cap

#### Tableau des Cryptomonnaies
- Liste complète avec filtres :
  - Seulement les hausses
  - Seulement les baisses
  - Variation minimale personnalisée
- Tri et recherche
- Colonnes colorées selon les variations

#### Analyse Détaillée
- Sélection d'une crypto spécifique
- **Graphique d'évolution** : Prix historique sur X jours (configurable)
- **Statistiques** :
  - Prix minimum/maximum sur la période
  - Variation totale sur X jours

#### Statistiques du Pipeline
- Dernières opérations Airflow
- Graphique des opérations par type
- Logs en temps réel

### Personnalisation

Dans la **barre latérale** du dashboard :
- Bouton de rafraîchissement manuel
- Curseur pour sélectionner la période d'analyse (1-30 jours)
- Informations sur le pipeline

### Captures d'écran

Le dashboard affiche :
- Métriques en temps réel
- Graphiques interactifs (zoom, pan, export)
- Couleurs adaptatives (vert pour hausse, rouge pour baisse)
- Design responsive et moderne
- Mise à jour automatique des données (cache 60s)

---

## Utilisation

### 1. Activer les DAGs

Dans l'interface Airflow (http://localhost:8080) :
1. Aller sur la page d'accueil
2. Rechercher `crypto_data_pipeline` et `crypto_monitoring`
3. Cliquer sur le **toggle** à gauche pour les activer (devient bleu)

### 2. Exécuter manuellement un DAG

1. Cliquer sur le nom du DAG
2. Cliquer sur le bouton **Play** (en haut à droite)
3. Confirmer l'exécution

### 3. Visualiser l'exécution

- **Grid View** : Vue d'ensemble des exécutions
- **Graph View** : Vue graphique du workflow
- **Task Duration** : Durée d'exécution des tâches
- **Gantt** : Diagramme de Gantt

### 4. Consulter les logs

Pour chaque tâche :
1. Cliquer sur la tâche dans le Graph View
2. Cliquer sur **Log**
3. Les logs s'affichent en temps réel

---

## Monitoring et Logs

### Logs Airflow

Les logs sont stockés dans le dossier `logs/` :

```bash
# Voir les logs du scheduler
tail -f logs/scheduler/latest/*.log

# Voir les logs d'une tâche spécifique
tail -f logs/dag_id=crypto_data_pipeline/run_id=*/task_id=*/attempt=*.log
```

### Monitoring PostgreSQL

```bash
# Se connecter à la base
psql -U postgres -d crypto_db

# Voir les dernières données importées
SELECT * FROM crypto_temps_reel 
WHERE date_import = CURRENT_DATE 
ORDER BY rang LIMIT 10;

# Statistiques du pipeline
SELECT * FROM pipeline_logs 
ORDER BY timestamp DESC LIMIT 20;
```

### Consulter les rapports

Les rapports quotidiens sont générés dans les logs de la tâche `generate_daily_report` :

```
RAPPORT CRYPTO QUOTIDIEN - 2025-10-25
============================================

TOP 10 CRYPTOMONNAIES:
rang  symbole  nom         prix_usd    variation_24h_pourcent
1     BTC      Bitcoin     67234.50    +2.45
2     ETH      Ethereum    3567.89     +3.12
...

Market Cap Total: $2.45 Md
Performance Moyenne: +2.67%
Dernière mise à jour: 21:59:50
```

---

## Troubleshooting

### Problème : DAG cassé (Broken DAG)

**Erreur** : `ModuleNotFoundError: No module named 'pandas'`

**Solution** :
```bash
source airflow_env/bin/activate
pip install pandas psycopg2-binary requests
# Redémarrer le scheduler
pkill -f "airflow scheduler"
airflow scheduler
```

---

### Problème : Providers manquants

**Erreur** : `No module named 'airflow.providers.apache.spark'`

**Solution** :
```bash
pip install apache-airflow-providers-apache-spark
pip install apache-airflow-providers-postgres
# Redémarrer Airflow
```

---

### Problème : Connexion PostgreSQL échoue

**Erreur** : `could not connect to server`

**Solution** :
```bash
# Vérifier que PostgreSQL tourne
brew services list  # macOS
systemctl status postgresql  # Linux

# Démarrer PostgreSQL si nécessaire
brew services start postgresql  # macOS
systemctl start postgresql  # Linux

# Tester la connexion
psql -U postgres -d crypto_db
```

---

### Problème : API CoinCap non accessible

**Erreur** : `API CoinCap erreur: 429 Too Many Requests`

**Solution** : Vous avez atteint la limite de requêtes. Attendre quelques minutes ou augmenter l'intervalle du DAG.

---

### Problème : Spark job échoue

**Erreur** : `FileNotFoundException: crypto-spark-processor.jar`

**Solution** :
1. Vérifier que le JAR existe dans `jars/crypto-spark-processor.jar`
2. Vérifier le chemin dans le DAG (ligne 177 de `dag_import_data.py`)
3. Le chemin doit être absolu ou relatif à AIRFLOW_HOME

---

### Problème : Scheduler ne démarre pas

**Erreur** : `Address already in use`

**Solution** :
```bash
# Trouver le processus qui utilise le port
lsof -i :8793

# Tuer le processus
kill -9 <PID>

# Redémarrer le scheduler
airflow scheduler
```

---

## Commandes utiles

### Airflow

```bash
# Lister les DAGs
airflow dags list

# Tester un DAG
airflow dags test crypto_data_pipeline 2025-10-25

# Voir les erreurs d'import
airflow dags list-import-errors

# Lister les tâches d'un DAG
airflow tasks list crypto_data_pipeline

# Tester une tâche spécifique
airflow tasks test crypto_data_pipeline check_coincap_api 2025-10-25

# Déclencher un DAG manuellement
airflow dags trigger crypto_data_pipeline

# Mettre en pause un DAG
airflow dags pause crypto_data_pipeline

# Réactiver un DAG
airflow dags unpause crypto_data_pipeline
```

### PostgreSQL

```bash
# Se connecter à la base
psql -U postgres -d crypto_db

# Requêtes SQL utiles
-- Nombre de cryptos par jour
SELECT date_import, COUNT(*) 
FROM crypto_temps_reel 
GROUP BY date_import 
ORDER BY date_import DESC;

-- Top 10 cryptos actuelles
SELECT rang, symbole, nom, prix_usd, variation_24h_pourcent
FROM crypto_temps_reel
WHERE date_import = CURRENT_DATE
ORDER BY rang
LIMIT 10;

-- Historique d'une crypto
SELECT date_import, heure_import, prix_usd, variation_24h_pourcent
FROM crypto_temps_reel
WHERE symbole = 'BTC'
ORDER BY date_import DESC, heure_import DESC
LIMIT 20;
```

---

## Contact et Support

### Équipe du projet

**Groupe 3 - Master 1 DIT**

- **Komi Missiamenou** - komimissiamenou97@gmail.com
- **Sabet Shibangua Lidor** - sabuetshibangualidor@gmail.com

### Support

En cas de problème :
1. Consulter la section [Troubleshooting](#-troubleshooting)
2. Vérifier les logs Airflow
3. Contacter l'équipe

---

## Contexte académique

**Projet réalisé dans le cadre de** :
- Formation : Master 1 DIT (Data & Intelligence Technologique)
- Module : Data Engineering
- Année : 2025

**Objectifs pédagogiques** :
- Orchestration de pipelines de données avec Apache Airflow
- Traitement distribué avec Apache Spark
- Intégration de sources de données externes (API REST)
- Stockage et requêtage avec PostgreSQL
- Monitoring et alerting automatisés

---

## Licence

Ce projet est réalisé à des fins éducatives dans le cadre du Master 1 DIT.

---

## Remerciements

- **CoinCap API** pour la fourniture gratuite des données cryptomonnaies
- **Apache Software Foundation** pour Airflow et Spark
- **PostgreSQL Global Development Group**
- Nos enseignants du Master DIT

---

## Notes importantes

1. **Sécurité** : Ne jamais exposer les mots de passe et API keys en production. Utiliser des secrets managers (AWS Secrets Manager, HashiCorp Vault, etc.)

2. **Performance** : En production, remplacer SQLite par PostgreSQL pour la base Airflow elle-même

3. **Scalabilité** : Pour de plus gros volumes, utiliser CeleryExecutor ou KubernetesExecutor au lieu de SequentialExecutor

4. **Backup** : Mettre en place des sauvegardes régulières de la base PostgreSQL

5. **Monitoring** : En production, intégrer des outils comme Prometheus/Grafana pour le monitoring avancé

---

**Dernière mise à jour** : 25 octobre 2025

**Version** : 1.0.0

---

*Made by Groupe 3 - Master 1 DIT*

