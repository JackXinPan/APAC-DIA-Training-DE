{{
  config(
    materialized='incremental',
    unique_key='audit_id',
    on_schema_change='merge'
  ) 
}}

with bronze_parquet as (
  select * from {{ ref('run_results_table') }}
),

typed as (
  select
    status,
    timing,
    thread_id,
    execution_time,
    message,
    failures,
    unique_id,
    compiled,
    compiled_code,
    relation_name,
    batch_results,
    'adapter_response._message' as adapter_response_message,
    ingestion_ts
  from bronze_parquet
)

select
  status,
  timing,
  thread_id,
  execution_time,
  message,
  failures,
  unique_id,
  compiled,
  compiled_code,
  relation_name,
  batch_results,
  adapter_response_message,
  ingestion_ts,
    -- Surrogate key using dbt_utils
    {{ dbt_utils.generate_surrogate_key(['unique_id', 'ingestion_ts']) }} as audit_id
  from typed


{% if is_incremental() %}
  WHERE ingestion_ts > (
    SELECT MAX(ingestion_ts) FROM {{ this }}
  )
{% endif %}
