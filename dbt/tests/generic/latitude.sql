{% test latitude(model, column_name) %}
    SELECT *
    FROM {{ model }}
    WHERE {{ column_name }} IS NOT NULL
      AND ({{ column_name }} < -90 OR {{ column_name }} > 90)
{% endtest %}