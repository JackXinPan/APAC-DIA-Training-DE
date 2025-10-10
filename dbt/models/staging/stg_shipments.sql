{% set src_table = 'shipments' %}

{{ config(materialized='table', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
    select
        cast(shipment_id as bigint) as shipment_id,
        cast(order_id as bigint) as order_id,
        cast(carrier as string) as carrier,
        cast(shipped_at as timestamp) as shipped_at,
        cast(delivered_at as timestamp) as delivered_at,
        cast(ship_cost as numeric(12, 2)) as ship_cost,
        cast(ingestion_ts as timestamp) as ingestion_ts
  from bronze_parquet
)

-- Step 3: Final output
select * from typed

