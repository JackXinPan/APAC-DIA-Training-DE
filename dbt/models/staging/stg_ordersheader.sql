{% set src_table = 'ordersheader' %}

{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (


SELECT
    CAST(order_id AS BIGINT) AS order_id,
    CAST(order_ts AS TIMESTAMP) AS order_ts,
    CAST(order_dt_local AS DATE) AS order_dt_local,
    CAST(customer_id AS BIGINT) AS customer_id,
    CAST(store_id AS BIGINT) AS store_id,
    CAST(TRIM(channel) AS VARCHAR) AS channel,
    CAST(TRIM(payment_method) AS VARCHAR) AS payment_method,
    CAST(TRIM(coupon_code) AS VARCHAR) AS coupon_code,
    CAST(shipping_fee AS DECIMAL(12, 2)) AS shipping_fee,
    CAST(TRIM(currency) AS VARCHAR) AS currency,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts,

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
WHERE row_num = 1
 and EXISTS (
     SELECT 1
     FROM {{ ref('stg_customers') }} c --checks that the customer id is valid
     WHERE t.customer_id = c.customer_id
 )
 and exists (
     select 1
     from {{ ref('stg_stores') }} s -- checks that the store_id is valid
     where t.store_id = s.store_id
 )



