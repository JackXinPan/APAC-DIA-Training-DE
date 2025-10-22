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

##
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

# Timezone check
# Define the UTC+8 timezone
tz = pytz.timezone("Australia/Perth")  
# Get current date in UTC+8
now = datetime.now(tz).date()
nowtime = datetime.now(tz)
print("Current date in UTC+8:", now.strftime("%Y-%m-%d %H:%M:%S"))

charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
currencies = ["USD", "EUR", "AUD", "GBP"]
countries = ["USA", "GER", "AUS", "UK", "NZ", "FRA", "ITA"]
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
#read

    customers_df = pd.read_csv('data_raw/customers.csv')
    customer_join_map = dict(zip(customers_df['customer_id'], pd.to_datetime(customers_df['join_ts'])))
    stores_df = pd.read_csv('data_raw/stores.csv')
    store_channel_map = dict(zip(stores_df['store_id'], stores_df['channel']))
    products_df = pd.read_csv('data_raw/products.csv')
    product_availability_map = {}
    
    for i, row in products_df.iterrows():
        product_availability_map[row['product_id']] = {
            'unit_price': row['current_price'],
            'is_continued': row.get('is_continued', True)  # default to True if missing
        }
 



### Generate a second set of order data testing
#Dimension Keys
### FACTS TABLES Do them together because they reference each other

    
    orders_header_data = ['order_id,order_dt_month,order_ts,order_dt_local,customer_id,store_id,channel,payment_method,coupon_code,shipping_fee,currency\n']
    orders_lines_data = ['order_id,order_dt_month,order_ts,line_number,product_id,qty,unit_price,line_discount_pct,tax_pct\n']


    order_ids = []
    customer_ids = customers_df['customer_id'].tolist()
    for i in range(transaction_count  * 2 , transaction_count * 2 + 10002): # picking up from last transaction count
        order_ids.append(i)
        # Customer selection
        customer_id = random.choice(customer_ids)
 ##     customer_join_ts = customer_join_map[customer_id]
        ##for second load just keep date last 2 days ago
        order_dt_local = now - timedelta(days=random.choice([1, 2]))
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

        store_id = random.choice(stores_df['store_id'].tolist())
        channel = store_channel_map.get(store_id)

        payment_method = (
            random.choices(['debit', 'bitcoin', 'afterpay'], weights=[0.3, 0.3, 0.4])[0]
            if channel == 'online'
            else random.choice(['debit', 'cash']) #retail
        )

        shipping_fee = round(random.uniform(1, 20), 2)
        currency = random.choice(currencies)
        
        

        # Append to order header list
        orders_header_data.append(
            f"{i},{order_dt_month},{order_ts},{order_dt_local},{customer_id},{store_id},{channel},{payment_method},{coupon_code},{shipping_fee},{currency}\n"
        )
##      # Generate order lines
        # Filter valid products for this order timestamp
        valid_products = [
            pid for pid, info in product_availability_map.items()
            if info['is_continued']
        ]

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
    ordersheader_path = out / 'orders_header_day1.csv'
    orderslines_path = out / 'orders_lines_day1.csv'

    with ordersheader_path.open('w', encoding='utf-8') as f:
        f.writelines(orders_header_data)

    with orderslines_path.open('w', encoding='utf-8') as olf:
        olf.writelines(orders_lines_data)

    print("Order header and line data created.")

    print("orderheader/orderline created") 

if __name__ == '__main__':
    
    start_time = time.time()

    main()
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Task completed in {duration:.2f} seconds")