{% set src_table = 'events' %}

{{ config(materialized='table', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (

  select
    cast(envelope__event_id as bigint) as event_id,
    cast(envelope__event_ts as timestamp) as env_event_ts,
    cast(envelope__event_type as string) as event_type,
    cast(envelope__user_id as bigint) as user_id,
    cast(envelope__session_id as string) as session_id,
    cast(envelope__event_date as date) as event_date,
    cast(payload__event_ts as timestamp) as payload_event_ts,
    cast(payload__device as string) as device,
    cast(payload__ip_address as string) as ip_address,
    cast(payload__geo_location__lat as double) as latitude,
    cast(payload__geo_location__lon as double) as longitude,
    cast(payload__product_id as bigint) as product_id,
    cast(payload__price as double) as price,
    cast(payload__action as string) as action,
--    cast(payload__discount_coupon as boolean) as discount_coupon,
    cast(payload__session_duration as int) as session_duration,
    cast(payload__logout_reason as string) as logout_reason,
    cast(ingestion_ts as timestamp) as ingestion_ts

  from bronze_parquet
)

-- Step 3: Final output
select * from typed
where latitude between -90 and 90
and longitude between -180 and 180
