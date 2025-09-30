{% set src_table = 'stores' %}

{{ config(materialized='table', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),


-- Step 2: Apply transformations
typed as (
select
    cast(store_id as bigint) as store_id,
    cast(store_code as string) as store_code,
    cast(name as string) as name,
    cast(channel as string) as channel,
    cast(region as string) as region,
    cast(state as string) as state,
    cast(latitude as double) as latitude,
    cast(longitude as double) as longitude,
    cast(open_dt as date) as open_dt,
    case when trim(close_dt) = '' THEN NULL ELSE cast(close_dt as date)
        END AS close_dt 
from bronze_parquet
)

-- Step 3: Final output
select * from typed
