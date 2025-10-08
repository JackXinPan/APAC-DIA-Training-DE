# scripts/bronze_dlt_pipeline.py
import dlt
from dlt.sources.filesystem import filesystem
import pyarrow as pa
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytz
import pandas as pd
import duckdb
from my_schemas.my_schemas import *

from datetime import datetime, timedelta, date
import json

from deltalake import DeltaTable
# Define the UTC+8 timezone
utc_plus_8 = pytz.timezone('Australia/Perth')  

# Configure destinations of where transformed data should go 
#setup a DuckDB destination -  a local analytics database
duckdb_dest = dlt.destinations.duckdb(
    credentials="duckdb/warehouse.duckdb"
)


parquet_dest = dlt.destinations.filesystem(
    bucket_url="lake/bronze/parquet",
    file_format="parquet"
)

# helper function to convert pyarrow schema to dictionary of dicts + convert data types to DLT compatible
def pyarrow_schema_to_dlt_columns(schema: pa.Schema) -> dict:
    # Mapping from PyArrow types to DLT-compatible types
    type_map = {
        "int64": "bigint",
        "string": "text",
        "float64": "double",
        "bool": "bool",
        "date32": "date",
        "timestamp[us]": "timestamp",#### may need to be changed downstream
        "json": "json"
    }

    return {
        field.name: {
            "name": field.name,
            "data_type": type_map.get(str(field.type), "text")  # default to 'text' if unknown
        }
        for field in schema
    }


# Helper function to enrich records
def enrich_record(record):
    return {
        **record,
        "ingestion_ts": datetime.now(utc_plus_8),
        "src_filename": dlt.current.source_state().get("file")
    }


