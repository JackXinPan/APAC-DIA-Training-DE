{{
  config(
    materialized='incremental',
    unique_key=['hour_ts', 'store_id', 'shelf_id'],
    on_schema_change='merge'
  ) 
}}

WITH base AS (
    SELECT 
        sensor_ts,
        store_id,
        shelf_id,
        temperature_c,
        humidity_pct,
        battery_mv
    FROM {{ ref('silver_sensors') }}
),

hourly_aggregates AS (
    SELECT
        store_id,
        shelf_id,
        --pre aggregations
        DATE_TRUNC('hour', sensor_ts) AS hour_ts,
        AVG(temperature_c) AS avg_temperature_c,
        AVG(humidity_pct) AS avg_humidity_pct,
        AVG(battery_mv) AS avg_battery_mv,

        -- Anomaly flags based on hourly averages
        CASE 
            WHEN AVG(temperature_c) < 0 OR AVG(temperature_c) > 50 THEN TRUE 
            ELSE FALSE 
        END AS is_anom_temp,

        CASE 
            WHEN AVG(humidity_pct) < 0 OR AVG(humidity_pct) > 100 THEN TRUE 
            ELSE FALSE 
        END AS is_anom_humidity,

        CASE 
            WHEN AVG(battery_mv) < 1000 THEN TRUE 
            ELSE FALSE 
        END AS is_anom_bat_mv
    FROM base
    GROUP BY store_id, shelf_id, DATE_TRUNC('hour', sensor_ts)
),

final AS (
    SELECT
        *,
        -- Rolling 3-hour average temperature
        AVG(avg_temperature_c) OVER (
            PARTITION BY store_id, shelf_id 
            ORDER BY hour_ts 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_avg_temp_3h,

        -- Rolling 3-hour average humidity
        AVG(avg_humidity_pct) OVER (
            PARTITION BY store_id, shelf_id 
            ORDER BY hour_ts 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_avg_humidity_3h,

        -- Rolling 3-hour average battery voltage
        AVG(avg_battery_mv) OVER (
            PARTITION BY store_id, shelf_id 
            ORDER BY hour_ts 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_avg_battery_mv_3h
    FROM hourly_aggregates
    {% if is_incremental() %}
      WHERE hour_ts > (
        SELECT MAX(hour_ts) FROM {{ this }}
      )
    {% endif %}
)

SELECT * FROM final
