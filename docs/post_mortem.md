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
    To simulate realistic sales data, Python scripts were used to generate millions of rows conforming to a specified schema. However, achieving 100% data realism proved to be performance-intensive on the company-provided local machine.
    As a result, shortcuts were intentionally taken to prioritize performance and focus on the core assessment of intermediate data engineering principles. Examples of these shortcuts include:

    Geographic Integrity: Region, postcode, latitude, and longitude values were randomized independently, without enforcing geographic consistency.
    Currency & Regional Buying Behavior: Currency usage and product preferences were not proportionally aligned with realistic regional distributions.
    Order Timestamp Distribution: Timestamps were randomly generated without modeling realistic purchase patterns (e.g., peak hours, seasonal trends).
    Column Independence: Each column was randomized independently, avoiding complex interdependencies that would increase generation time.

    This approach allowed me to focus on pipeline design, transformation logic, and DLT/DBT integration, rather than over-investing in data realism that would not materially impact the assessment objectives.
## Challenges Encountered
- Technical difficulties and how you solved them
    - A few major issues early on with environmental config with the Insight Laptop. Solved by
        - Acquire a method from IT to be able to install libraries with by executing powershell scripts in Powershell as an administrator.
        - Rollback updates to Python to be compatible to requireed libraries
    - Performance issues with generating and ingesting synthetic data.
        - Refactor to more performant code making to handle definitions outside of loops, creating helper functions, having a single write to data_raw command for each data source and NOT write each time a line of data is created as sampled from the sample code given.
        - Explore using libraries and tools beyond recommended in the dependencies and requirements sections
        - Calculated concessions with data realism for the interest of time to be spent on core of the assessment
    - Visual requirements and assumptions made downstream that aren't possible within the local environment or specified/ goes against schema specified in the earlier sections

## Data Quality Findings  
- Anomalies you injected and detection rates
    Anomalies were injected in during the synthetic data generation phase using random probability rolls during loops to know when use anomalous data generation logic at the specified probability rate
- Unexpected data patterns discovered
    - Found at the schema enforcement stage in DLT and DBT. As well constraint tests in DBT. Custom logic used to raise flags if there is bad data generation created beyond intended anomaly rates as a % of bad rows over total rows.
- Test failures and resolutions
    - Further constraint tests done during the destination and curation stage. Anomaly flags in place for down stream reporting or removed rows based on referential integrity/ unique keys/ nulls/ expected values that match contrainst test logics.

## Performance Results
- Pipeline execution times by layer
 - Diagnostics results/ data presented in CLI as well run results for DBT that staged via DBT Seed
     Providing insights on model test successes/ failed, rows processed and execution times and key violations
- Query performance benchmarks

## Production Recommendations
- What you would do differently in production
    CI/CD 
    Date filters based on business requirements to contain data model size
    Self Serve analytics/ shared semantic modelling
    Monitoring and Alert Systems if built to scale
    - Set up real-time monitoring for:

        Pipeline failures
        Data freshness and latency
        Schema drift (e.g., unexpected column changes)
        Volume anomalies (e.g., sudden drop/spike in row counts)
    Import execution logs and report user telemetry
    Generate metadata tables/parametrize ingestion to scale against more/different data sources
    Move away from a environment agnostic perspective (good for pure fundamentals of python coding as a high code design) not for scale

## Time Investment
- Hours spent per exercise
 - ordered in terms of effort
    1. HIGH - Data Generation (has many downstream consequences therefore requiring most attention, tweaks to data realism or tweaks to fit down stream requirements, non performant sample coding)
    2. HIGH - Power BI Visualisation ( Creating and managing many metrics, many metrics visuals not possible given constraints given in assessment, agonising over possible requirements)
    3. MEDIUM - DBT Silver/ Gold (creating raw_, stg_, silver_, fct_/dim_, proper use of full and incremental loading. Proper use of schema enforcement and schema evolution, proper use of metadata column and composite keys, uses of macros, tests, seeds and project configs to streamline dbt run process. Sample coding may not work in local environment or non performant)
    4. MEDIUM - DLT Bronze (Ingestion of data from many sources from raw folder location into DUCKDB, takes longest to run as python ingestion script, sample coding may not work in local environment or install version/python environment)

- What you learned
    Gained strong familiarity with DLT and dbt. These tools are highly effective for diagnostics, unit testing, and enforcing data quality etc. They streamline many traditional Python practices, such as load types and staging tablesas examples.
    Learned to work backwards rather than iteratively—adopting a business analyst/data analyst perspective helps avoid downstream issues and allows early identification of blockers. Acting as an architect/engineer without clear direction can be detrimental.
    Recognized the importance of communication. Sharing knowledge helps address common missteps, especially among both beginner and seasoned data engineers. Struggles during this assessment are not always a reflection of personal competency.

## Tools Assessment
- Experience with new tools (DLT, dbt, Delta Lake)
    DLT:
        Takes time to run and differs from the Databricks version in terms of arguments. There is some overlap and redundancy with dbt. DLT is tightly integrated with Databricks but not yet native to Microsoft Fabric (though Fabric has equivalents like declarative pipelines).


    dbt:
        A best-practice standard that is highly scalable. Many features were explored and utilized.


    Delta Lake:
        Writing and reading Delta (built on Parquet) locally was a valuable experience. Delta is a common component in modern Fabric platforms and a strong alternative to Parquet in Fabric infrastructure.
