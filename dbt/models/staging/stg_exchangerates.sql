
{% set src_table = 'exchangerates' %}
{{ config(materialized='table', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
  select
    cast(date as date) as date,
    cast(currency as string) as currency,
    cast(rate_to_aud as decimal(18, 8)) as rate_to_aud,
    cast(ingestion_ts as timestamp) as ingestion_ts
  from bronze_parquet
)

-- Step 3: Final output
select * from typed
