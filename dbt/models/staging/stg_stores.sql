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
    cast(ingestion_ts as timestamp) as ingestion_ts,
    case when trim(close_dt) = '' THEN NULL ELSE cast(close_dt as date)
        END AS close_dt,
      row_number() over (
        partition by store_code
        order by store_id asc 
      ) as row_num
 
from bronze_parquet
)

-- Step 3: Final output
select store_id,
        store_code,
        name,
        channel,
        region,
        state,
        latitude,
        longitude,
        open_dt,
        close_dt,
        ingestion_ts
 from typed
where latitude between -90 and 90
and longitude between -180 and 180 
and row_num = 1