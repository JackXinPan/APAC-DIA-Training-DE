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
    ol.line_number,
    oh.order_dt_local AS order_dt,
    oh.customer_id,
    ol.product_id,
    p.currency as product_currency,
    ol.qty * ol.unit_price AS gross_amount,
    ol.qty * ol.unit_price * er.exchange_rate AS gross_amount_aud,
    ol.line_discount_pct,
    ol.tax_pct,
    (ol.qty * ol.unit_price) * (1-COALESCE(ol.line_discount_pct, 0.0))*(1+COALESCE(ol.tax_pct, 0.0)) AS total_amount,
    (ol.qty * ol.unit_price * er.exchange_rate)*(1-COALESCE(ol.line_discount_pct, 0.0))*(1+COALESCE(ol.tax_pct, 0.0)) AS total_amount_aud,
    ol.qty * ol.unit_price,
    oh.store_id,
    oh.channel,
    oh.payment_method,
    oh.coupon_code,
    oh.shipping_fee as shipping_fee_aud,
    oh.currency as order_currency,
--    oh.ingestion_ts AS header_ingestion_ts,

    -- From orderslines


 --   ol.qty,
 --   ol.unit_price,

 --   ol.ingestion_ts AS line_ingestion_ts

FROM {{ ref('silver_orders') }} oh
JOIN {{ ref('silver_orderslines') }} ol 
     ON oh.order_id = ol.order_id
JOIN {{ ref('dim_product_scd') }} p 
    on ol.product_id = p.product_id Where p.is_current IS TRUE
JOIN {{ ref('silver_exchangerates') }} er
    on oh.order_dt_local= er.date AND p.currency = er.currency

 

{% if is_incremental() %}
  WHERE ol.ingestion_ts > (
    SELECT MAX(line_ingestion_ts) FROM {{ this }}
  )
{% endif %}