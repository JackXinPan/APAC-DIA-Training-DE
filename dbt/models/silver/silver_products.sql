
{{ 
  config(
    materialized='incremental',
    unique_key='product_scd_id'
  ) 
}}


WITH source AS (
  SELECT 
    product_id,
    sku,
    REGEXP_REPLACE(name, '^.*\s', '') AS name, --product names have absurd pre-fixes I want to trim out
    category,
    subcategory,
    current_price,
    currency,
    is_discontinued,
    introduced_dt,
    discontinued_dt,
    ingestion_ts,
    product_scd_id,
    CURRENT_DATE AS effective_from,
    NULL AS effective_to,
    TRUE AS is_current
  FROM {{ ref('stg_products') }}
  {% if is_incremental() %}
    WHERE ingestion_ts > COALESCE(
      (SELECT MAX(ingestion_ts) FROM {{ this }}),
      '1900-01-01'::DATE
    )
  {% endif %}
)
,

new_records AS (
  SELECT *
  FROM source
  WHERE NOT EXISTS (
    SELECT 1
    FROM {{ this }}
    WHERE product_scd_id = source.product_scd_id
      AND is_current = TRUE
  )
),

expired_records AS (
  SELECT 
    product_id,
    sku,
    name,
    category,
    subcategory,
    current_price,
    currency,
    is_discontinued,
    introduced_dt,
    discontinued_dt,
    ingestion_ts,
    product_scd_id,
    effective_from,
    CURRENT_DATE AS effective_to,
    FALSE AS is_current
  FROM {{ this }}
  WHERE is_current = TRUE
    AND product_scd_id IN (
      SELECT product_scd_id FROM new_records
    )
)
---SCD retain expired records updating current and effective to status as and UNION new records with same surrogate key

SELECT * FROM new_records
UNION ALL
SELECT * FROM expired_records





