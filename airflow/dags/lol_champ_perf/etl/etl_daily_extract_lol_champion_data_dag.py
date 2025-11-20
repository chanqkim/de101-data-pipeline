from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from src.lol_champ_perf.api_client import get_lol_champ_data

with DAG(
    dag_id="lol_champ_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False
) as dag:

    extract_lol_champion_data = PythonOperator(
        task_id="extract_lol_champion_data",
        python_callable=get_lol_champ_data
    )

    