from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.email import EmailOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.models import Variable
from datetime import datetime, timedelta
import requests
import json

# Configuration
default_args = {
    'owner': 'groupe3',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30)
}

def check_api():
    try:
        response = requests.get('https://api.coincap.io/v2/assets', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"API CoinCap disponible - {len(data['data'])} cryptos accessibles")
            return True
        else:
            print(f"API CoinCap erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"Erreur connexion API: {e}")
        return False

def check_db_connection():
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="crypto_db",
            user="postgres",
            password="postgres"
        )
        conn.close()
        print("Connexion PostgreSQL réussie")
        return True
    except Exception as e:
        print(f"Erreur connexion PostgreSQL: {e}")
        return False

def verify_spark_results():
    """Vérifier que Spark a bien sauvegardé les données"""
    try:
        import psycopg2
        import pandas as pd
        
        conn = psycopg2.connect(
            host="localhost",
            database="crypto_db",
            user="postgres",
            password="postgres"
        )
        
        query = """
        SELECT COUNT(*) as count, MAX(heure_import) as last_update
        FROM crypto_temps_reel 
        WHERE date_import = CURRENT_DATE;
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        record_count = df['count'].iloc[0]
        
        if record_count > 0:
            print(f"Spark a traité {record_count} cryptos")
            return True
        else:
            print("Aucune donnée trouvée")
            return False
            
    except Exception as e:
        print(f"Erreur vérification: {e}")
        return False

def generate_daily_report():
    """Générer un rapport quotidien"""
    import psycopg2
    import pandas as pd
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="crypto_db",
            user="postgres",
            password="postgres"
        )
        
        # Top 10 cryptos du jour
        query = """
        SELECT 
            rang, symbole, nom, prix_usd, 
            variation_24h_pourcent, market_cap_usd,
            date_import, heure_import
        FROM crypto_temps_reel 
        WHERE date_import = CURRENT_DATE 
        AND rang <= 10
        ORDER BY rang;
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            report = f"""
RAPPORT CRYPTO QUOTIDIEN - {datetime.now().strftime('%Y-%m-%d')}
============================================

TOP 10 CRYPTOMONNAIES:
{df[['rang', 'symbole', 'nom', 'prix_usd', 'variation_24h_pourcent']].to_string(index=False)}

Market Cap Total: ${df['market_cap_usd'].sum() / 1e9:.2f} Md
Performance Moyenne: {df['variation_24h_pourcent'].mean():.2f}%
Dernière mise à jour: {df['heure_import'].iloc[0]}
            """
            print(report)
            return report
        else:
            return "Aucune donnée disponible pour aujourd'hui"
            
    except Exception as e:
        return f"Erreur génération rapport: {e}"

with DAG(
    'crypto_data_pipeline',
    default_args=default_args,
    description='Pipeline de données cryptomonnaies en temps réel',
    schedule_interval='*/30 * * * *',  # Toutes les 30 minutes
    catchup=False,
    tags=['crypto', 'spark', 'postgres'],
) as dag:

    start = DummyOperator(task_id='start')
    
    # Vérifications
    check_api_task = PythonOperator(
        task_id='check_coincap_api',
        python_callable=check_api
    )

    check_db_task = PythonOperator(
        task_id='check_database_connection',
        python_callable=check_db_connection
    )

    # Nettoyage des données anciennes
    cleanup_old_data = PostgresOperator(
        task_id='cleanup_old_data',
        postgres_conn_id='postgres_default',
        sql="""
        -- Garder seulement 7 jours d'historique
        DELETE FROM crypto_temps_reel 
        WHERE date_import < CURRENT_DATE - INTERVAL '7 days';
        
        -- Statistiques de nettoyage
        INSERT INTO pipeline_logs (operation, records_affected, timestamp)
        VALUES ('cleanup_old_data', 0, NOW());
        """
    )
    
    # Job Spark Scala (SEULEMENT cette tâche change)
    spark_crypto_job = SparkSubmitOperator(
        task_id='spark_crypto_processing',
        application='/opt/airflow/jars/crypto-spark-processor.jar',  # MAINTENANT JAR Scala
        conn_id='spark_default',
        application_args=[
            '{{ var.value.coincap_url }}',
            '{{ var.value.postgres_url }}',
            '{{ var.value.pg_user }}',
            '{{ var.value.pg_password }}'
        ],
        jars='/opt/airflow/jars/postgresql-42.5.0.jar',
        driver_memory='2g',
        executor_memory='2g',
        num_executors=2,
        executor_cores=2,
        verbose=False
    )

    # Vérification des résultats Spark
    verify_spark_task = PythonOperator(
        task_id='verify_spark_results',
        python_callable=verify_spark_results
    )

    # Vérification de la qualité des données
    verify_results = PostgresOperator(
        task_id='verify_data_quality',
        postgres_conn_id='postgres_default',
        sql="""
        -- Vérifier qu'on a bien les top 10 cryptos
        DO $$
        DECLARE
            record_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO record_count 
            FROM crypto_temps_reel 
            WHERE date_import = CURRENT_DATE 
            AND rang <= 10;
            
            IF record_count >= 10 THEN
                INSERT INTO pipeline_logs (operation, records_affected, timestamp)
                VALUES ('data_quality_check', record_count, NOW());
            ELSE
                RAISE EXCEPTION 'Données insuffisantes: % enregistrements', record_count;
            END IF;
        END $$;
        """
    )

    # Génération de rapport
    generate_report = PythonOperator(
        task_id='generate_daily_report',
        python_callable=generate_daily_report
    )

    # Notification de succès
    success_notification = EmailOperator(
        task_id='send_success_email',
        to=['komimissiamenou97@gmail.com','sabuetshibangualidor@gmail.com'],
        subject='Pipeline Crypto Réussi - {{ ds }}',
        html_content="""
        <h3>Pipeline Crypto Exécuté avec Succès</h3>
        <p>Le pipeline de données cryptomonnaies a été exécuté avec succès le {{ ds }}.</p>
        <p><strong>Détails:</strong></p>
        <ul>
            <li>Données mises à jour depuis CoinCap API</li>
            <li>Stockage dans PostgreSQL</li>
            <li>Rapport quotidien généré</li>
        </ul>
        <br>
        <p><em>Système de surveillance crypto - Airflow + Spark + PostgreSQL</em></p>
        """
    )

    end = DummyOperator(task_id='end')

    # Workflow
    start >> [check_api_task, check_db_task] >> cleanup_old_data >> spark_crypto_job
    spark_crypto_job >> verify_spark_task >> verify_results >> generate_report >> success_notification >> end