
{{ 
  config(
    materialized='incremental',
    unique_key=['order_id', 'line_number'],
    on_schema_change='merge'
  ) 
}}

SELECT 
    order_id,
    line_number,
    product_id,
    qty,
    unit_price,
    line_discount_pct,
    tax_pct,
    ingestion_ts

FROM {{ ref('stg_orderslines') }} 

{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}