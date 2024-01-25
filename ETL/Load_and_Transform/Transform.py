from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, DateType

KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
KAFKA_TOPIC = 'Belarus_Weather'
HDFS_OUTPUT_PATH = '/hdfs/'
CHECKPOINT_OUTPUT_PATH = '/checkpoint/'

schema = StructType([
    StructField("city", StringType(), True),
    StructField("date", DateType(), True),
    StructField("max_temp_c", DoubleType(), True),
    StructField("max_temp_f", DoubleType(), True),
    StructField("min_temp_c", DoubleType(), True),
    StructField("min_temp_f", DoubleType(), True),
    StructField("avg_temp_c", DoubleType(), True),
    StructField("avg_temp_f", DoubleType(), True),
    StructField("condition_text", StringType(), True),
    StructField("wind_mph", DoubleType(), True),
    StructField("wind_kph", DoubleType(), True),
    StructField("precipitation_mm", DoubleType(), True),
    StructField("precipitation_in", DoubleType(), True),
    StructField("humidity", DoubleType(), True),
])


def create_spark_session():
    return SparkSession.builder \
        .appName("KafkaWeatherProcessing") \
        .config("spark.cassandra.connection.host", "cassandra") \
        .config("spark.cassandra.connection.port", "9042") \
        .getOrCreate()


def main():
    spark = create_spark_session()
    spark.conf.set("spark.sql.adaptive.enabled", "false")
    spark.conf.set("spark.kafka.consumer.ignoreExceptions", "true")

    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .load()

    json_data = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    local_query = json_data \
        .writeStream \
        .outputMode("append") \
        .format("parquet") \
        .option("path", HDFS_OUTPUT_PATH) \
        .option("checkpointLocation", CHECKPOINT_OUTPUT_PATH + 'hdfs') \
        .start()

    cassandra_query = json_data \
        .writeStream \
        .outputMode("append") \
        .format("org.apache.spark.sql.cassandra") \
        .option("keyspace", 'weather') \
        .option("table", "r_city") \
        .option("checkpointLocation", CHECKPOINT_OUTPUT_PATH + 'cassandra') \
        .start()

    local_query.awaitTermination()
    cassandra_query.awaitTermination()


if __name__ == "__main__":
    main()
