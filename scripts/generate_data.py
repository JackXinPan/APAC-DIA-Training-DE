# Generate synthetic raw data locally with controlled edge cases.
# Usage: python scripts/generate_data.py --seed 42 --out data_raw
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse, os, pathlib, random
import numpy as np
from faker import Faker
from datetime import datetime, timedelta, date
from mimesis import Person, Address
import rstr
import pyarrow as pa
import pyarrow.parquet as pq

#for commerce synthetic data
from faker_commerce import Provider

#timezone check
import pytz

# random character/ digit fix
import string

# Define the correct character set
charset = string.ascii_uppercase + string.digits 

# read csv
import csv

#JSON
import json
import uuid

#xlsx
import pandas as pd

#shipment pq
import pytz

# returns delta
from deltalake.writer import write_deltalake

import time

print("Delta import successful!")

# Timezone check
# Define the UTC+8 timezone
tz = pytz.timezone("Australia/Perth")  
# Get current date in UTC+8
now = datetime.now(tz).date()
nowtime = datetime.now(tz)
print("Current date in UTC+8:", now.strftime("%Y-%m-%d %H:%M:%S"))

charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--out', type=str, default='data_raw')
    return ap.parse_args()

def ensure_dir(p): pathlib.Path(p).mkdir(parents=True, exist_ok=True)

def main():
    args = parse_args()
    random.seed(args.seed); np.random.seed(args.seed)
    out = pathlib.Path(args.out); ensure_dir(out)

    # Minimal sample generation (expand to full volumes per docs)
    fake = Faker('en_AU')
    fake.add_provider(Provider)
### DIMENSION TABLES

#Dimension Keys
    # THe day the first store opened
    open_ts = tz.localize(datetime(2023, 1, 1))

    customer_count = 80000
    product_count = 25000
    store_count = 5000
    supplier_count = 8000
    transaction_count = 1000001
    transaction_backdate = 365*2
    event_count = 2000001
    sensor_count = 1000001
    exchangerates_count = 365*3
    shipment_count = 1000000
    returns_count = 100001
    v1_returns_count = 90000
    #v2_returns_count = 10000

    currencies = ["USD", "EUR", "AUD", "GBP"]
    countries = ["USA", "GER", "AUS", "UK", "NZ", "FRA", "ITA"]
    customer_ids = []
    product_ids = []
    product_data = []
    product_availability_map = {} # for fact table
    store_ids = []
    store_channel_map = {} # for fact table
#    store_code_map = {}
    supplier_ids = []
    order_ids = []

