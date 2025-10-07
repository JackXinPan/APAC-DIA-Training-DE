{{
  config(
    materialized='table',
    schema ='gold'
  ) 
}}

WITH silver AS (
    -- Reference your Silver layer model
    SELECT     
        supplier_id,
        supplier_code,
        name,
        s.country_code,
        c.country,
        c.region,
        lead_time_days,
        preferred
         FROM {{ ref('stg_suppliers') }} 
),
enhanced AS (
    SELECT
       supplier_id,
        supplier_code,
        name,
        country_code,
        country,
        region
        lead_time_days,
        preferred,
CASE
    WHEN lead_time_days <= 7 THEN 'Tier 1'
    WHEN lead_time_days <= 14 THEN 'Tier 2'
    ELSE 'Tier 3'
END AS supplier_tier



    FROM silver
)
SELECT 
    {{ dbt_utils.generate_surrogate_key(['supplier_id']) }} AS supplier_sk,
    * 
FROM enhanced