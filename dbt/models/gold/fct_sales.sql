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
  oh.order_date,
  oh.customer_id,
  ol.product_id,
  p.currency AS product_currency,

  -- Monetary values rounded to 2 decimal places
  ROUND(ol.qty * ol.unit_price, 2) AS gross_amount,
  ROUND(ol.qty * ol.unit_price * er.rate_to_aud, 2) AS gross_amount_aud,
  ROUND(er.rate_to_aud, 2) AS rate_to_aud,

  -- Percentages as whole numbers (e.g., 15%) and rounded
  ROUND(100 * ol.line_discount_pct, 2) AS line_discount_pct,
  ROUND(100 * ol.tax_pct, 2) AS tax_pct,

  -- Total amount with discount and tax, rounded
  ROUND(
    (ol.qty * ol.unit_price) 
    * (1 - COALESCE(ol.line_discount_pct, 0.0)) 
    * (1 + COALESCE(ol.tax_pct, 0.0)), 
    2
  ) AS total_amount,


   ROUND(
     (ol.qty * ol.unit_price * er.rate_to_aud) 
     * (1 - COALESCE(ol.line_discount_pct, 0.0)) 
     * (1 + COALESCE(ol.tax_pct, 0.0)), 
     2
   ) AS total_amount_aud,

  oh.store_id,
  oh.channel,
  oh.payment_method,
  oh.coupon_code,
  ROUND(oh.shipping_fee, 2) AS shipping_fee_aud,
  oh.currency AS order_currency,
  oh.ingestion_ts AS ingestion_ts
    -- From orderslines


 --   ol.qty,
 --   ol.unit_price,

 --   ol.ingestion_ts ingestion_ts


FROM {{ ref('silver_orders') }} oh
JOIN {{ ref('silver_orderslines') }} ol 
     ON oh.order_id = ol.order_id
JOIN {{ ref('dim_product_scd') }} p 
     ON ol.product_id = p.product_id 
JOIN {{ ref('silver_exchangerates') }} er
     ON oh.order_date = er.date AND p.currency = er.currency

WHERE p.is_current IS TRUE
{% if is_incremental() %}
  AND oh.ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}
