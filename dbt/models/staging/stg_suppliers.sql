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
    cast(preffered as boolean) as preferred
from bronze_parquet
)

-- Step 3: Final output
select * from typed
