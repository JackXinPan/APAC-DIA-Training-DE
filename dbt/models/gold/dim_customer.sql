{{
  config(
    materialized='table',
    schema ='gold'
  ) 
}}

WITH silver AS (
    -- Reference your Silver layer model
    SELECT     
        customer_id,
       natural_key,
       first_name,
       last_name,
       email,
       phone,
       address_line1, 
       address_line2, 
       city, 
       state_region,
       postcode,
       country_code,
       latitude,
       longitude,
       birth_date,   
--        age,
       join_ts,
       is_vip,
       gdpr_consent,
       ingestion_ts FROM {{ ref('silver_customers') }}
),
enhanced AS (
    SELECT
        customer_id,
       natural_key,
       first_name,
       last_name,
    -- Apply GDPR masking
        CASE 
            WHEN gdpr_consent = false THEN md5(email)
            ELSE email
        END AS email,       

        CASE 
            WHEN gdpr_consent = false THEN 'XXX-XXX-XXXX'
            ELSE phone
        END AS phone_number,
        
        CASE 
                WHEN gdpr_consent = false THEN null
                ELSE address_line1
        END AS address_line1,
        CASE 
                WHEN gdpr_consent = false THEN null
                ELSE address_line2
        END AS address_line2,
       city, 
       state_region,
       postcode,
       country_code,
       latitude,
       longitude,
       birth_date,  
        EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) AS customer_age,
        CURRENT_DATE - CAST(join_ts AS Date) AS customer_lifetime_days, 
       join_ts,
       is_vip,
       gdpr_consent,
       
        CASE 
            WHEN is_vip = true THEN 'VIP'
            WHEN CURRENT_DATE - CAST(join_ts AS Date) < 180 THEN 'New'
            ELSE 'Standard'
        END AS customer_segment

 --      ingestion_ts 
    FROM silver
)
SELECT 
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS customer_sk,
    * 
FROM enhanced