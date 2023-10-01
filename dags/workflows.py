import sys
import os
current_dir = os.getcwd()
project_directory = os.path.dirname(current_dir)
sys.path.append(project_directory)
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
from app.main import scrape_and_write_flights
from lib.utils import week_from_date

default_args = {
    'owner': 'francesco',
    'start_date': datetime(2023, 9, 18),
    'retries': 1,
}

# Define the DAG
dag = DAG(
    'flight_data_workflow',
    default_args=default_args,
    schedule_interval=timedelta(weeks=1),  # Run every week
    catchup=False
)

date = "2023-09-25"
next_week_date = week_from_date(date, 1)
args = ["AMS", "ROM", date, 200, 0]

python_task = PythonOperator(
    task_id='scrape_and_write_flights',
    python_callable=scrape_and_write_flights,
    op_args=args,
    dag=dag
)

spark_script_path = os.path.join(project_directory, "app/spark_script.py")
spark_task = SparkSubmitOperator(
    task_id='call_spark_script',
    conn_id='spark_standalone_conn',
    application=spark_script_path,
    executor_memory="4g",
    dag=dag
)

# Set task dependencies
python_task >> spark_task

date = next_week_date
