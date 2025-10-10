{{
  config(
    materialized='incremental',
    unique_key=['return_id'],
    on_schema_change='merge'
  ) 
}}

SELECT 
    return_id,
      order_id,
        product_id 
        ,return_ts
        ,  qty
,reason ,
return_reason_code,
 source_version,
  ingestion_ts 
FROM {{ ref('stg_returns') }}

{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}