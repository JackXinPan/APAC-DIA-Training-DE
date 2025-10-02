{% set src_table = 'suppliers' %}

{{ config(materialized='table', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),


-- Step 2: Apply transformations
typed as (
select
    cast(supplier_id as bigint) as supplier_id,
    cast(supplier_code as string) as supplier_code,
    cast(name as string) as name,
    cast(country_code as string) as country_code,
    cast(lead_time_days as int) as lead_time_days,
    cast(preffered as boolean) as preferred,
    cast(ingestion_ts as timestamp) as ingestion_ts,
      row_number() over (
        partition by supplier_code
        order by supplier_id asc  
      ) as row_num

from bronze_parquet
)

-- Step 3: Final output
select supplier_id,
        supplier_code,
        name,
        country_code,
        lead_time_days,
        preferred,
        ingestion_ts

 from typed where row_num = 1
 
