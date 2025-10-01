
select store_id
from {{ ref('stg_sensors') }}
where store_id not in (
  select store_id from {{ ref('stg_stores') }}
)
group by store_id
