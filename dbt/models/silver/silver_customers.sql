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


FROM {{ ref('stg_customers') }}

{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(line_ingestion_ts) FROM {{ this }}
  )
{% endif %}