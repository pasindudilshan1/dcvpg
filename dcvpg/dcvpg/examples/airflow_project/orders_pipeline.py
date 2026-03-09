from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from orchestrators.airflow.operators.contract_validator import DataContractValidatorOperator

def dummy_extract():
    print("Extracting data...")

def dummy_transform():
    print("Transforming data...")

def dummy_load():
    print("Loading data...")

with DAG(
    dag_id='dcvpg_example_orders_pipeline',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:

    # The single line integration of DCVPG into any Airflow DAG
    validate = DataContractValidatorOperator(
        task_id='validate_orders_contract',
        contract='orders_raw',              # Must exist in your contracts/ dir
        source_conn='local_orders_csv',     # Must exist in dcvpg.config.yaml
        config_path='./examples/airflow_project/dcvpg.config.yaml',
        on_failure='quarantine_and_alert'
    )

    extract = PythonOperator(task_id='extract', python_callable=dummy_extract)
    transform = PythonOperator(task_id='transform', python_callable=dummy_transform)
    load = PythonOperator(task_id='load', python_callable=dummy_load)

    # validate first, if it fails, downstream is halted automatically by Airflow
    validate >> extract >> transform >> load