#define source pipeline to read raw data from the folder data_raw
@dlt.source(name="retail_bronze") # schema
def retail_source(raw_path: str = "data_raw"):
    # resources are data loaders 
    # When you wrap a function like load_customers() with @dlt.resource, you're telling DLT: "This is a stream of records I want to load into a destination table."
    # customers becomes the destination table, and the @dlt.resource function acts as a data pipeline component that feeds it
    @dlt.resource(
        write_disposition="replace", # overwrite
        columns=pyarrow_schema_to_dlt_columns(customers_schema),  # Use PyArrow schema that is converted to dict # schema grabbed the schema.py file
    )
    def load_customers():
        # Read CSV and yield data will load in the data from the data_raw file 
        print("Loading resource: customers")
        file_path = os.path.join(raw_path, "customers.csv")
        customersdf = pd.read_csv(file_path)
        for record in customersdf.to_dict(orient="records"):
            yield record #Each record is streamed one at a time, allowing DLT to process efficiently and apply schema validation.
    @dlt.resource(
        write_disposition="replace", # overwrite
        columns=pyarrow_schema_to_dlt_columns(products_schema),  # Use PyArrow schema that is converted to dict # schema grabbed the schema.py file
    )
    def load_products():
        # Read CSV and yield data will load in the data from the data_raw file 
        print("Loading resource: products")
        file_path = os.path.join(raw_path, "products.csv")
        productsdf = pd.read_csv(file_path)
        for record in productsdf.to_dict(orient="records"):
            yield record #Each record is streamed one at a time, allowing DLT to process efficiently and apply schema validation.
    @dlt.resource(
            write_disposition="replace", # overwrite
            columns=pyarrow_schema_to_dlt_columns(stores_schema),  # Use PyArrow schema that is converted to dict # schema grabbed the schema.py file
    )
    def load_stores():
        # Read CSV and yield data will load in the data from the data_raw file
        print("Loading resource: stores") 
        file_path = os.path.join(raw_path, "stores.csv")
        storesdf = pd.read_csv(file_path)
        for record in storesdf.to_dict(orient="records"):
            yield record #Each record is streamed one at a time, allowing DLT to process efficiently and apply schema validation.
    @dlt.resource(
            write_disposition="replace", # overwrite
            columns=pyarrow_schema_to_dlt_columns(suppliers_schema),  # Use PyArrow schema that is converted to dict # schema grabbed the schema.py file
    )
    def load_suppliers():
        # Read CSV and yield data will load in the data from the data_raw file 
        print("Loading resource: suppliers")
        file_path = os.path.join(raw_path, "suppliers.csv")
        suppliersdf = pd.read_csv(file_path)
        for record in suppliersdf.to_dict(orient="records"):
            yield record #Each record is streamed one at a time, allowing DLT to process efficiently and apply schema validation.

    @dlt.resource( #ordersheader
            write_disposition="append",
            columns=pyarrow_schema_to_dlt_columns(orders_header_schema),  # Use PyArrow schema that is converted to dict # schema grabbed the schema.py file
            primary_key="order_id",
            merge_key="order_id" # is there a reason why there is a merge key? If it's just appending then append on the ts watermark
        )

    def load_ordersheader(updated_after=dlt.sources.incremental("order_ts")):
        print("Loading resource: ordersheader")
        file_path = os.path.join(raw_path, "orders_header.csv")
        ordersheaderdf = pd.read_csv(file_path)
        for record in ordersheaderdf.to_dict(orient="records"):
            if updated_after.last_value is None or record["order_ts"] > updated_after.last_value:
                    yield record  
            

    @dlt.resource( #orderslines
            write_disposition="append",
            columns=pyarrow_schema_to_dlt_columns(orders_lines_schema), # Use PyArrow schema that is converted to dict # schema grabbed the schema.py file
            primary_key=["order_id", "line_number"],
            merge_key=["order_id", "line_number"]
        )


    def load_orderslines(updated_after=dlt.sources.incremental("order_id")):
        print("Loading resource: orderslines")
        file_path = os.path.join(raw_path, "orders_lines.csv")
        orderslinesdf = pd.read_csv(file_path)
        for record in orderslinesdf.to_dict(orient="records"):
            if updated_after.last_value is None or record["order_id"] > updated_after.last_value: #it's monotomically increasing
                yield record


    @dlt.resource(#events
        write_disposition="append",
        primary_key="event_id",
        columns=pyarrow_schema_to_dlt_columns(events_schema)
    )
    def load_events(updated_after=dlt.sources.incremental("envelope.event_ts")):
        print("Loading resource: events")       
        file_path = os.path.join(raw_path, "events.jsonl")  # single file
        with open(file_path, "r") as f:
            for line in f:
                record = json.loads(line)
                if updated_after.last_value is None or record["envelope"]["event_ts"] > updated_after.last_value: 
                    record["event_id"] = record["envelope"]["event_id"]  # flatten for primary key
                    yield record

    @dlt.resource(
        write_disposition="append",
        columns=pyarrow_schema_to_dlt_columns(sensors_schema)
    )
    def load_sensors(updated_after=dlt.sources.incremental("sensor_ts")):
        print("Loading resource: Sensors")
        file_path = os.path.join(raw_path, "sensors.csv")
        sensorsdf = pd.read_csv(file_path)

        # Convert last_value to datetime if it exists
        last_ts = None
        if updated_after.last_value:
            try:
                last_ts = datetime.fromisoformat(str(updated_after.last_value).strip())
                if last_ts.tzinfo is None or last_ts.tzinfo.utcoffset(last_ts) is None: #to check if timezone is naive
                    last_ts = utc_plus_8.localize(last_ts)

            except ValueError:
                print(f"Invalid last_value format: {updated_after.last_value}")

        for record in sensorsdf.to_dict(orient="records"):
            sensor_ts = record.get("sensor_ts")

            # Check for missing or empty timestamp
            if sensor_ts is None or str(sensor_ts).strip() == "" or pd.isna(sensor_ts):
                record["error_reason"] = "Missing or empty sensor_ts"
                continue

            try:
                record_ts = datetime.fromisoformat(str(sensor_ts).strip())
            except ValueError:
                record["error_reason"] = "Invalid sensor_ts format"
                continue

            # Compare only if last_ts is valid
            if last_ts is None or record_ts > last_ts:
                yield record


    @dlt.resource(#exchangerates
        write_disposition="replace",
        columns=pyarrow_schema_to_dlt_columns(exchange_rates_schema)
    )
    def load_exchangerates():
        print("Loading resource: Exchange Rates")      
        file_path = os.path.join(raw_path, "exchangerates.xlsx")  
        exchangratesdf = pd.read_excel(file_path, engine="openpyxl")  # Use openpyxl for .xlsx file
        for record in exchangratesdf.to_dict(orient="records"):
            yield record

 
    @dlt.resource(#shipments
        write_disposition="append",
        columns=pyarrow_schema_to_dlt_columns(shipments_schema)
    )
    def load_shipments(updated_after=dlt.sources.incremental("shipment_id")):
        print("Loading resource: Shipments")
        file_path = os.path.join(raw_path, "shipments.parquet")
        shipmentsdf = pd.read_parquet(file_path)
        for record in shipmentsdf.to_dict(orient="records"):
            if updated_after.last_value is None or record["shipment_id"] > updated_after.last_value: #it's monotomically increasing
             yield record
             
    @dlt.resource(#returns_v1
        write_disposition="append"
    ##    ,columns=pyarrow_schema_to_dlt_columns(returns_day1_schema)
    )
    def load_returns_v1():
        print("Loading resource: Returns")
        file_path = os.path.join(raw_path, "returns_v1")
        
        # Load Delta table and convert to Pandas DataFrame
        dt = DeltaTable(file_path)
        returnsdf = dt.to_pandas()

        for record in returnsdf.to_dict(orient="records"):
             yield record
    
    @dlt.resource(#returns_v2
        write_disposition="append"
      ##  ,schema_contract_settings={"columns": "evolve"}
    )
    def load_returns_v2():
        dt = DeltaTable(os.path.join(raw_path, "returns_v2"))
        df = dt.to_pandas()
        for record in df.to_dict(orient="records"):
            yield record

    
