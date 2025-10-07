
{{
  config(
    materialized='table'
  )
}}

with bronze_parquet as (
  select * from read_parquet('seeds/run_results_table.parquet')
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
    "adapter_response._message" as adapter_response_message,
    CURRENT_DATE as ingestion_ts
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
  ingestion_ts
from typed

