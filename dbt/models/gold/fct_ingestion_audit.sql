{{
  config(
    materialized='incremental',
    unique_key='audit_id',
    on_schema_change='merge'
  ) 
}}

SELECT 

  status,
  timing,
 compile_started_at,
  compile_completed_at,
   execute_started_at,
  execute_completed_at,
  thread_id,
  execution_time,
  message,
  failures,
  unique_id,
  compiled,
  compiled_code,
  relation_name,
   database,
   schema,
  table_name,
  batch_results,
  adapter_response_message,
  ingestion_ts,
 audit_id
 
    -- Pipeline Health Metrics
 --  try_cast(json_extract(batch_results, '$.rows_processed') as int) as rows_processed,
  --  execution_time as processing_time_seconds,
 --   try_cast(json_extract(adapter_response_message, '$.file_size_bytes') as int) as file_size_bytes
--


FROM {{ ref('silver_audit') }}

{% if is_incremental() %}
WHERE ingestion_ts > (
  SELECT MAX(ingestion_ts) FROM {{ this }}
)
{% endif %}
