{% set src_table = 'customers' %}

{{ config(materialized='table', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
  select
    cast(customer_id as bigint) as customer_id,
    natural_key,
    trim(first_name) as first_name,
    trim(last_name) as last_name,
    email,
    phone,
    address_line1, 
    address_line2, 
    city, 
    cast(state_region as string) as state_region,
    postcode,
    cast(country_code as string) as country_code,
    cast(latitude as double) as latitude,
    cast(longitude as double) as longitude,
    cast(birth_date as date) as birth_date,
    cast(join_ts as timestamp) as join_ts,
    cast(is_vip as boolean) as is_vip,
    cast(gdpr_consent as boolean) as gdpr_consent
  from bronze_parquet
)

-- Step 3: Final output
select * from typed

