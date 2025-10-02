{% set src_table = 'countries' %}

{{ config(materialized='table', contract={'enforced': false}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
  select
    *

  from bronze_parquet
)

-- Step 3: Final output with deduplication
select *
 from typed

