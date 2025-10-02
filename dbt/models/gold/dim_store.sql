{{
  config(
    materialized='table',
    schema ='gold'
  ) 
}}

WITH silver AS (
    -- Reference your Silver layer model
    SELECT     
        store_id,
        store_code,
        name,
        channel,
        region,
        state,
        latitude,
        longitude,
        open_date,
        close_date
         FROM {{ ref('silver_stores') }} s

),
enhanced AS (
    SELECT
        store_id,
        store_code,
        name,
        channel,
        region,
        state,
        latitude,
        longitude,
        open_date,
        close_date,
    CASE
        WHEN close_date IS NULL THEN CURRENT_DATE - open_date
        ELSE close_date - open_date
    END AS store_age_days,
    CASE
        WHEN close_date IS NULL AND channel = 'online'
            THEN 'large'
        WHEN close_date IS NULL AND channel = 'retail' 
            THEN 
                    CASE 
                        WHEN RANDOM() < 0.5 THEN 'medium'
                        ELSE 'small'
                    END
        ELSE NULL
        END AS store_size_category,
    CASE
        WHEN close_date IS NULL THEN false
        ELSE  true
    END AS operational_status
    FROM silver
)
SELECT 
    {{ dbt_utils.generate_surrogate_key(['store_id']) }} AS store_sk,
    * 
FROM enhanced