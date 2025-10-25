#!/bin/bash

# Script de lancement du Dashboard Streamlit
# Crypto Pipeline - Data Engineering

echo "🚀 Démarrage du Dashboard Crypto..."
echo ""

# Se placer dans le bon répertoire
cd "$(dirname "$0")"

# Activer l'environnement virtuel
source airflow_env/bin/activate

# Lancer Streamlit
streamlit run dashboard.py --server.port 8501 --server.address localhost

echo ""
echo "✅ Dashboard arrêté"

