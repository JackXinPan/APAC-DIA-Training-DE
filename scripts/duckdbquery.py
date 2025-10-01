
# scripts/bronze_dlt_pipeline.py
import dlt
from dlt.sources.filesystem import filesystem
import pyarrow as pa
import sys
import os
import pytz
import pandas as pd
import duckdb
from datetime import datetime, timedelta, date
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from my_schemas.my_schemas import *

# Define the UTC+8 timezone
utc_plus_8 = pytz.timezone('Australia/Perth')

# Construct relative path to DuckDB file
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
duckdb_path = os.path.join(project_root, "duckdb", "warehouse.duckdb")

# Connect to the DuckDB file
con = duckdb.connect(duckdb_path)

# List tables in the 'raw' schema
tables = con.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'raw_dataset'
""").fetchall()

print("Tables in 'raw_dataset' schema:", tables)

# Example: Query a table from the 'raw' schema
# Replace 'customers' with any actual table name from the list above
df = con.execute("SELECT * FROM raw_dataset.customers LIMIT 10").fetchdf()
print(df)


main_stg_tables = con.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'main_stg'
""").fetchall()

print("Tables in 'main_stg' schema:", main_stg_tables)


# List all schemas
schemas = con.execute("""
    SELECT schema_name
    FROM information_schema.schemata
""").fetchall()
print("Schemas in database:", schemas)




relationship = con.execute("""
    
SELECT distinct event_type
FROM main_stg.stg_events s

""").fetchall()
print("Schemas in database:", relationship)