######Customer
    
    # Prepare data list
    customer_data = []
    customer_join_map ={}
    customer_headers = 'customer_id,natural_key,first_name,last_name,email,phone,address_line1,address_line2,city,state_region,postcode,country_code,latitude,longitude,birth_date,join_ts,is_vip,gdpr_consent\n'
    customer_data.append(customer_headers)

    for i in range(1, customer_count + 1):  # TODO raise to 80_000
        customer_ids.append(i)
        nk = 'CUST-' + rstr.rstr(charset, 9)
        email = fake.email() if random.random()>0.01 else 'bad_email' # 0.1 is 10% in base code so changing to 0.01
        lat = -44 + random.random()*10
        lon = 112 + random.random()*40
        birth = date(1960,1,1) + timedelta(days=random.randint(0, 20000))
        
        # Skewed join_ts toward earlier dates (closer to 2023-01-01)
        total_days = (nowtime - open_ts).days
        skewed_day = int(random.betavariate(2, 5) * total_days)  # alpha < beta = skew toward open_ts

        join_ts = open_ts + timedelta(skewed_day, seconds=random.randint(0, 86399))
        
        customer_join_map[i] = join_ts  # Add to join map
        
        is_vip = str(random.random()<0.15)
        gdpr_consent = str(random.random()>0.05)
        row = f"{i},{nk},{fake.first_name()},{fake.last_name()},{email},{fake.phone_number().replace(',',' ')},{fake.street_address().replace(',',' ')},{fake.street_name().replace(',',' ')},{fake.city().replace(',',' ')},{fake.state_abbr()},{fake.postcode()},{random.choice(currencies)},{lat:.6f},{lon:.6f},{birth.isoformat()},{join_ts.isoformat()},{is_vip},{gdpr_consent}\n"
        customer_data.append(row)
    
    customers_path = out/'customers.csv'
    with customers_path.open('w', encoding='utf-8') as f:
        f.writelines(customer_data)
    print("customer created")    
    
     
    

    product_headers = 'product_id,sku,name,category,subcategory,current_price,currency,introduced_dt,discontinued_dt,is_discontinued\n'
    product_data.append(product_headers)

    for i in range(1, product_count + 1):
        sku = 'SKU-' + rstr.rstr(charset, 6)
        current_price = round((random.random() ** 2) * 1000, 4) if random.random() > 0.01 else 0.00

        total_days = (nowtime - open_ts).days
        skewed_day = int(random.betavariate(2, 5) * total_days)
        introduced_dt = open_ts + timedelta(days=skewed_day)

        # Determine discontinued date and flag
        if random.random() < 0.2:  # 20% chance of being discontinued
            days_since_intro = (nowtime - introduced_dt).days
            if days_since_intro > 0:
                skewed_day = int(random.betavariate(5, 2) * days_since_intro)
                discontinued_dt = introduced_dt + timedelta(days=skewed_day)
            else:
                discontinued_dt = introduced_dt

            if random.random() < 0.02:  # 2% anomaly case
                discontinued_dt = date(1911, 12, 31)

            is_discontinued = True
        else:
            discontinued_dt = date(9999, 12, 31)
            is_discontinued = False



        product_availability_map[i] = {
            'introduced_dt': introduced_dt.date() if isinstance(introduced_dt, datetime) else introduced_dt,
            'discontinued_dt': discontinued_dt.date() if isinstance(discontinued_dt, datetime) else discontinued_dt,
            'unit_price': current_price
        }



        row = f"{i},{sku},{fake.ecommerce_name()},{fake.ecommerce_category()},{fake.ecommerce_material()},{current_price},{random.choice(currencies)},{introduced_dt},{discontinued_dt},{is_discontinued}\n"
        product_data.append(row)


    products_path = out / 'products.csv'
    with products_path.open('w', encoding='utf-8') as f:
        f.writelines(product_data)

    print("Product data created.")

    
      
    #Stores
    existing_nks = [] # for duplicates
    stores_path = out/'stores.csv'
    with stores_path.open('w', encoding='utf-8') as f:
        f.write('store_id,store_code,name,channel,region,state,latitude,longitude,open_dt,close_dt\n')
        for i in range(1, store_count):                 
            if random.random() < 0.01 and existing_nks:  # 1% chance to reuse an existing nk
                nk = random.choice(existing_nks)
                channel = 'online' if nk.startswith('O-') else 'retail'
            else:
                if random.random() < 0.5:
                    channel = 'online'
                    nk = 'O-' + rstr.rstr(charset, 8)
                else:
                    channel = 'retail'
                    nk = 'R-' + rstr.rstr(charset, 8)
                existing_nks.append(nk)
