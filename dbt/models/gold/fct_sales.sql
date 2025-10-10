
{{ config(
    materialized='incremental',
    unique_key='sale_id',
    on_schema_change='merge'
) }}

WITH sales_enriched AS (
  SELECT 
    ol.order_id || '-' || ol.line_number AS sale_id,
    ol.order_id,
    ol.line_number,
    oh.order_ts,
    oh.order_date,
    oh.customer_id,
    ol.product_id,
    p.currency AS product_currency,
    qty,
    ROUND(ol.unit_price, 2)  as unit_price,
    ROUND(er.rate_to_aud, 2) AS rate_to_aud,
    --  actual percentages
    ROUND(100 * ol.line_discount_pct, 2) AS line_discount_pct,
    ROUND(100 * ol.tax_pct, 2) AS tax_pct,

    -- Order metadata
    oh.store_id,
    oh.channel,
    oh.payment_method,
    oh.coupon_code,
    ROUND(oh.shipping_fee, 2) AS shipping_fee_aud,
    oh.currency AS order_currency,
    oh.ingestion_ts AS ingestion_ts
  FROM {{ ref('silver_orderslines') }} ol
  JOIN {{ ref('silver_orders') }} oh 
       ON oh.order_id = ol.order_id
  JOIN {{ ref('silver_products') }} p 
       ON ol.product_id = p.product_id 
  JOIN {{ ref('silver_exchangerates') }} er
       ON oh.order_date = er.date AND p.currency = er.currency
  {% if is_incremental() %}
WHERE ol.ingestion_ts > (
  SELECT MAX(ingestion_ts) FROM {{ this }}
)
{% endif %}

)


SELECT 
  sale_id,
  order_id,
  line_number,
  order_ts,
  line_number,
  order_date,
  customer_id,
  product_id,
  product_currency,
  qty,
  unit_price,
  line_discount_pct,
  tax_pct,
  rate_to_aud,
ROUND(CAST(qty * unit_price AS DECIMAL(38, 2)), 2) AS gross_amount,
ROUND(CAST(qty * unit_price * rate_to_aud AS DECIMAL(38, 2)), 2) AS gross_amount_aud,
ROUND(CAST(qty * unit_price * (1 - line_discount_pct / 100) * (1 + tax_pct / 100) AS DECIMAL(38, 2)), 2) AS total_amount,
ROUND(CAST(qty * unit_price * rate_to_aud * (1 - line_discount_pct / 100) * (1 + tax_pct / 100) AS DECIMAL(38, 2)), 2) AS total_amount_aud,
  store_id,
  channel,
  payment_method,
  coupon_code,
  shipping_fee_aud,
  order_currency,
  ingestion_ts

FROM sales_enriched


