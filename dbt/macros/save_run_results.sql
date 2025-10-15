
{% macro save_run_results() %}
    {{ log("Running save_run_results script...", info=True) }}
    {% do run_operation('run_results') %}
{% endmacro %}
