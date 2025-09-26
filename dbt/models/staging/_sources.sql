-- External views pointing at Bronze Parquet/Delta. Adjust path if needed.
{{ config(materialized='view') }}

{% set lake_root = '../lake/bronze/parquet/retail_bronze_dataset' %}

-- Step 1: Read from external Parquet file

  select * from read_parquet('{{ lake_root }}/customers/*.parquet')

--create or replace view bronze_customers_delta as
--select * from delta_scan('{{ lake_root }}/delta/customers');



--{{ config(materialized='view') }}

--{% set lake_root = '../lake/bronze/parquet/retail_bronze_dataset' %}

--select * from read_parquet('{{ lake_root }}/customers/*.parquet')
