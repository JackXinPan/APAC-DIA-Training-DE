{% set src_table = 'orderslines' %}
{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
  select
    cast(order_id as bigint) as order_id,
    cast(line_number as int) as line_number,
    cast(product_id as bigint) as product_id,
    cast(qty as int) as qty,
    cast(unit_price as decimal(12, 4)) as unit_price,
    cast(line_discount_pct as decimal(5, 4)) as line_discount_pct,
    cast(tax_pct as decimal(5, 4)) as tax_pct,
    cast(ingestion_ts as timestamp) as ingestion_ts
  from bronze_parquet
)

-- Step 3: Final output
select * from typed
WHERE 
 product_id IN (
    SELECT product_id
    FROM main_stg.stg_products
) --cleaned out product ids due to intentdbt ruional anomalies or incorrect product ids. to keep referential integrity

