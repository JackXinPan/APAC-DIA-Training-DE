{{
  config(
    materialized='table',
    schema ='gold'
  ) 
}}

WITH silver AS (
    -- Reference your Silver layer model
    SELECT     
    product_scd_id,
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
    effective_from,
    effective_to,
    is_current
         FROM {{ ref('silver_products') }} s

),
enhanced AS (
    SELECT
    product_scd_id,
    product_id,
    sku,
    name,
    category,
    subcategory,
    current_price,
    currency,
    is_discontinued,
    introduced_dt as introduced_date,
    discontinued_dt as discontinued_date,
    effective_from as effective_from_date,
    effective_to as effective_to_date, 
    is_current,
    CASE 
      WHEN current_price != LAG(current_price) OVER (PARTITION BY product_id ORDER BY effective_from)
      THEN TRUE ELSE FALSE
    END AS is_price_change

    FROM silver
)
SELECT 
    * 
FROM enhanced