#         store_code_map[i] = nk            
            open_dt = date.today() - timedelta(days=random.randint(0, 2000))
            # Determine discontinued date and indicator
            if random.random() < 0.2:  # 20% chance of being discontinued
                days_since_intro = (now - open_dt).days
                close_dt = open_dt + timedelta(days=random.randint(0, days_since_intro))
            else:
                close_dt = None
            if close_dt is None or (now - close_dt).days > transaction_backdate:
                store_ids.append(i)
                store_channel_map[i] = channel
            # Format close_dt for writing (handle None safely)
            open_dt = open_dt.isoformat()
            close_dt = close_dt.isoformat() if close_dt else ''

            #lat long
            latitude = fake.latitude() if random.random() > 0.01 else float(fake.latitude()) + random.uniform(1000,6000)
            longitude = fake.longitude() if random.random() > 0.01 else float(fake.longitude()) + random.uniform(1000,6000)
            f.write(f"{i},{nk},{'Insight ' + fake.city().replace(',',' ')},{channel},{fake.country().replace(',',' ')},{fake.state()},{latitude},{longitude},{open_dt}, {close_dt}\n")
    print("store created")             
    suppliers_path = out/'suppliers.csv'
    used_codes = set()  # To track used supplier_codes
    with suppliers_path.open('w', encoding='utf-8') as f:
        f.write('supplier_id,supplier_code,name,country_code,lead_time_days,preffered\n')
        for i in range(1, supplier_count):  
            supplier_ids.append(i)

            # Ensure unique supplier_code
            while True:
                nk = 'S-' + rstr.rstr(charset, 4)
                if nk not in used_codes:
                    used_codes.add(nk)
                    break

 
            ltd = random.randint(1, 28) # 1 to 28 days
            f.write(f"{i},{nk},{fake.company().replace(',',' ')},{random.choice(countries)},{ltd},{fake.boolean()}\n")
    print("supplier created")             
            
### FACTS TABLES Do them together because they reference each other

    
    orders_header_data = ['order_id,order_dt_month,order_ts,order_dt_local,customer_id,store_id,channel,payment_method,coupon_code,shipping_fee,currency\n']
    orders_lines_data = ['order_id,order_dt_month,order_ts,line_number,product_id,qty,unit_price,line_discount_pct,tax_pct\n']

    raw_date = nowtime - timedelta(days=transaction_backdate)

    for i in range(1, transaction_count + 1):
        order_ids.append(i)
        # Customer selection
        if random.random() > 0.01:
            customer_id = random.choice(customer_ids)
            customer_join_ts = customer_join_map[customer_id]
        else:
            customer_id = int(random.uniform(customer_count, customer_count * 2))
            customer_join_ts = raw_date

        earliest_order_date = max(customer_join_ts, raw_date)
        days_since_earliest = (nowtime - earliest_order_date).days

        if days_since_earliest > 0:
            random_days_ago = random.randint(0, days_since_earliest)
            order_dt_local = now - timedelta(days=random_days_ago)
        else:
            order_dt_local = earliest_order_date

        random_seconds = random.randint(0, 86399)
        order_dt_local_dt = datetime.combine(order_dt_local, datetime.min.time())
        order_ts = tz.localize(order_dt_local_dt + timedelta(seconds=random_seconds))
        order_dt_month = order_dt_local.replace(day=1)

        # Coupon logic
        if random.random() < 0.7:
            coupon_code = rstr.rstr(charset, 10)
            line_discount_pct = random.choice([0.10, 0.20, 0.50])
        else:
            coupon_code = ''
            line_discount_pct = 0.00

        store_id = random.choice(store_ids) if random.random() > 0.01 else int(random.uniform(store_count, store_count * 2))
        channel = store_channel_map.get(store_id, 'online')

        payment_method = (
            random.choices(['debit', 'bitcoin', 'afterpay'], weights=[0.3, 0.3, 0.4])[0]
            if channel == 'online'
            else random.choice(['debit', 'cash'])
        )

        shipping_fee = round(random.uniform(1, 20), 2)
        currency = random.choice(currencies)

        # Append to order header list
        orders_header_data.append(
            f"{i},{order_dt_month},{order_ts},{order_dt_local},{customer_id},{store_id},{channel},{payment_method},{coupon_code},{shipping_fee},{currency}\n"
        )

        # Filter valid products for this order timestamp
        valid_products = [
            pid for pid, info in product_availability_map.items()
            if info['introduced_dt'] <= order_ts.date() <= info['discontinued_dt']
        ]

        if not valid_products:
            continue  # Skip this order if no valid products are available

        num_lines = random.randint(1, 6)
        for line_number in range(1, num_lines + 1):
            if random.random() < 0.01:
                product_id = int(random.choice(valid_products) * 20)
                unit_price = round(random.uniform(1, 1000), 4)
            else:
                product_id = random.choice(valid_products)
                unit_price = round(product_availability_map[product_id]['unit_price'], 4)

            qty = random.randint(1, 10)
            if random.random() < 0.001:
                qty = qty * -1 if random.random() < 0.5 else 0

            tax_pct = random.choice([0.050, 0.010, 0.150])

            orders_lines_data.append(
                f"{i},{order_dt_month},{order_ts},{line_number},{product_id},{qty},{unit_price},{line_discount_pct},{tax_pct}\n"
            )

    # Write to files after loop
    ordersheader_path = out / 'orders_header.csv'
    orderslines_path = out / 'orders_lines.csv'

    with ordersheader_path.open('w', encoding='utf-8') as f:
        f.writelines(orders_header_data)

    with orderslines_path.open('w', encoding='utf-8') as olf:
        olf.writelines(orders_lines_data)

    print("Order header and line data created.")

