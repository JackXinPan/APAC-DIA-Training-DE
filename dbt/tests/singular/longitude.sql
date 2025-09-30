{% test valid_longitude(model, column_name) %}
    SELECT *
    FROM {{ model }}
    WHERE {{ column_name }} IS NOT NULL
      AND ({{ column_name }} < -180 OR {{ column_name }} > 180)
{% endtest %}