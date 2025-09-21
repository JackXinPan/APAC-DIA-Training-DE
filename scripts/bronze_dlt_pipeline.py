# scripts/bronze_dlt_pipeline.py
import dlt
from dlt.sources.filesystem import filesystem
import pyarrow as pa
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytz
import pandas as pd

from my_schemas.my_schemas import *

from datetime import datetime, timedelta, date

# Define the UTC+8 timezone
utc_plus_8 = pytz.timezone('Australia/Perth')  

# Configure destinations of where transformed data should go (folder directory)
duckdb_dest = dlt.destinations.duckdb(
    credentials="C:/Users/jpan/Documents/Assessment/APAC-DIA-Training-DE/duckdb/warehouse.duckdb"
)

#setup a DuckDB destination -  a local analytics database
parquet_dest = dlt.destinations.filesystem(
    bucket_url="lake/bronze/parquet",
    file_format="parquet"
)

#helper function to convert pyarrow schema to dictionary of dicts
def pyarrow_schema_to_dlt_columns(schema: pa.Schema) -> dict:
    return {
        field.name: {
            "name": field.name,
            "data_type": str(field.type)
        }
        for field in schema
    }


#define source pipeline to read raw data from the folder data_raw
@dlt.source(name="retail_bronze")
def retail_source(raw_path: str = "data_raw"):
    # resources are data loaders 
    # When you wrap a function like load_customers() with @dlt.resource, you're telling DLT: "This is a stream of records I want to load into a destination table."
    # customers becomes the destination table, and the @dlt.resource function acts as a data pipeline component that feeds it
    @dlt.resource(
        name="customers", # name of the py in the raw_data folder
        write_disposition="replace", # overwrite
        columns=pyarrow_schema_to_dlt_columns(customers_schema)  # Use PyArrow schema that is converted to dict # schema grabbed the schema.py file
    )
    def load_customers():
        # Read CSV and yield data will load in the data from the data_raw file 
        file_path = os.path.join(raw_path, "customers.csv")
        customerdf = pd.read_csv(file_path)
        for record in customerdf.to_dict(orient="records"):
            yield record #Each record is streamed one at a time, allowing DLT to process efficiently and apply schema validation.
 
#   @dlt.resource( #order
#        name="orders",
#        write_disposition="append",
#       primary_key="order_id",
#        merge_key="order_id"
#    )
#    def load_orders():
#        # Incremental loading with automatic dedup
#        pass
    
    @dlt.transformer(
        data_from=load_customers,
        write_disposition="replace"
    )
    def add_audit_columns(record):
        # Add ingestion_ts, src_filename, etc.
        return {
            **record,
           "ingestion_ts": datetime.now(utc_plus_8),
            "src_filename": dlt.current.source_state().get("file")
        }
    
    # DLT handles schema validation automatically      
    return [load_customers]   
#   return [
#        add_audit_columns,
#        load_orders
#        ,load_customers
        # ... other resources
#    ]

#When you run pipeline.run(retail_source()), DLT orchestrates the whole flow:
#Reads from the source
#Applies transformations (like add_audit_columns) and schema validation
#Loads into the destination table (customers)

pipeline = dlt.pipeline(pipeline_name="retail_bronze", destination=duckdb_dest)
info = pipeline.run(retail_source())
print(info)