#Add duplicate order_id for anomaly
    
    orders_data = pd.read_csv(ordersheader_path)

    # Determine how many duplicates to insert (0.5% of total)
    duplicate_count = int(transaction_count * 0.005)

    # Randomly select indices to duplicate
    duplicate_indices = random.sample(range(len(orders_data)), duplicate_count)

    # Append duplicates to the CSV
    with ordersheader_path.open('a', encoding='utf-8') as f:
        for idx in duplicate_indices:
            row = orders_data.iloc[idx]
            f.write(','.join(map(str, row.values)) + '\n')

    print("orderheader/orderline created")     
### Event and IoT Data
    #events JSON
    events_path = out / 'events.jsonl'
    event_types = ["product_view", "cart_add", "checkout", "watchlist", "login", "logout", "signup"]
    actions = ["click", "view", "purchase"]
    devices = ["mobile", "desktop"]
    logout_reasons = ["timeout", "manual", "error"]
    event_lines = []
    for i in range(1, event_count): 
        event_ts = (nowtime - timedelta(days=random.randint(0, transaction_backdate), seconds=random.randint(0, 86400))).isoformat()
        event_date = datetime.fromisoformat(event_ts).date().isoformat()
        event_type = random.choice(event_types)
        user_id = random.choice(customer_ids)
        session_id = f"session-{random.randint(1000000, 9999999)}"

        envelope = {
            "event_id": str(i),  # Use loop index as event_id
            "event_ts": event_ts,
            "event_type": event_type,
            "user_id": user_id,
            "session_id": session_id,
            "event_date": event_date
        }
        # global parameters
        payload = {
            "event_ts": event_ts
        }
        # Dynamic payload
        if event_type in ["product_view", "cart_add", "checkout", "watchlist"]:
            product_id = random.choice(list(product_availability_map.keys()))
            payload.update({
                "product_id": product_id,
                "price": round(product_availability_map[product_id]['unit_price'], 4),
                "action": random.choice(actions)          
            })
            if event_type == "checkout":
                payload.update({
                    "discount_coupon": True if random.random() < 0.7 else False
                })
        elif event_type in ["login", "signup"]:
            payload.update({
                "device": random.choice(devices),
                "ip_address": fake.ipv4(),
                "geo_location": {
                    "lat": float(fake.latitude()),
                    "lon": float(fake.longitude())
                }
            })
        elif event_type == "logout":
            payload.update({
                "session_duration": random.randint(30, 3600),  # seconds
                "logout_reason": random.choice(logout_reasons)
            })
        event = {"envelope": envelope, "payload": payload}
        event_lines.append(json.dumps(event))
    
    with events_path.open('w', encoding='utf-8') as f:
        f.write('\n'.join(event_lines))

    print("events created")     
