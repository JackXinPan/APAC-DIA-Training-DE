
{% set src_table = 'sensors' %}
{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
  select


    CAST(sensor_ts AS TIMESTAMP) AS sensor_ts,
    CAST(store_id AS BIGINT) AS store_id,
    CAST(TRIM(shelf_id) AS STRING) AS shelf_id,
    CAST(temperature_c AS DECIMAL(5, 2)) AS temperature_c,
    CAST(humidity_pct AS DECIMAL(5, 2)) AS humidity_pct,
    CAST(battery_mv AS INT) AS battery_mv,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts


  from bronze_parquet
)

-- Step 3: Final output
select * from typed
where sensor_ts is not null
-- moved to curated
--and temperature_c between 0 and 50 
--    and humidity_pct between 0 and 100
--and battery_mv >= 1000
and 
 store_id IN (
    SELECT store_id
    FROM main_stg.stg_stores
) --cleaned out store ids due to lat/long anomalies to keep referential integrity
