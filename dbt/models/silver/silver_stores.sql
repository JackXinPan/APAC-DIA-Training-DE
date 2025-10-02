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

{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(line_ingestion_ts) FROM {{ this }}
  )
{% endif %}