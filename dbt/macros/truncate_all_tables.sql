
{% macro truncate_all_tables() %}
{% for model in graph.nodes.values() if model.resource_type == 'model' %}
    {% set relation = adapter.get_relation(
        database=model.database,
        schema=model.schema,
        identifier=model.name
    ) %}
    {% if relation %}
        {{ log("Truncating " ~ relation, info=True) }}
        {% do run_query("TRUNCATE TABLE " ~ relation) %}
    {% endif %}
{% endfor %}
{% endmacro %}

--dbt run-operation truncate_all_tables