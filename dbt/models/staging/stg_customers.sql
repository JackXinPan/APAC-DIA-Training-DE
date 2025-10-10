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
    cast(postcode as BIGINT) as postcode,
    cast(country_code as string) as country_code,
    cast(latitude as double) as latitude,
    cast(longitude as double) as longitude,
    cast(birth_date as date) as birth_date,   
-- Derive age
--    datediff('year', cast(birth_date as date), current_date) as age,
    cast(join_ts as timestamp) as join_ts,
    cast(is_vip as boolean) as is_vip,
    cast(ingestion_ts as timestamp) as ingestion_ts,
    cast(gdpr_consent as boolean) as gdpr_consent,
      row_number() over (
        partition by natural_key
        order by join_ts desc  -- Keep latest join_ts per natural_key
      ) as row_num

  from bronze_parquet
)

-- Step 3: Final output with deduplication
select customer_id,
       natural_key,
       first_name,
       last_name,
       email,
       phone,
       address_line1, 
       address_line2, 
       city, 
       state_region,
       postcode,
       country_code,
       latitude,
       longitude,
       birth_date,   
--       age,
       join_ts,
       is_vip,
       gdpr_consent,
       ingestion_ts
 from typed
where row_num = 1
and email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'-- email format validation 
and latitude between -90 and 90
and longitude between -180 and 180
