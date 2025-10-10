select *
from {{ ref('stg_products') }}
where is_discontinued = true
  and discontinued_dt is null

