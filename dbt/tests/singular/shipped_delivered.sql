-- tests/test_delivered_before_shipped.sql

SELECT *
FROM {{ ref('stg_shipments') }}
WHERE delivered_at < shipped_at

