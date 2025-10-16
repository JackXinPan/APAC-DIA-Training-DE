{{
  config(
    materialized='incremental',
    unique_key='audit_id',
    on_schema_change='merge'
  ) 
}}


WITH audit_data AS (
  SELECT 
    status,
    timing,
    try_cast(json_extract(timing[1], '$.started_at') AS TIMESTAMP) AS compile_started_at,
    try_cast(json_extract(timing[1], '$.completed_at') AS TIMESTAMP) AS compile_completed_at,
    try_cast(json_extract(timing[2], '$.started_at') AS TIMESTAMP) AS execute_started_at,
    try_cast(json_extract(timing[2], '$.completed_at') AS TIMESTAMP) AS execute_completed_at,
    thread_id,
    execution_time,
    message,
    failures,
    unique_id,
    compiled,
    compiled_code,
    relation_name,
    split_part(relation_name, '.', 1) AS database,
    split_part(relation_name, '.', 2) AS schema,
    split_part(relation_name, '.', 3) AS table_name,
    batch_results,
    adapter_response_message,
    ingestion_ts,
    audit_id

    -- Optional metrics (uncomment if needed)
    -- try_cast(json_extract(batch_results, '$.rows_processed') AS INT) AS rows_processed,
    -- execution_time AS processing_time_seconds,
    -- try_cast(json_extract(adapter_response_message, '$.file_size_bytes') AS INT) AS file_size_bytes
  FROM {{ ref('silver_audit_seed') }}
)

SELECT 
   status,
    timing,
    compile_started_at,
    compile_completed_at,
   execute_started_at,
    execute_completed_at,
  CAST(compile_started_at AS DATE) AS compile_started_date,
  CAST(compile_completed_at AS DATE) AS compile_completed_date,
  CAST(execute_started_at AS DATE) AS execute_started_date,
  CAST(execute_completed_at AS DATE) AS execute_completed_date,
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
FROM audit_data

{% if is_incremental() %}
WHERE ingestion_ts > (
  SELECT MAX(ingestion_ts) FROM {{ this }}
)
{% endif %}
