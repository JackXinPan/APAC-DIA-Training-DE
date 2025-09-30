-- test to check for a positive flag on a discontinued product even thought there is no discontinued date

{% test discontinued_without_date(model) %}
    select *
    from {{ model }}
    where is_discontinued = true
      and discontinued_dt is null
{% endtest %}
