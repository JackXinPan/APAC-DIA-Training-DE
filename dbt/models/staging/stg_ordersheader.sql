{% set src_table = 'ordersheader' %}

{{ config(materialized='table', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (

  select
    cast(order_id as bigint) as order_id,
    cast(order_ts as timestamp) as order_ts,
    cast(order_dt_local as date) as order_dt_local,
    cast(customer_id as bigint) as customer_id,
    cast(store_id as bigint) as store_id,
    cast(channel as varchar) as channel,
    cast(payment_method as varchar) as payment_method,
    cast(coupon_code as varchar) as coupon_code,
    cast(shipping_fee as decimal(12, 2)) as shipping_fee,
    cast(currency as varchar) as currency,
    cast(ingestion_ts as timestamp) as ingestion_ts,
 --deduplicate based on order_id, keeping the latest order_ts
        row_number() over (
            partition by order_id
            order by order_ts desc  -- or any other logic to keep the "latest" or "first"
        ) as row_num

  from bronze_parquet
)

-- Step 3: Final output deduplication


SELECT order_id,
       order_ts,
       order_dt_local,
       customer_id,
       store_id,
       channel,
       payment_method,
       coupon_code,
       shipping_fee,
       currency,
       ingestion_ts
FROM typed t
WHERE EXISTS (
    SELECT 1
    FROM {{ ref('stg_customers') }} c
    WHERE t.customer_id = c.customer_id
)
and exists (
    select 1
    from {{ ref('stg_stores') }} s
    where t.store_id = s.store_id
)
and row_num = 1


