{% set src_table = 'shipments' %}

{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
    select

    CAST(shipment_id AS BIGINT) AS shipment_id,
    CAST(order_id AS BIGINT) AS order_id,
    CAST(TRIM(carrier) AS STRING) AS carrier,
    CAST(shipped_at AS TIMESTAMP) AS shipped_at,
    CAST(delivered_at AS TIMESTAMP) AS delivered_at,
    CAST(ship_cost AS NUMERIC(12, 2)) AS ship_cost,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts

  from bronze_parquet
)

-- Step 3: Final output
select * from typed

