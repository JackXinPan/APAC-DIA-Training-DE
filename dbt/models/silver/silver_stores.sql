{{
  config(
    materialized='table'
  ) 
}}

SELECT 
        store_id,
        store_code,
        name,
        channel,
        region,
        state,
        latitude,
        longitude,
        open_dt as open_date,
        close_dt as close_date,
        ingestion_ts

FROM {{ ref('stg_stores') }}
WHERE latitude between -90 and 90
  and longitude between -180 and 180 
  
{% if is_incremental() %}
  and ingestion_ts > (
    SELECT MAX(line_ingestion_ts) FROM {{ this }}
  )
{% endif %}