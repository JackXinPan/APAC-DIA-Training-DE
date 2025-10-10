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
        country_code,
        
    -- Random region assignment (can go back and have a more concise list of country codes and map it like that as a stretch goal)
        CASE 
            WHEN RANDOM() < 0.25 THEN 'America'
            WHEN RANDOM() < 0.5 THEN 'Europe'
            WHEN RANDOM() < 0.75 THEN 'Asia'
            ELSE 'Oceania'
        END AS region,

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
        region
        lead_time_days,
        preferred,
        lead_time_days,
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