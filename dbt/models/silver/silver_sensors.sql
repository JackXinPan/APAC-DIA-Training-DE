{{
  config(
    materialized='incremental',
    unique_key=['sensor_ts', 'store_id', 'shelf_id'],
    on_schema_change='merge'
  ) 
}}

SELECT 
    sensor_ts,
    store_id,
    shelf_id,
    temperature_c,
    humidity_pct,
    battery_mv,
    ingestion_ts

FROM {{ ref('stg_sensors') }}

{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}