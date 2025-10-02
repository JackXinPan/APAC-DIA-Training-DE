{{
  config(
    materialized='incremental',
    unique_key='shipment_id',
    on_schema_change='merge'
  ) 
}}

SELECT 
        shipment_id,
        order_id,
        carrier,
        shipped_at,
        delivered_at,
        ship_cost,
        ingestion_ts

FROM {{ ref('stg_shipments') }}

{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}