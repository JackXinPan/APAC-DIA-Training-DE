{{
  config(
    materialized='table'
  ) 
}}

SELECT 
    supplier_id,
        supplier_code,
        name,
        country_code,
        lead_time_days,
        preferred,
        ingestion_ts

FROM {{ ref('stg_suppliers') }}

{% if is_incremental() %}
  WHERE ol.ingestion_ts > (
    SELECT MAX(line_ingestion_ts) FROM {{ this }}
  )
{% endif %}