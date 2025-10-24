{{
  config(
    materialized='table'
  ) 
}}

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
        datediff('year', birth_date, ingestion_ts) as age,
       join_ts,
       is_vip,
       gdpr_consent,
       ingestion_ts

--and email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'-- email format validation 
--and latitude between -90 and 90
--and longitude between -180 and 180
FROM {{ ref('stg_customers') }}


WHERE 
    email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' -- email format validation
    AND latitude BETWEEN -90 AND 90
    AND longitude BETWEEN -180 AND 180

    {% if is_incremental() %}
    AND ingestion_ts > (
        SELECT MAX(ingestion_ts) FROM {{ this }}
    )
    {% endif %}
