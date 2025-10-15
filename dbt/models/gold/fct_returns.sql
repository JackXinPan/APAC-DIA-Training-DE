
{{ config(
    materialized='incremental',
    unique_key='return_id',
    on_schema_change='merge'
) }}

WITH latest_ingestion AS (
  SELECT MAX(ingestion_ts) AS max_ingestion_ts
  FROM {{ this }}
),

returns_filtered AS (
  SELECT 
    r.return_id,
    r.order_id,
    r.product_id,
    r.return_ts,
    r.qty AS return_qty,
    r.reason AS return_reason,
    r.return_reason_code,
    r.source_version,
     CAST(r.return_ts AS DATE) AS return_date,
    r.ingestion_ts
  FROM {{ ref('silver_returns') }} r
  JOIN {{ ref('dim_product_scd') }} p 
       ON r.product_id = p.product_id 
  JOIN {{ ref('silver_orders') }} o 
       ON r.order_id = o.order_id
  {% if is_incremental() %}
  JOIN latest_ingestion li ON r.ingestion_ts > li.max_ingestion_ts
  {% endif %}
)

SELECT * FROM returns_filtered