# Define transformers with appropriate write dispositions
    @dlt.transformer(data_from=load_customers, write_disposition="replace")
    def customers(record):
        return enrich_record(record)

    @dlt.transformer(data_from=load_products, write_disposition="replace")
    def products(record):
        return enrich_record(record)

    @dlt.transformer(data_from=load_stores, write_disposition="replace")
    def stores(record):
        return enrich_record(record)

    @dlt.transformer(data_from=load_suppliers, write_disposition="replace")
    def suppliers(record):
        return enrich_record(record)

    @dlt.transformer(data_from=load_ordersheader, write_disposition="append")
    def ordersheader(record):
        return enrich_record(record)

    @dlt.transformer(data_from=load_orderslines, write_disposition="append")
    def orderslines(record):
        return enrich_record(record)

    @dlt.transformer(data_from=load_events, write_disposition="append")
    def events(record):
        return enrich_record(record)

    @dlt.transformer(data_from=load_sensors, write_disposition="append")
    def sensors(record):
        return enrich_record(record)

    @dlt.transformer(data_from=load_exchangerates, write_disposition="append")
    def exchangerates(record):
        return enrich_record(record)

    @dlt.transformer(data_from=load_shipments, write_disposition="append")
    def shipments(record):
        return enrich_record(record)
    

    
    @dlt.transformer(data_from=load_returns_v1, write_disposition="append")
    def returnsall(record):
        record["source_version"] = "v1"
        return enrich_record(record)

    @dlt.transformer(data_from=load_returns_v2, write_disposition="append")
    def returnsall(record):
        record["source_version"] = "v2"
        return enrich_record(record)


    return [

        returnsall

    ]
#When you run pipeline.run(retail_source()), DLT orchestrates the whole flow:
#Reads from the source
#Applies transformations (like add_audit_columns) and schema validation
#Loads into the destination table (customers)
pipelineduck = dlt.pipeline(pipeline_name="raw", destination=duckdb_dest)

pipelinepq = dlt.pipeline(
    pipeline_name="retail_bronze",
    destination=parquet_dest,
    dataset_name="retail_bronze_dataset"
)


pipelineduck.drop()  # Clears previous format and schema
infoduck = pipelineduck.run(retail_source())
pipelinepq.drop()  # Clears previous format and schema
infopq = pipelinepq.run(retail_source(), loader_file_format="parquet") # have to specify the file format here as parquet for some reason

print(infoduck)
print(infopq)

print( "it's ran")