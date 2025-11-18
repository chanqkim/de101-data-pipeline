from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def hello():
    print('Hello Airflow')

with DAG(dag_id='example_dag', start_date=datetime(2025,1,1), schedule_interval='@daily') as dag:
    task = PythonOperator(task_id='hello_task', python_callable=hello)
