{% set src_table = 'products' %}

{{ config(materialized='table', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),


-- Step 2: Apply transformations
typed as (
select
    cast(product_id as bigint) as product_id,
    cast(sku as string) as sku,
    cast(name as string) as name,
    cast(category as string) as category,
    cast(subcategory as string) as subcategory,
    cast(current_price as numeric(12, 4)) as current_price,
    cast(currency as string) as currency,
    cast(is_discontinued as boolean) as is_discontinued,
    cast(introduced_dt as date) as introduced_dt,
    cast(discontinued_dt as date) as discontinued_dt,
    cast(ingestion_ts as timestamp) as ingestion_ts

from bronze_parquet
)

-- Step 3: Final output
select * from typed

