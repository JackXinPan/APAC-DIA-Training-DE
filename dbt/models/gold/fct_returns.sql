{{
  config(
    materialized='incremental',
    unique_key='return_id',
    on_schema_change='merge'
  ) 
}}

SELECT 

    return_id,
      order_id,
        product_id 
        ,return_ts
        ,  qty
reason ,
return_reason_code,
 source_version,
  ingestion_ts 

FROM {{ ref('silver_returns') }} r
JOIN {{ ref('dim_product_scd') }} p 
     ON r.product_id = p.product_id 
JOIN {{ ref('silver_orders') }} o 
     ON r.order_id = o.order_id


{% if is_incremental() %}
WHERE ingestion_ts > (
  SELECT MAX(ingestion_ts) FROM {{ this }}
)
{% endif %}
