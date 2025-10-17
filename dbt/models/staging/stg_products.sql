{% set src_table = 'products' %}

{{ config(materialized='view', contract={'enforced': true}) }}
{% set lake_root = var('lake_root') %}

-- Step 1: Read from external Parquet file
with bronze_parquet as (
  select * from read_parquet('{{ lake_root }}/{{ src_table }}/*.parquet')
),


-- Step 2: Apply transformations
typed as (

SELECT

    CAST(product_id AS BIGINT) AS product_id,
    CAST(TRIM(sku) AS STRING) AS sku,
    CAST(TRIM(name) AS STRING) AS name,
    CAST(TRIM(category) AS STRING) AS category,
    CAST(TRIM(subcategory) AS STRING) AS subcategory,
    CAST(current_price AS NUMERIC(12, 4)) AS current_price,
    CAST(TRIM(currency) AS STRING) AS currency,
    CAST(is_discontinued AS BOOLEAN) AS is_discontinued,
    CAST(introduced_dt AS DATE) AS introduced_dt,
    CAST(discontinued_dt AS DATE) AS discontinued_dt,
    CAST(ingestion_ts AS TIMESTAMP) AS ingestion_ts


    -- Generate a surrogate key for SCD 2    
    {{ dbt_utils.generate_surrogate_key([
      'product_id',
      'name',
      'category',
      'subcategory',
      'current_price',
      'currency',
      'is_discontinued',
      'discontinued_dt'
    ]) }} AS product_scd_id

from bronze_parquet
)

-- Step 3: Final output
select * from typed

