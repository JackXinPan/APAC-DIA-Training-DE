
{{ config(
    materialized='table',
    schema='gold'
) }}






WITH date_spine AS (
    SELECT generate_series AS date_day
    FROM generate_series(
        DATE '2021-01-01',
        DATE '2025-12-31',
        INTERVAL '1 day'
    )
),


dim_date AS (
    SELECT
        d.date_day AS date,
        EXTRACT(YEAR FROM d.date_day) AS year,
        EXTRACT(MONTH FROM d.date_day) AS month,
        EXTRACT(DAY FROM d.date_day) AS day,
        EXTRACT(DAYOFWEEK FROM d.date_day) AS day_of_week,

CASE EXTRACT(DOW FROM d.date_day)
    WHEN 0 THEN 'Sunday'
    WHEN 1 THEN 'Monday'
    WHEN 2 THEN 'Tuesday'
    WHEN 3 THEN 'Wednesday'
    WHEN 4 THEN 'Thursday'
    WHEN 5 THEN 'Friday'
    WHEN 6 THEN 'Saturday'
END AS day_name,

CASE EXTRACT(MONTH FROM d.date_day)
    WHEN 1 THEN 'January'
    WHEN 2 THEN 'February'
    WHEN 3 THEN 'March'
    WHEN 4 THEN 'April'
    WHEN 5 THEN 'May'
    WHEN 6 THEN 'June'
    WHEN 7 THEN 'July'
    WHEN 8 THEN 'August'
    WHEN 9 THEN 'September'
    WHEN 10 THEN 'October'
    WHEN 11 THEN 'November'
    WHEN 12 THEN 'December'
    END AS month_name
,


        EXTRACT(QUARTER FROM d.date_day) AS quarter,
-- Weekend logic (PostgreSQL: 0 = Sunday, 6 = Saturday)
CASE WHEN EXTRACT(DOW FROM d.date_day) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,

-- Month start
DATE_TRUNC('month', d.date_day) AS month_start_date,

-- Month end

(DATE_TRUNC('month', d.date_day) + INTERVAL '1 month' - INTERVAL '1 day')::date AS month_end_date,


-- Quarter start
DATE_TRUNC('quarter', d.date_day) AS quarter_start_date,
-- Quarter end
(DATE_TRUNC('quarter', d.date_day) + INTERVAL '3 month' - INTERVAL '1 day')::date AS quarter_end_date,

-- Year start
DATE_TRUNC('year', d.date_day) AS year_start_date,
-- Year end
(DATE_TRUNC('year', d.date_day) + INTERVAL '1 year' - INTERVAL '1 day')::date AS year_end_date,
        EXTRACT(WEEK  FROM d.date_day) AS week_number,
        
-- Australian fiscal year (starts in July)
CASE 
    WHEN EXTRACT(MONTH FROM d.date_day) >= 7 
    THEN EXTRACT(YEAR FROM d.date_day) + 1 
    ELSE EXTRACT(YEAR FROM d.date_day) 
END AS fiscal_year_au,

-- Australian fiscal quarter (Q1 = Jul–Sep)
CASE 
    WHEN EXTRACT(MONTH FROM d.date_day) >= 7 
    THEN FLOOR(((EXTRACT(MONTH FROM d.date_day) - 7) / 3) + 1)
    ELSE FLOOR(((EXTRACT(MONTH FROM d.date_day) + 5) / 3) + 1)
END AS fiscal_quarter_au,


        -- Holiday logic with weekend adjustment

    CASE 
        WHEN d.date_day IN (
            DATE '2021-04-02', DATE '2021-04-05',
            DATE '2022-04-15', DATE '2022-04-18',
            DATE '2023-04-07', DATE '2023-04-10',
            DATE '2024-03-29', DATE '2024-04-01',
            DATE '2025-04-18', DATE '2025-04-21'
        )

    OR (
        (EXTRACT(MONTH FROM d.date_day), EXTRACT(DAY FROM d.date_day)) IN (
            (1, 1), (1, 26), (4, 25), (12, 25), (12, 26)
        )
        AND EXTRACT(DOW FROM d.date_day) NOT IN (0, 6)  -- Not weekend
    )
    OR (
        (EXTRACT(MONTH FROM d.date_day - INTERVAL '1 day'), EXTRACT(DAY FROM d.date_day - INTERVAL '1 day')) IN (
            (1, 1), (1, 26), (4, 25), (12, 25), (12, 26)
        )
        AND EXTRACT(DOW FROM d.date_day) = 1  -- Monday
        AND EXTRACT(DOW FROM d.date_day - INTERVAL '1 day') IN (0, 6)  -- Sunday or Saturday
    )
    THEN TRUE
    ELSE FALSE
END AS is_holiday_au,

CASE
    WHEN d.date_day IN (
        DATE '2021-04-02', DATE '2021-04-05',
        DATE '2022-04-15', DATE '2022-04-18',
        DATE '2023-04-07', DATE '2023-04-10',
        DATE '2024-03-29', DATE '2024-04-01',
        DATE '2025-04-18', DATE '2025-04-21'
    )
    OR (
        (EXTRACT(MONTH FROM d.date_day), EXTRACT(DAY FROM d.date_day)) IN (
            (1, 1),   -- New Year's Day
            (7, 4),   -- Independence Day
            (11, 11), -- Veterans Day
            (12, 25)  -- Christmas Day
        )
        AND EXTRACT(DOW FROM d.date_day) NOT IN (0, 6)  -- Not weekend
    )
    OR (
        (EXTRACT(MONTH FROM d.date_day - INTERVAL '1 day'), EXTRACT(DAY FROM d.date_day - INTERVAL '1 day')) IN (
            (1, 1), (7, 4), (11, 11), (12, 25)
        )
        AND EXTRACT(DOW FROM d.date_day) = 1  -- Monday
        AND EXTRACT(DOW FROM d.date_day - INTERVAL '1 day') IN (0, 6)  -- Sunday or Saturday
    )
    THEN TRUE
    ELSE FALSE
END AS is_holiday_us,

CASE 
    WHEN d.date_day IN (
        DATE '2021-04-02', DATE '2021-04-05',
        DATE '2022-04-15', DATE '2022-04-18',
        DATE '2023-04-07', DATE '2023-04-10',
        DATE '2024-03-29', DATE '2024-04-01',
        DATE '2025-04-18', DATE '2025-04-21'
    )
    OR (
        (EXTRACT(MONTH FROM d.date_day), EXTRACT(DAY FROM d.date_day)) IN (
            (1, 1),   -- New Year's Day
            (12, 25), -- Christmas Day
            (12, 26)  -- Boxing Day
        )
        AND EXTRACT(DOW FROM d.date_day) NOT IN (0, 6)  -- Not weekend
    )
    OR (
        (EXTRACT(MONTH FROM d.date_day - INTERVAL '1 day'), EXTRACT(DAY FROM d.date_day - INTERVAL '1 day')) IN (
            (1, 1), (12, 25), (12, 26)
        )
        AND EXTRACT(DOW FROM d.date_day) = 1  -- Monday
        AND EXTRACT(DOW FROM d.date_day - INTERVAL '1 day') IN (0, 6)  -- Sunday or Saturday
    )
    THEN TRUE
    ELSE FALSE
END AS is_holiday_uk

    FROM date_spine d
)


SELECT * FROM dim_date
