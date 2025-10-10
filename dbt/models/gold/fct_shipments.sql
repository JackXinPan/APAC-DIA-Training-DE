{{
  config(
    materialized='incremental',
    unique_key='shipment_id',
    on_schema_change='merge'
  ) 
}}

SELECT 
        s.shipment_id,
        s.order_id,
        s.carrier,
        o.shipping_fee,
        s.shipped_at,
        s.delivered_at,
        s.ship_cost as shipping_cost,
        s.ingestion_ts,
        
  -- Calculate delivery days only if delivered
  CASE 
   
  WHEN s.delivered_at IS NOT NULL THEN datediff('day', s.shipped_at, s.delivered_at)
  ELSE NULL

  END AS delivery_days,

 -- Flag late deliveries based on SLA (e.g., 5 days)
  CASE 
    WHEN s.delivered_at IS NOT NULL AND s.delivered_at <= s.shipped_at + INTERVAL '5 days' THEN TRUE
    ELSE FALSE
  END AS on_time_flag

FROM {{ ref('silver_shipments') }} s
JOIN {{ ref('silver_orders') }} o
on s.order_id = o.order_id
{% if is_incremental() %}
  WHERE s.ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}