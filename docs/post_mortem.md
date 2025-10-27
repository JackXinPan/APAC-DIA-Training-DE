# Data Engineering Assessment - Post Mortem

## Architecture Decisions
- Why you chose Option A/B for Bronze ingestion?
    -  I chose to use DLT instead of traditional data ingestion tools because it is a helpful, modern Python library streamlines pipe data creation. It includes:
        - Schema enforcement/evolution . It's helpful with both enforcing schema structure as well as schema evolution. By setting schema_contract settings.
        - Schema, data type inference and normalisation. Standardising data data transformations during ingestion from many data sources loaded using python.
        - Declarative Pipeline Configuration - You specify what the pipeline should do (e.g., load, transform, enforce schema), and DLT handles how it gets done
        - Declare load types (full, incremental). DLT is stateful and will remember previous loads and ingestion times to make sure no duplicates are ingested to raw or staging and improves performance and cost-efficiency.
        - Logs, retries and error handling - simiplying triaging with in built commands making it easier to debug and maintain pipelines.
- Key design patterns used:
    - Python Scripts to generate realistic synthetic sales data to the specified schema, and source file type requirements stored in the 'data_raw' folder location
    - Used DLT Python pipeline ingestion for reasons stated above. Writing to both duckdb in the raw database, as as parquet in the 'lake' folders locations
    - DBT for staging from raw to destination silver layer and curated gold layer.
        -    Raw → Silver: Clean, standardize, and structure raw data into staging models (stg_, silver_) 
        -   Silver → Gold: Apply business logic, joins, and aggregations to create curated datasets (fct_, dim_)
        -    Modularity: Each transformation is a separate, testable model
        -    Reusability: Shared logic can be abstracted into macros or common models
        -    Lineage & Documentation: dbt auto-generates lineage graphs and docs
        -    Testing: Built-in tests ensure data quality (e.g., uniqueness, not null)
- Trade-offs made for performance vs complexity

## Challenges Encountered
- Technical difficulties and how you solved them
- Data quality issues discovered and handled
- Performance bottlenecks and optimizations

## Data Quality Findings  
- Anomalies you injected and detection rates
- Unexpected data patterns discovered
- Test failures and resolutions

## Performance Results
- Pipeline execution times by layer
- Data volumes processed
- Query performance benchmarks

## Production Recommendations
- What you would do differently in production
- Monitoring and alerting strategies
- Scaling considerations

## Time Investment
- Hours spent per exercise
- Most time-consuming aspects
- What you learned

## Tools Assessment
- Experience with new tools (DLT, dbt, Delta Lake)
- What worked well vs challenges
- Alternative approaches considered