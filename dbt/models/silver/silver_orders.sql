{{
  config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='merge'
  ) 
}}

SELECT 
    order_id,
    order_ts,
    order_dt_local AS order_date,
    customer_id,
    store_id,
    channel,
    payment_method,
    coupon_code,
    shipping_fee,
    currency,
    ingestion_ts
FROM {{ ref('stg_ordersheader') }} 
{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}