from datetime import datetime

from airflow.operators.python import PythonOperator

from airflow import DAG
from src.lol_champ_perf.api_client import get_lol_champ_data
from src.lol_champ_perf.crawler import (
    fetch_all_champion_tier,
    fetch_champion_build_data,
)

with DAG(
    dag_id="lol_champ_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
) as dag:
    # etl lol champion data
    extract_lol_champion_data = get_lol_champ_data()

    # etl all_champion_tier
    fetch_all_champion_tier = fetch_all_champion_tier(
        tier=["all"], position=["all"], region=["all"]
    )

    # Dynamic Task Mapping: champion build data
    fetch_champion_build_data.expand(
        champion=extract_lol_champion_data,
        tier=["all"],
        region=["all"],
    )

    # run lol champion data, all_champion_tier etl simultaneously
    [extract_lol_champion_data, fetch_all_champion_tier]
