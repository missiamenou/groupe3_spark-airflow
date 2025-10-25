from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
import psycopg2
import pandas as pd

default_args = {
    'owner': 'crypto_monitoring',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def check_data_freshness():
    """Vérifier la fraîcheur des données"""
    conn = None
    try:
        # Connexion avec context manager
        conn = psycopg2.connect(
            host="localhost",
            database="crypto_db",
            user="postgres",
            password="postgres",
            connect_timeout=10  # Timeout de connexion
        )
        
        query = """
        SELECT 
            MAX(heure_import) as derniere_maj,
            COUNT(*) as total_records,
            AVG(variation_24h_pourcent) as variation_moyenne
        FROM crypto_temps_reel 
        WHERE date_import = CURRENT_DATE;
        """
        
        df = pd.read_sql(query, conn)
        
        # Vérifier si le DataFrame n'est pas vide
        if df.empty:
            print("Aucune donnée trouvée pour aujourd'hui")
            return False
        
        # Récupérer les valeurs avec gestion de None
        derniere_maj = df['derniere_maj'].iloc[0]
        total_records = int(df['total_records'].iloc[0]) if pd.notna(df['total_records'].iloc[0]) else 0
        
        # Vérifier si derniere_maj n'est pas None/NaT
        if pd.notna(derniere_maj) and total_records > 0:
            print(f"Données fraîches - Dernière maj: {derniere_maj}, Records: {total_records}")
            return True
        else:
            print(f"Données non fraîches ou manquantes - Records: {total_records}")
            return False
            
    except psycopg2.OperationalError as e:
        print(f"Erreur de connexion PostgreSQL: {e}")
        raise  # Relancer pour que Airflow sache que la tâche a échoué
        
    except psycopg2.ProgrammingError as e:
        print(f"Erreur SQL (table inexistante?): {e}")
        raise
        
    except Exception as e:
        print(f"Erreur inattendue lors de la vérification de fraîcheur: {e}")
        raise
        
    finally:
        # Toujours fermer la connexion
        if conn is not None:
            conn.close()
            print("Connexion PostgreSQL fermée")

def detect_anomalies():
    """Détecter les anomalies de marché"""
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="crypto_db",
            user="postgres",
            password="postgres",
            connect_timeout=10
        )
        
        query = """
        SELECT 
            symbole,
            nom,
            prix_usd,
            variation_24h_pourcent,
            volume_24h_usd
        FROM crypto_temps_reel 
        WHERE date_import = CURRENT_DATE
        AND (
            variation_24h_pourcent > 20 
            OR variation_24h_pourcent < -20
            OR volume_24h_usd > 1000000000
        )
        ORDER BY ABS(variation_24h_pourcent) DESC;
        """
        
        df = pd.read_sql(query, conn)
        
        if not df.empty:
            anomalies = df.to_dict('records')
            print(f"{len(anomalies)} anomalie(s) détectée(s):")
            for anomaly in anomalies:
                symbole = anomaly.get('symbole', 'UNKNOWN')
                variation = anomaly.get('variation_24h_pourcent', 0)
                print(f"   - {symbole}: {variation:.2f}%")
            return anomalies
        else:
            print("Aucune anomalie détectée")
            return []
            
    except psycopg2.OperationalError as e:
        print(f"Erreur de connexion PostgreSQL: {e}")
        raise
        
    except psycopg2.ProgrammingError as e:
        print(f"Erreur SQL: {e}")
        raise
        
    except Exception as e:
        print(f"Erreur inattendue lors de la détection d'anomalies: {e}")
        raise
        
    finally:
        if conn is not None:
            conn.close()
            print("Connexion PostgreSQL fermée")

with DAG(
    'crypto_monitoring',
    default_args=default_args,
    description='Monitoring et alertes crypto',
    schedule_interval='0 */2 * * *',  # Toutes les 2 heures
    catchup=False,
    tags=['monitoring', 'crypto', 'alerting']
) as dag:

    check_freshness = PythonOperator(
        task_id='check_data_freshness',
        python_callable=check_data_freshness
    )

    detect_anomalies_task = PythonOperator(
        task_id='detect_market_anomalies',
        python_callable=detect_anomalies
    )

    update_monitoring_stats = PostgresOperator(
        task_id='update_monitoring_stats',
        postgres_conn_id='postgres_default',
        sql="""
        INSERT INTO monitoring_stats (
            check_timestamp, 
            records_count, 
            anomalies_detected,
            market_cap_total
        )
        SELECT 
            NOW(),
            COUNT(*),
            SUM(CASE WHEN ABS(variation_24h_pourcent) > 20 THEN 1 ELSE 0 END),
            SUM(market_cap_usd)
        FROM crypto_temps_reel 
        WHERE date_import = CURRENT_DATE;
        """
    )

    send_alerts = EmailOperator(
        task_id='send_alert_report',
        to=['komimissiamenou97@gmail.com','sabuetshibangualidor@gmail.com'],
        subject='Rapport Alertes Crypto - {{ ds }}',
        html_content="""
        <h3>Rapport de Monitoring Crypto</h3>
        <p>Vérification des anomalies et de la fraîcheur des données.</p>
        <p>Exécuté le: {{ ds }}</p>
        """
    )

    check_freshness >> detect_anomalies_task >> update_monitoring_stats >> send_alerts