
{% set src_table = 'sensors' %}
{{ config(materialized='table', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
  select
    cast(sensor_ts as timestamp) as sensor_ts,
    cast(store_id as bigint) as store_id,
    cast(shelf_id as string) as shelf_id,
    cast(temperature_c as decimal(5, 2)) as temperature_c,
    cast(humidity_pct as decimal(5, 2)) as humidity_pct,
    cast(battery_mv as int) as battery_mv
  from bronze_parquet
)

-- Step 3: Final output
select * from typed
where sensor_ts is not null

and temperature_c between 0 and 50
    and humidity_pct between 0 and 100
and battery_mv >= 1000
and 
 store_id IN (
    SELECT store_id
    FROM main_stg.stg_stores
) --cleaned out store ids due to lat/long anomalies to keep referential integrity
