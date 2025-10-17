
{{
  config(
    materialized='view'
  )
}}

with bronze_parquet as (
  select * from read_parquet('seeds/run_results_table.parquet')
),

typed as (
  select
   *
  from bronze_parquet
)

select
  *
from typed

