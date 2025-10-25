import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuration de la page
st.set_page_config(
    page_title="Crypto Dashboard - Pipeline Data",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction de connexion à PostgreSQL
@st.cache_resource
def get_connection():
    """Créer une connexion PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="crypto_db",
            user="postgres",
            password="postgres"
        )
        return conn
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données: {e}")
        return None

# Fonction pour récupérer les données
@st.cache_data(ttl=60)  # Cache pendant 60 secondes
def get_latest_crypto_data():
    """Récupérer les dernières données crypto"""
    conn = get_connection()
    if conn:
        query = """
        SELECT rang, symbole, nom, prix_usd, variation_24h_pourcent, 
               market_cap_usd, volume_24h_usd, date_import, heure_import
        FROM crypto_temps_reel
        WHERE date_import = CURRENT_DATE
        ORDER BY rang
        LIMIT 50;
        """
        df = pd.read_sql(query, conn)
        return df
    return pd.DataFrame()

@st.cache_data(ttl=60)
def get_historical_data(symbole, days=7):
    """Récupérer l'historique d'une crypto"""
    conn = get_connection()
    if conn:
        query = f"""
        SELECT date_import, heure_import, prix_usd, variation_24h_pourcent
        FROM crypto_temps_reel
        WHERE symbole = '{symbole}'
        AND date_import >= CURRENT_DATE - INTERVAL '{days} days'
        ORDER BY date_import DESC, heure_import DESC
        LIMIT 100;
        """
        df = pd.read_sql(query, conn)
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['date_import'].astype(str) + ' ' + df['heure_import'].astype(str))
        return df
    return pd.DataFrame()

@st.cache_data(ttl=300)
def get_pipeline_stats():
    """Récupérer les statistiques du pipeline"""
    conn = get_connection()
    if conn:
        query = """
        SELECT operation, records_affected, timestamp
        FROM pipeline_logs
        ORDER BY timestamp DESC
        LIMIT 20;
        """
        df = pd.read_sql(query, conn)
        return df
    return pd.DataFrame()

# Titre principal
st.title("Dashboard Crypto - Pipeline Data Engineering")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    # Refresh button
    if st.button("Actualiser les données"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Sélection période historique
    st.subheader("Période d'analyse")
    days = st.slider("Jours d'historique", 1, 30, 7)
    
    st.markdown("---")
    
    # Informations
    st.info("""
    **Pipeline Airflow**
    - Fréquence: 30 minutes
    - Source: CoinCap API
    - Stockage: PostgreSQL
    """)
    
    st.success(f"Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")

# Récupérer les données
df_crypto = get_latest_crypto_data()

if df_crypto.empty:
    st.warning("Aucune donnée disponible. Vérifiez que le pipeline Airflow est en cours d'exécution.")
    st.stop()

# Métriques principales (Top 3)
st.header("Top 3 Cryptomonnaies")
col1, col2, col3 = st.columns(3)

top3 = df_crypto.head(3)

with col1:
    crypto = top3.iloc[0]
    delta_color = "normal" if crypto['variation_24h_pourcent'] >= 0 else "inverse"
    st.metric(
        label=f"#{crypto['rang']} {crypto['nom']} ({crypto['symbole']})",
        value=f"${crypto['prix_usd']:,.2f}",
        delta=f"{crypto['variation_24h_pourcent']:.2f}%",
        delta_color=delta_color
    )

with col2:
    crypto = top3.iloc[1]
    delta_color = "normal" if crypto['variation_24h_pourcent'] >= 0 else "inverse"
    st.metric(
        label=f"#{crypto['rang']} {crypto['nom']} ({crypto['symbole']})",
        value=f"${crypto['prix_usd']:,.2f}",
        delta=f"{crypto['variation_24h_pourcent']:.2f}%",
        delta_color=delta_color
    )

with col3:
    crypto = top3.iloc[2]
    delta_color = "normal" if crypto['variation_24h_pourcent'] >= 0 else "inverse"
    st.metric(
        label=f"#{crypto['rang']} {crypto['nom']} ({crypto['symbole']})",
        value=f"${crypto['prix_usd']:,.2f}",
        delta=f"{crypto['variation_24h_pourcent']:.2f}%",
        delta_color=delta_color
    )

st.markdown("---")

# Statistiques globales
st.header("Statistiques Globales")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_market_cap = df_crypto['market_cap_usd'].sum()
    st.metric("Market Cap Total", f"${total_market_cap/1e9:.2f}B")

with col2:
    avg_variation = df_crypto['variation_24h_pourcent'].mean()
    st.metric("Variation Moyenne 24h", f"{avg_variation:.2f}%")

with col3:
    gainers = len(df_crypto[df_crypto['variation_24h_pourcent'] > 0])
    st.metric("Cryptos en hausse", f"{gainers}/{len(df_crypto)}")

with col4:
    losers = len(df_crypto[df_crypto['variation_24h_pourcent'] < 0])
    st.metric("Cryptos en baisse", f"{losers}/{len(df_crypto)}")

st.markdown("---")

# Graphiques
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 - Variation 24h")
    top10 = df_crypto.head(10).copy()
    top10['color'] = top10['variation_24h_pourcent'].apply(lambda x: 'green' if x >= 0 else 'red')
    
    fig = px.bar(
        top10,
        x='symbole',
        y='variation_24h_pourcent',
        color='color',
        color_discrete_map={'green': '#00cc00', 'red': '#ff3333'},
        title="Variation 24h (%)",
        labels={'variation_24h_pourcent': 'Variation (%)', 'symbole': 'Crypto'},
        text='variation_24h_pourcent'
    )
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Répartition Market Cap")
    top10_market = df_crypto.head(10)
    
    fig = px.pie(
        top10_market,
        values='market_cap_usd',
        names='symbole',
        title="Répartition du Market Cap (Top 10)",
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Tableau des cryptos
st.header("Liste des Cryptomonnaies")

# Filtres
col1, col2, col3 = st.columns(3)

with col1:
    filter_positive = st.checkbox("Seulement les hausses", value=False)

with col2:
    filter_negative = st.checkbox("Seulement les baisses", value=False)

with col3:
    min_variation = st.number_input("Variation min (%)", value=-100.0, step=1.0)

# Appliquer les filtres
df_filtered = df_crypto.copy()

if filter_positive:
    df_filtered = df_filtered[df_filtered['variation_24h_pourcent'] > 0]

if filter_negative:
    df_filtered = df_filtered[df_filtered['variation_24h_pourcent'] < 0]

df_filtered = df_filtered[df_filtered['variation_24h_pourcent'] >= min_variation]

# Formater le DataFrame pour l'affichage
df_display = df_filtered[['rang', 'symbole', 'nom', 'prix_usd', 'variation_24h_pourcent', 'market_cap_usd']].copy()
df_display.columns = ['Rang', 'Symbole', 'Nom', 'Prix (USD)', 'Variation 24h (%)', 'Market Cap (USD)']
df_display['Prix (USD)'] = df_display['Prix (USD)'].apply(lambda x: f"${x:,.2f}")
df_display['Market Cap (USD)'] = df_display['Market Cap (USD)'].apply(lambda x: f"${x/1e9:.2f}B" if x >= 1e9 else f"${x/1e6:.2f}M")

# Colorer les variations
def color_variation(val):
    try:
        num_val = float(val.replace('%', ''))
        color = 'green' if num_val >= 0 else 'red'
        return f'color: {color}'
    except:
        return ''

st.dataframe(
    df_display.style.applymap(color_variation, subset=['Variation 24h (%)']),
    use_container_width=True,
    height=400
)

st.markdown("---")

# Analyse d'une crypto spécifique
st.header("Analyse Détaillée d'une Crypto")

selected_crypto = st.selectbox(
    "Sélectionner une cryptomonnaie",
    df_crypto['symbole'].unique(),
    index=0
)

if selected_crypto:
    # Info de la crypto sélectionnée
    crypto_info = df_crypto[df_crypto['symbole'] == selected_crypto].iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Rang", f"#{crypto_info['rang']}")
    
    with col2:
        st.metric("Prix actuel", f"${crypto_info['prix_usd']:,.2f}")
    
    with col3:
        delta_color = "normal" if crypto_info['variation_24h_pourcent'] >= 0 else "inverse"
        st.metric("Variation 24h", f"{crypto_info['variation_24h_pourcent']:.2f}%", delta_color=delta_color)
    
    with col4:
        st.metric("Market Cap", f"${crypto_info['market_cap_usd']/1e9:.2f}B")
    
    # Historique
    st.subheader(f"Historique du prix - {selected_crypto} ({days} derniers jours)")
    
    df_hist = get_historical_data(selected_crypto, days)
    
    if not df_hist.empty:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_hist['datetime'],
            y=df_hist['prix_usd'],
            mode='lines+markers',
            name='Prix USD',
            line=dict(color='#00cc00', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=f"Évolution du prix de {crypto_info['nom']} ({selected_crypto})",
            xaxis_title="Date",
            yaxis_title="Prix (USD)",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiques historiques
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Prix minimum", f"${df_hist['prix_usd'].min():,.2f}")
        
        with col2:
            st.metric("Prix maximum", f"${df_hist['prix_usd'].max():,.2f}")
        
        with col3:
            variation_total = ((df_hist['prix_usd'].iloc[0] - df_hist['prix_usd'].iloc[-1]) / df_hist['prix_usd'].iloc[-1] * 100)
            st.metric(f"Variation sur {days} jours", f"{variation_total:.2f}%")
    else:
        st.warning(f"Aucun historique disponible pour {selected_crypto}")

st.markdown("---")

# Statistiques du pipeline
st.header("Statistiques du Pipeline Airflow")

df_pipeline = get_pipeline_stats()

if not df_pipeline.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dernières opérations")
        df_display_pipeline = df_pipeline[['operation', 'records_affected', 'timestamp']].copy()
        df_display_pipeline.columns = ['Opération', 'Enregistrements', 'Date/Heure']
        st.dataframe(df_display_pipeline, use_container_width=True, height=300)
    
    with col2:
        st.subheader("Opérations par type")
        ops_count = df_pipeline['operation'].value_counts()
        
        fig = px.bar(
            x=ops_count.index,
            y=ops_count.values,
            labels={'x': 'Type d\'opération', 'y': 'Nombre'},
            title="Répartition des opérations"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune statistique de pipeline disponible")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p><strong>Crypto Dashboard</strong> - Pipeline Data Engineering</p>
    <p>Données en temps réel depuis CoinCap API | Mis à jour toutes les 30 minutes via Airflow</p>
    <p><em>Master 1 DIT - Data Engineering Project - Groupe 3</em></p>
</div>
""", unsafe_allow_html=True)

