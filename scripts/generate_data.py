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
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, LongType, StringType, TimestampType, IntegerType



print("Delta import successful!")

# Timezone check
# Define the UTC+8 timezone
tz = pytz.timezone("Australia/Perth")  
# Get current date in UTC+8
now = datetime.now(tz).date()
nowtime = datetime.now(tz)
print("Current date in UTC+8:", now.strftime("%Y-%m-%d %H:%M:%S"))
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

### DIMENSION TABLES

#Dimension Keys

    customer_count = 80000
    product_count = 25000
    store_count = 5000
    supplier_count = 8000
    transaction_count = 1000001
    transaction_backdate = 200
    event_count = 2000001
    sensor_count = 1000001
    exchangerates_count = 365*3
    shipment_count = 1000000
    returns_count = 100001


    customer_ids = []
    product_ids = []
    store_ids = []
    store_channel_map = {}# for fact table
#    store_code_map = {}
    supplier_ids = []
    order_ids = []
    product_price_map = {} # for fact table
    
    
    # Minimal sample generation (expand to full volumes per docs)
    fake = Faker('en_AU')
    fake.add_provider(Provider)
    customers_path = out/'customers.csv'
    with customers_path.open('w', encoding='utf-8') as f:
        f.write('customer_id,natural_key,first_name,last_name,email,phone,address_line1,address_line2,city,state_region,postcode,country_code,latitude,longitude,birth_date,join_ts,is_vip,gdpr_consent\n')
        for i in range(1, customer_count):  # TODO raise to 80_000
            customer_ids.append(i)
            nk = 'CUST-' + rstr.rstr(charset, 8)
            email = fake.email() if random.random()>0.01 else 'bad_email' # 0.1 is 10% in base code so changing to 0.01
            lat = -44 + random.random()*10; lon = 112 + random.random()*40
            birth = date(1960,1,1) + timedelta(days=random.randint(0, 20000))
            join_ts = datetime(2024,1,1) + timedelta(days=random.randint(0, 400), seconds=random.randint(0, 86399))
            f.write(f"{i},{nk},{fake.first_name()},{fake.last_name()},{email},{fake.phone_number().replace(',',' ')},{fake.street_address().replace(',',' ')},,{fake.city().replace(',',' ')},{fake.state_abbr()},{fake.postcode()},AU,{lat:.6f},{lon:.6f},{birth.isoformat()},{join_ts.isoformat()},{str(random.random()<0.15)},{str(random.random()>0.05)}\n")
    #products
    products_path = out/'products.csv'
    with products_path.open('w', encoding='utf-8') as f:
        f.write('product_id,sku,name,category,subcategory,current_price,currency,introduced_dt,discontinued_dt,is_discontinued\n')
        for i in range(1, product_count):             
            nk = 'SKU-' + rstr.rstr(charset, 6)
            current_price = round((random.random() ** 2) * 1000, 4) if random.random() > 0.01 else 0.00 # Random price skewed using the squaring or numbers below 1 (DECIMAL 12,4 style)
            introduced_dt = now - timedelta(days=random.randint(0, 2000))
            # Determine discontinued date and indicator
            if random.random() < 0.2:  # 20% chance of being discontinued
                days_since_intro = (now - introduced_dt).days
                discontinued_dt = introduced_dt + timedelta(days=random.randint(0, days_since_intro)) if random.random() > 0.02 else date(1911, 12, 31) #anomaly
                is_discontinued = True                
            else:
                discontinued_dt = date(9999, 12, 31)
                is_discontinued = False
            if not is_discontinued or (now - discontinued_dt).days > transaction_backdate:
                product_ids.append(i) # transactions assumed to not include discontinued products transactions date back 200 days
                product_price_map[i] = current_price # transactions assumed to not include discontinued products transactions date back 200 days
            f.write(f"{i},{nk},{fake.ecommerce_name()},{fake.ecommerce_category()},{fake.ecommerce_material()},{current_price},{fake.currency_code()},{introduced_dt},{discontinued_dt},{is_discontinued}\n")
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
#                store_code_map[i] = nk            
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
    #Suppliers
    suppliers_path = out/'suppliers.csv'
    with suppliers_path.open('w', encoding='utf-8') as f:
        f.write('supplier_id,supplier_code,name,country_code,lead_time_days,preffered\n')
        for i in range(1, supplier_count):  
            supplier_ids.append(i)
            nk =  'S-' + rstr.rstr(charset, 4)         
            ltd = random.randint(1, 28) # 1 to 28 days
            f.write(f"{i},{nk},{fake.company().replace(',',' ')},{fake.country_code().replace(',',' ')},{ltd},{fake.boolean()}\n")
### FACTS TABLES Do them together because they reference each other

    # ordersheader
    ordersheader_path = out/'orders_header.csv'
    #ordersLines
    orderslines_path = out/'orders_lines.csv'
    with ordersheader_path.open('w', encoding='utf-8') as f,orderslines_path.open('w', encoding='utf-8') as olf:
        f.write('order_id,order_dt_month,order_ts,order_dt_local,customer_id,store_id,channel,payment_method,coupon_code,shipping_fee,currency\n')
        olf.write('order_id,order_dt_month,order_ts,line_number,product_id,qty,unit_price,line_discount_pct,tax_pct\n')
        for i in range(1, transaction_count):  
