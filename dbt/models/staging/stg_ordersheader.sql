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
    cast(currency as varchar) as currency
  from bronze_parquet
)

-- Step 3: Final output
select * from typed

