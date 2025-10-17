{% set src_table = 'customers' %}

{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
  select

    CAST(customer_id AS BIGINT) AS customer_id,
    TRIM(natural_key) AS natural_key,
    TRIM(first_name) AS first_name,
    TRIM(last_name) AS last_name,
    TRIM(email) AS email,
    TRIM(phone) AS phone,
    TRIM(address_line1) AS address_line1,
    TRIM(address_line2) AS address_line2,
    TRIM(city) AS city,
    CAST(TRIM(state_region) AS STRING) AS state_region,
    CAST(postcode AS BIGINT) AS postcode,
    CAST(TRIM(country_code) AS STRING) AS country_code,
    CAST(latitude AS DOUBLE) AS latitude,
    CAST(longitude AS DOUBLE) AS longitude,
    CAST(birth_date AS DATE) AS birth_date,
-- Derive age
--    DATEDIFF('year', CAST(TRIM(birth_date) AS DATE), CURRENT_DATE) AS age,
    CAST(join_ts AS TIMESTAMP) AS join_ts,
    CAST(is_vip AS BOOLEAN) AS is_vip,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts,
    CAST(gdpr_consent AS BOOLEAN) AS gdpr_consent,

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
--and email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'-- email format validation 
--and latitude between -90 and 90
--and longitude between -180 and 180
