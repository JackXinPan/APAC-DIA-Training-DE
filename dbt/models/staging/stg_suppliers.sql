{% set src_table = 'suppliers' %}

{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),


-- Step 2: Apply transformations
typed as (
select

    CAST(supplier_id AS BIGINT) AS supplier_id,
    CAST(TRIM(supplier_code) AS STRING) AS supplier_code,
    CAST(TRIM(name) AS STRING) AS name,
    CAST(TRIM(country_code) AS STRING) AS country_code,
    CAST(lead_time_days AS INT) AS lead_time_days,
    CAST(preffered AS BOOLEAN) AS preferred,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts,

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
 
