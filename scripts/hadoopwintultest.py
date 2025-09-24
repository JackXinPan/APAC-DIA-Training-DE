from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("WinutilsTest") \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")

df = spark.range(5)
df.show()