#OrdersHeaders
            # Generate a random date within the last transaction_backdate days
            order_ids.append(i)
            random_days_ago = random.randint(0, transaction_backdate)
            raw_date = now - timedelta(days=random_days_ago)
            #start of month for partioning 
            
            order_dt_month = raw_date.replace(day=1)
            # Create a timestamp by combining raw_date with a random time offset
            random_seconds = random.randint(0, 86399)  # Seconds in a day
            order_ts = tz.localize(datetime.combine(raw_date, datetime.min.time()) + timedelta(seconds=random_seconds))
            order_dt_local = raw_date
            join_ts = datetime(2024,1,1) + timedelta(days=random.randint(0, 400), seconds=random.randint(0, 86399))    
            if random.random() < 0.7:
                coupon_code = rstr.rstr(charset, 10)
                line_discount_pct = random.choice([0.10, 0.20, 0.50]) # 10%, 20% or 50%
            else:
                coupon_code = ''
                line_discount_pct = 0.00
            store_id = random.choice(store_ids) if random.random() > 0.01 else random.uniform(store_count, store_count*2)
            channel = store_channel_map.get(store_id, 'online')
            if channel == 'online':
                rand = random.random()
                if rand < 0.3:
                    payment_method = 'debit'
                elif rand < 0.6:
                    payment_method = 'bitcoin'
                else:
                    payment_method = 'afterpay'
            else:
                if random.random() < 0.5:
                    payment_method = 'debit'
                else:
                    payment_method = 'cash'
            customer_id = random.choice(customer_ids) if random.random() > 0.01 else random.uniform(customer_count, customer_count*2)
            shipping_fee = round(random.uniform(1, 20), 2)
            # write to orderheaders
            f.write(f"{i},{order_dt_month},{order_ts},{order_dt_local},{customer_id},{store_id},{channel},{payment_method},{coupon_code},{shipping_fee},{fake.currency_code()}\n")    
#Orderslines
            # Generate 1–6 lines per order
            num_lines = random.randint(1, 6)
            for line_number in range(1, num_lines + 1):
            # Anomoly
                if random.random() < 0.01:
                    product_id = f"INVALID_{random.randint(1000,9999)}"
                    unit_price = round(random.uniform(1, 1000), 4)
                else:
                    product_id = random.choice(product_ids)
                    unit_price = product_price_map.get(product_id, round(random.uniform(1, 1000), 4))
            # qty (amount of each product) up to 10 
                qty = random.randint(1, 10)
                if random.random() < 0.001:
                    if random.random() < 0.5:
                        qty *= -1  # Rare negative quantity times by negative 1
                    else:
                        qty *= 0   # Rare zero quantity times by 0
                tax_pct = random.choice([0.050, 0.075, 0.100])
                olf.write(f"{i},{order_dt_month},{order_ts},{line_number},{product_id},{qty},{unit_price},{line_discount_pct},{tax_pct}\n")



### Event and IoT Data
    #events JSON
    events_path = out / 'events.jsonl'
    with events_path.open('w', encoding='utf-8') as f:
        for i in range(1, event_count): 
            event_ts = (datetime.now(tz) - timedelta(days=random.randint(0, 200), seconds=random.randint(0, 86400))).isoformat()
            event_date = datetime.fromisoformat(event_ts).date().isoformat()
            event_type = random.choice(["product_view", "cart_add", "checkout", "watchlist", "login", "logout", "signup"])
            user_id = random.choice(customer_ids)
            session_id = f"session-{random.randint(100000, 999999)}"

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
                payload.update({
                    "product_id": random.choice(product_ids),
                    "price": product_price_map.get(product_id, round(random.uniform(1, 1000), 4)),
                    "action": random.choice(["click", "view", "purchase"])          
                })
                if event_type == "checkout":
                    payload.update({
                        "discount_coupon": True if random.random() < 0.7 else False
                    })
            elif event_type in ["login", "signup"]:
                payload.update({
                    "device": random.choice(["mobile", "desktop"]),
                    "ip_address": fake.ipv4(),
                    "geo_location": {
                        "lat": float(fake.latitude()),
                        "lon": float(fake.longitude())
                    }
                })
            elif event_type == "logout":
                payload.update({
                    "session_duration": random.randint(30, 3600),  # seconds
                    "logout_reason": random.choice(["timeout", "manual", "error"])
                })
            event = {"envelope": envelope, "payload": payload}
            f.write(json.dumps(event) + '\n')

