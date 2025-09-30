{% test discontinued_without_date(model) %}
    select *
    from {{ model }}
    where is_discontinued = true
      and discontinued_dt is null
{% endtest %}
