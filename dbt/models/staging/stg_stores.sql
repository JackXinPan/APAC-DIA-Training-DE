{% set src_table = 'stores' %}

{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),


-- Step 2: Apply transformations
typed as (
SELECT
    CAST(store_id AS BIGINT) AS store_id,
    CAST(TRIM(store_code) AS STRING) AS store_code,
    CAST(TRIM(name) AS STRING) AS name,
    CAST(TRIM(channel) AS STRING) AS channel,
    CAST(TRIM(region) AS STRING) AS region,
    CAST(TRIM(state) AS STRING) AS state,
    CAST(latitude AS DOUBLE) AS latitude,
    CAST(longitude AS DOUBLE) AS longitude,
    CAST(open_dt AS DATE) AS open_dt,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts,
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
--where latitude between -90 and 90
--and longitude between -180 and 180 
--and row_num = 1