# Sensors
    sensors_path = out / 'sensors.csv'
    sensor_lines = ['sensor_id,sensor_ts,sensor_month,store_id,shelf_id,temperature_c,humidity_pct,battery_mv']
    retail_store_ids = [store_id for store_id, channel in store_channel_map.items() if channel == "retail"]

    for i in range(1, sensor_count):
        #includes anomalies 
        sensor_ts = (nowtime - timedelta(days=random.randint(0, transaction_backdate), seconds=random.randint(0, 86400))).isoformat() if random.random() > 0.01 else ''
        sensor_dt = datetime.fromisoformat(sensor_ts) if sensor_ts else ''
        sensor_month = sensor_dt.replace(day=1).date().isoformat() if sensor_dt else ''

        store_id = random.choice(retail_store_ids)
        shelf_id = rstr.rstr(charset, 6)

        # Temperature, inc anomalies
        if random.random() < 0.01:
            temperature_c = round(random.uniform(70.0, 100.0), 2) if random.random() < 0.5 else round(random.uniform(-50.0, -10.0), 2)
        else:
            temperature_c = round(random.normalvariate(22.0, 3.0), 2)

        # Humidity, inc anomalies
        if random.random() < 0.015:
            humidity_pct = round(random.uniform(-100.0, 200.0), 2)
        else:
            humidity_pct = round(random.normalvariate(50.0, 10.0), 2)
        battery_mv = random.randint(1000, 5000)
        sensor_lines.append(f"{i},{sensor_ts},{sensor_month},{store_id},{shelf_id},{temperature_c},{humidity_pct},{battery_mv}")
    
    # Write all lines at once
    with sensors_path.open('w', encoding='utf-8') as f:
        f.write('\n'.join(sensor_lines))

    print("sensors created")     
    
    # Financial and Operational Data
    # Parameters
    exchangerates_path = out / 'exchangerates.xlsx'
    
    exchange_rows = []

    # Loop over each day
    for i in range(exchangerates_count):
        
        erdate = now - timedelta(days=i)
    
        if erdate.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            continue  # Skip weekends

        
        # Determine variation range
        if erdate.weekday() == 0:  # Monday
            variation = 0.15
        else:
            variation = 0.05


        for currency in currencies:
            if currency == "AUD":
                rate_to_aud = 1.0
            else:
                base_rate = {
                    "USD": 1.5,
                    "EUR": 1.6,
                    "GBP": 1.8,
                }[currency]
                rate_to_aud = round(base_rate + random.uniform(-variation, variation), 8)

            exchange_rows.append({
                "date": erdate,
                "currency": currency,
                "rate_to_aud": rate_to_aud
            })



    # Convert to DataFrame
    df = pd.DataFrame(exchange_rows)

    # Save to Excel
    df.to_excel(exchangerates_path, index=False)
    
    print("exchangerates created")
### Shipping

    sla_days = 5  # SLA for delivery
    
    shippingorder_ids = None
    # Generate data
    shipment_ids = list(range(1, shipment_count + 1))
    shippingorder_ids = [random.choice(order_ids) for _ in range(shipment_count)]
    carriers = ["AUSPOST", "TOLL", "SENDLE", "ARAMEX"]
    carrier_values = [random.choice(carriers) for _ in range(shipment_count)]

    shipped_at_values = [
        datetime(2025, 1, 1, tzinfo=tz) + timedelta(days=random.randint(0, 180))
        for _ in range(shipment_count)
    ]

    delivered_at_values = []
    for shipped in shipped_at_values:
        rand = random.random()
        if rand < 0.02:
            # Late delivery
            delivered = shipped + timedelta(days=sla_days + random.randint(1, 5))
        elif rand < 0.10:
            # In-transit (null)
            delivered = None
        else:
            # On-time delivery
            delivered = shipped + timedelta(days=random.randint(1, sla_days))
        delivered_at_values.append(delivered)

    ship_cost_values = [round(random.uniform(5.00, 25.00), 2) for _ in range(shipment_count)]

    # Build Shipments table
    table = pa.table({
        "shipment_id": pa.array(shipment_ids, type=pa.int64()),
        "order_id": pa.array(shippingorder_ids, type=pa.int64()),
        "carrier": pa.array(carrier_values, type=pa.string()),
        "shipped_at": pa.array(shipped_at_values, type=pa.timestamp("us", tz="Australia/Perth")),
        "delivered_at": pa.array(delivered_at_values, type=pa.timestamp("us", tz="Australia/Perth")),
        "ship_cost": pa.array(ship_cost_values).cast(pa.decimal128(12, 2)),
    })

    # Write to Parquet
    pq.write_table(table, out/'shipments.parquet', compression='snappy')

    print("shipments created")
