-- macros/normalize_column_names.sql
{% macro snakecase_column_names(columns) %}
  {% set normalized = [] %}
  {% for col in columns %}
    {% set snake = col | lower | replace(" ", "_") | replace("-", "_") %}
    {% do normalized.append(snake) %}
  {% endfor %}
  {{ return(normalized) }}
{% endmacro %}
