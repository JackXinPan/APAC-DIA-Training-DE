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

CAST(json_extract(timing[1], '$.started_at') AS TIMESTAMP) AS compile_started_at,
CAST(json_extract(timing[1], '$.completed_at') AS TIMESTAMP) AS compile_completed_at,
CAST(json_extract(timing[2], '$.started_at') AS TIMESTAMP) AS execute_started_at,
CAST(json_extract(timing[2], '$.completed_at') AS TIMESTAMP) AS execute_completed_at,

  thread_id,
  execution_time,
  message,
  failures,
  unique_id,
  compiled,
  compiled_code,
  relation_name,
  split_part(relation_name, '.', 1) as database,
  split_part(relation_name, '.', 2) as schema,
  split_part(relation_name, '.', 3) as table_name,
  batch_results,
  adapter_response_message,
  ingestion_ts,
 audit_id
 
    -- Pipeline Health Metrics
 --  try_cast(json_extract(batch_results, '$.rows_processed') as int) as rows_processed,
  --  execution_time as processing_time_seconds,
 --   try_cast(json_extract(adapter_response_message, '$.file_size_bytes') as int) as file_size_bytes
--


FROM {{ ref('silver_audit_seed') }}

{% if is_incremental() %}
WHERE ingestion_ts > (
  SELECT MAX(ingestion_ts) FROM {{ this }}
)
{% endif %}