# Sensors
    sensors_path = out / 'sensors.csv'
    with sensors_path.open('w', encoding='utf-8') as f:
        f.write('sensor_id,sensor_ts,sensor_month,store_id,shelf_id,temperature_c,humidity_pct,battery_mv\n')

        retail_store_ids = [store_id for store_id, channel in store_channel_map.items() if channel == "retail"]

        for i in range(1, sensor_count):
            #includes anomalies 
            sensor_ts = (datetime.now(tz) - timedelta(days=random.randint(0, 200), seconds=random.randint(0, 86400))).isoformat() if random.random() > 0.01 else ''
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
            f.write(f"{i},{sensor_ts},{sensor_month},{store_id},{shelf_id},{temperature_c},{humidity_pct},{battery_mv}\n")

    # Financial and Operational Data


    # Parameters
    exchangerates_path = out / 'exchangerates.xlsx'
    currencies = ["USD", "EUR", "JPY", "GBP", "NZD", "CNY"]
    exchange_rows = []

    # Loop over each day
    for i in range(exchangerates_count):
        erdate = (now - timedelta(days=i)).isoformat()

        for currency in currencies:
            base_rate = {
                "USD": 1.5,
                "EUR": 1.6,
                "JPY": 0.012,
                "GBP": 1.8,
                "NZD": 0.9,
                "CNY": 0.22
            }[currency]

            # Add slight daily variation
            rate_to_aud = round(base_rate + random.uniform(-0.05, 0.05), 8)  #(DECIMAL 18,8)

            exchange_rows.append({
                "date": erdate,
                "currency": currency,
                "rate_to_aud": rate_to_aud
            })

    # Convert to DataFrame
    df = pd.DataFrame(exchange_rows)

    # Save to Excel
    df.to_excel(exchangerates_path, index=False)
    
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


    ### Returns (delta)
    returns_path = out / 'returns.delta'

    
    spark = SparkSession.builder \
        .appName("DeltaLakeApp") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()



    
    # use order_lines as a reference
    # Read into DataFrame    
    df_orders_lines = pd.read_csv(orderslines_path)

    # Generate base data
    base_data = []
    for i in range(1, returns_count+1):
    # Keep sampling until a valid row with qty ≥ 1 is found
        while True:
            row = df_orders_lines.sample(1).iloc[0]
            qty = row.get('qty', 0)

            if pd.isna(qty) or qty < 1:
                continue  # resample

            qtyret = random.randint(1, int(qty))
            break  # valid row found

        # Calculate the time range
        order_ts = row['order_ts']
        order_ts = pd.to_datetime(order_ts)
        time_now = datetime.now(tz)
        time_diff = (time_now- order_ts).total_seconds()

        # Generate a random offset within that range
        random_offset = random.uniform(0, time_diff)

        # Create return_ts
        return_ts = order_ts + timedelta(seconds=random_offset)  # return_ts 
        # reason 
        reason = random.choice(["damaged", "wrong item", "changed mind", "late delivery"])
        
        base_data.append((
            i,  # return_id
            row['order_id'],  # order_id
            row['product_id'], # product_id
            return_ts, # return_ts
            qtyret,  # qty
            reason,  # reason
            row['order_dt_month'] # partitioning
        ))
        
    schema_v1 = StructType([
        StructField("return_id", LongType(), False),
        StructField("order_id", LongType(), False),
        StructField("product_id", StringType(), False),
        StructField("return_ts", TimestampType(), False),
        StructField("qty", IntegerType(), False),
        StructField("reason", StringType(), False)
    ])
    # Save as Delta table
    df_returns_v1 = spark.createDataFrame(base_data, schema=schema_v1)
    df_returns_v1.write.format("delta").mode("overwrite").save(str(returns_path))

    #v2 evolution
    evolved_data = []
    #map evolved schema
    reason_map = {
    "damaged": "DMG",
    "wrong item": "WRONG_IT",
    "changed mind": "CH_MND",
    "late delivery": "LT_DELIV"
    }
    for i in range(returns_count + 1, returns_count + 101):  # 100 new rows to highlight append
        row = df_orders_lines.sample(1).iloc[0]
        order_id = row['order_id']
        order_ts = row['order_ts']

        qtyret = random.randint(1, max(1, int(row['qty'])))
        time_diff = (now - order_ts).total_seconds()
        return_ts = order_ts + timedelta(seconds=random.uniform(0, time_diff))

        reason = random.choice(list(reason_map.keys()))
        reason_code = reason_map[reason]

        evolved_data.append((
            i,
            int(order_id),
            row['product_id'],
            return_ts,
            qtyret,
            reason,
            row['order_dt_month'], # partitioning
            reason_code # added evolution with reasoncode
        ))
    # Updated schema with return_reason_code
    schema_v2 = StructType([
        StructField("return_id", LongType(), False),
        StructField("order_id", LongType(), False),
        StructField("product_id", StringType(), False),
        StructField("return_ts", TimestampType(), False),
        StructField("qty", IntegerType(), False),
        StructField("reason", StringType(), False),
        StructField("return_reason_code", StringType(), True) # evolved schema
    ])

    # Save as Delta table with schema evolution
    df_returns_v2 = spark.createDataFrame(base_data, schema=schema_v2)
    df_returns_v2.write.format("delta").mode("append").option("mergeSchema", "true").save(str(returns_path))


    print(f"✅ Sample raw written to {out}. Expand to required volumes per /docs.")
if __name__ == '__main__':
    main()
