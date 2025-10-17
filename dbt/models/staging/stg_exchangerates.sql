
{% set src_table = 'exchangerates' %}
{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),

-- Step 2: Apply transformations
typed as (
  select

    CAST(date AS DATE) AS date,
    CAST(TRIM(currency) AS STRING) AS currency,
    CAST(rate_to_aud AS DECIMAL(18, 8)) AS rate_to_aud,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts

  from bronze_parquet
)

-- Step 3: Final output
select * from typed
