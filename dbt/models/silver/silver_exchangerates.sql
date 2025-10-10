{{
  config(
    materialized='incremental',
    unique_key='date',
    on_schema_change='merge'
  ) 
}}

SELECT 
    date,
    currency,
    rate_to_aud,
    ingestion_ts
FROM {{ ref('stg_exchangerates') }} 
{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}