### Returns (delta)

    # Paths
    orderslines_path = out / 'orders_lines.csv'
    returns_v1_path = out / 'returns_v1'
    returns_v2_path = out / 'returns_v2'

    # Read order_lines.csv
    df_orders_lines = pd.read_csv(orderslines_path)

    # Filter valid rows with qty ≥ 1
    valid_order_rows = df_orders_lines[df_orders_lines['qty'].fillna(0) >= 1]

    # Prebatch sampling for performance (no duplicates)
    sampled_rows = valid_order_rows.sample(n=returns_count).reset_index(drop=True)
        
    # prebatch for v1 and v2
    v1_sampled_rows = sampled_rows.head(n=v1_returns_count).reset_index(drop=True)
    v2_sampled_rows = sampled_rows.tail(len(sampled_rows) - v1_returns_count).reset_index(drop=True)

    # Generate synthetic returns data
    base_data = []
    for i, row in enumerate(v1_sampled_rows.itertuples(index=False), start=1):
        qtyret = random.randint(1, int(row.qty))
        order_ts = pd.to_datetime(row.order_ts)
        time_now = datetime.now(tz)
        time_diff = (time_now - order_ts).total_seconds()
        random_offset = random.uniform(0, time_diff)
        return_ts = (order_ts + timedelta(seconds=random_offset)).replace(tzinfo=None)
        reason = random.choice(["damaged", "wrong item", "changed mind", "late delivery"])
        base_data.append({
            "return_id": i,
            "order_id": row.order_id,
            "product_id": row.product_id,
            "return_ts": return_ts,
            "qty": qtyret,
            "reason": reason
        })

    # Convert to DataFrame and then to PyArrow Table

    df_returns = pd.DataFrame(base_data).sort_values(by="return_ts").reset_index(drop=True)
    table = pa.Table.from_pandas(df_returns)


    # Write to Delta Lake folder
    write_deltalake(str(returns_v1_path), table, mode="overwrite")

    
## v2


    reason_map = {
        "damaged": "DMG",
        "wrong item": "WRONG_IT",
        "changed mind": "CH_MND",
        "late delivery": "LT_DELIV"
    }

    evolved_data = []

    for i, row in enumerate(v2_sampled_rows.itertuples(index=False), start=v1_returns_count + 1):
        order_ts = pd.to_datetime(row.order_ts)
        time_diff = (time_now - order_ts).total_seconds()
        return_ts = order_ts + timedelta(seconds=random.uniform(0, time_diff))

        reason = random.choice(list(reason_map.keys()))
        reason_code = reason_map[reason]

        evolved_data.append({
            "return_id": i,
            "order_id": row.order_id,
            "product_id": row.product_id,
            "return_ts": return_ts.replace(tzinfo=None),
            "qty": random.randint(1, max(1, int(row.qty))),
            "reason": reason,
            "return_reason_code": reason_code
        })

    # Convert to PyArrow Table

    df_evolved = pd.DataFrame(evolved_data).sort_values(by="return_ts").reset_index(drop=True)
    table_evolved = pa.Table.from_pandas(df_evolved)


    # Append to Delta Lake with schema evolution
    write_deltalake(str(returns_v2_path), table_evolved, mode="overwrite")

    print("return v1 and v2 created")     
    
    print(f"✅ Sample raw written to {out}. Expand to required volumes per /docs.")
if __name__ == '__main__':
    


    start_time = time.time()

    main()
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Task completed in {duration:.2f} seconds")