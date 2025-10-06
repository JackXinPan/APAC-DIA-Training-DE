{{
  config(
    materialized='incremental',
    unique_key='sale_id',
    on_schema_change='merge'
  ) 
}}

SELECT 
    -- From ordersheader
 --   oh.order_id,
    ol.order_id || '-' || ol.line_number AS sale_id,
    oh.order_ts,
 --   oh.order_dt_local AS order_dt,
    oh.customer_id,
    ol.product_id,
    ol.qty * ol.unit_price AS gross_amount,
     --                    AS gross_amount_aud,
     --                    AS total_amount,
    --                      AS total_amount_aud,
    ol.qty * ol.unit_price,
    oh.store_id,
    oh.channel,
    oh.payment_method,
    oh.coupon_code,
    oh.shipping_fee,
    oh.currency,
    oh.ingestion_ts AS header_ingestion_ts,

    -- From orderslines
    ol.line_number,

 --   ol.qty,
 --   ol.unit_price,
    ol.line_discount_pct,
    ol.tax_pct,
    ol.ingestion_ts AS line_ingestion_ts

FROM {{ ref('silver_orders') }} oh
JOIN {{ ref('silver_orderslines') }} ol 
 join silver er   oh.currency,

  ON oh.order_id = ol.order_id

{% if is_incremental() %}
  WHERE ol.ingestion_ts > (
    SELECT MAX(line_ingestion_ts) FROM {{ this }}
  )
{% endif %}