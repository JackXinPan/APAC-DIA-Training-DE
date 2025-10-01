{% test compositekey(model, column_names) %}
    select {{ column_names | join(', ') }}, count(*) as record_count
    from {{ model }}
    group by {{ column_names | join(', ') }}
    having count(*) > 1
{% endtest %}

