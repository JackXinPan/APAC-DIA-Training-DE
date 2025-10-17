{% set src_table = 'events' %}

{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (


SELECT
    CAST(envelope__event_id AS BIGINT) AS event_id,
    CAST(envelope__event_ts AS TIMESTAMP) AS env_event_ts,
    CAST(TRIM(envelope__event_type) AS STRING) AS event_type,
    CAST(envelope__user_id AS BIGINT) AS user_id,
    CAST(TRIM(envelope__session_id) AS STRING) AS session_id,
    CAST(envelope__event_date AS DATE) AS event_date,
    CAST(payload__event_ts AS TIMESTAMP) AS payload_event_ts,
    CAST(TRIM(payload__device) AS STRING) AS device,
    CAST(TRIM(payload__ip_address) AS STRING) AS ip_address,
    CAST(payload__geo_location__lat AS DOUBLE) AS latitude,
    CAST(payload__geo_location__lon AS DOUBLE) AS longitude,
    CAST(payload__product_id AS BIGINT) AS product_id,
    CAST(payload__price AS DOUBLE) AS price,
    CAST(TRIM(payload__action) AS STRING) AS action,
--    CAST(payload__discount_coupon AS BOOLEAN) AS discount_coupon,
    CAST(payload__session_duration AS INT) AS session_duration,
    CAST(TRIM(payload__logout_reason) AS STRING) AS logout_reason,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts


  from bronze_parquet
)

-- Step 3: Final output
select * from typed
--where latitude between -90 and 90
--and longitude between -180 and 180
