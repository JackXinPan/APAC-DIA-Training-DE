{{
  config(
    materialized='incremental',
    unique_key='event_id',
    on_schema_change='merge'
  ) 
}}

SELECT 
    event_id,
    env_event_ts,
    event_type,
    user_id,
    session_id,
    event_date,
    payload_event_ts,
    device,
    ip_address,
    latitude,
    longitude,
    product_id,
    price,
    action,
    discount_coupon,
    session_duration,
    logout_reason,
    ingestion_ts
FROM {{ ref('stg_events') }} 
{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}