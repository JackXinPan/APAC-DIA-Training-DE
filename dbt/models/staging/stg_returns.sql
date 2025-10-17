{% set src_table = 'returnscombined' %}
{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),


-- Step 2: Apply transformations
typed as (
select

    CAST(return_id AS BIGINT) AS return_id,
    CAST(order_id AS BIGINT) AS order_id,
    CAST(product_id AS BIGINT) AS product_id,
    CAST(return_ts AS TIMESTAMP) AS return_ts,
    CAST(qty AS INT) AS qty,
    CAST(TRIM(reason) AS VARCHAR) AS reason,
    CAST(TRIM(source_version) AS VARCHAR) AS source_version,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts,
    CAST(TRIM(_dlt_load_id) AS VARCHAR) AS _dlt_load_id,
    CAST(TRIM(_dlt_id) AS VARCHAR) AS _dlt_id,
    CAST(TRIM(return_reason_code) AS VARCHAR) AS return_reason_code

 
from bronze_parquet
)

-- Step 3: Final output
select *
from typed