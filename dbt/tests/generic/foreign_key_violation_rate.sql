
{% test foreign_key_violation_rate(model, column_name, parent_model, parent_key) %}
    with violations as (
        select {{ column_name }}
        from {{ model }}
        where {{ column_name }} is not null
          and {{ column_name }} not in (select {{ parent_key }} from {{ parent_model }})
    ),
    total as (
        select count(*) as total_rows from {{ model }} where {{ column_name }} is not null
    ),
    violation_rate as (
        select
            (select count(*) from violations) * 100.0 / nullif(total.total_rows, 0) as rate
        from total
    )
    select *
    from violation_rate
    where rate >= 1.5
{% endtest %}
