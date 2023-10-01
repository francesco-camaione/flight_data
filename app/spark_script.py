import os
import sys

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from services.database import Database
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DateType, IntegerType
from pyspark.sql.functions import mean, col, min
from datetime import datetime, timedelta

spark = SparkSession.builder \
    .config('spark.driver.host', "localhost") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.shuffle.partition", "200") \
    .master("local") \
    .getOrCreate()

db = Database()
flights_data = db.select_one_way_flights()
schema = StructType([
    StructField("flight_id", StringType()),
    StructField("origin", StringType()),
    StructField("destination", StringType()),
    StructField("departure_time", StringType()),
    StructField("arrival_time", StringType()),
    StructField("duration", StringType()),
    StructField("price", IntegerType()),
    StructField("stops", IntegerType()),
    StructField("date", DateType())
])
df = spark.createDataFrame(flights_data, schema=schema)

# Define the number of weeks from now
weeks_from_now = 2

# Compute the starting date of the week (Monday) and the ending date (Sunday), two weeks from now
current_date = datetime.now()
two_weeks_from_now = current_date + timedelta(weeks=weeks_from_now)
starting_week_date = two_weeks_from_now - timedelta(days=two_weeks_from_now.weekday())
ending_week_date = starting_week_date + timedelta(days=6)

# Filter df based on the date range
filtered_df = df.filter((col("date") >= starting_week_date.strftime('%Y-%m-%d')) &
                        (col("date") <= ending_week_date.strftime('%Y-%m-%d')))
filtered_df.show(5)

mean_price = df.select(mean("price")).first()[0]
min_price_of_the_week = filtered_df.select(min("price")).first()[0]
print("min_price_of_the_week: ", min_price_of_the_week, "mean", mean_price)




