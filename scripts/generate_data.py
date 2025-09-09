# Generate synthetic raw data locally with controlled edge cases.
# Usage: python scripts/generate_data.py --seed 42 --out data_raw
import argparse, os, pathlib, random
from datetime import datetime, timedelta, date
import numpy as np
from faker import Faker
from mimesis import Person, Address
import rstr
import pyarrow as pa
import pyarrow.parquet as pq
import xlsxwriter

#for commerce synthetic data
from faker_commerce import Provider

#timezone check
import pytz

# random character/ digit fix

import rstr
import string

# Define the correct character set
charset = string.ascii_uppercase + string.digits 

# Timezone check
# Define the UTC+8 timezone
utc_plus_8 = pytz.timezone('Australia/Perth')  

# Get current date in UTC+8
now = datetime.now(utc_plus_8).date()
nowtime = datetime.now(utc_plus_8)
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

    customer_ids = []
    product_ids = []
    store_ids = []
    supplier_ids = []
    order_ids = []
    
    # Minimal sample generation (expand to full volumes per docs)
    fake = Faker('en_AU')
    fake.add_provider(Provider)
    customers_path = out/'customers.csv'
    with customers_path.open('w', encoding='utf-8') as f:
        f.write('customer_id,natural_key,first_name,last_name,email,phone,address_line1,address_line2,city,state_region,postcode,country_code,latitude,longitude,birth_date,join_ts,is_vip,gdpr_consent\n')
        for i in range(1, supplier_count):  # TODO raise to 80_000
            customer_ids.append(i)
            nk = 'CUST-' + rstr.rstr(charset, 8)
            email = fake.email() if random.random()>0.1 else 'bad_email'
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
            current_price = round(random.uniform(1, 10000), 4)# Random price (DECIMAL 12,4 style)
            introduced_dt = now - timedelta(days=random.randint(0, 2000))
            # Determine discontinued date and indicator
            if random.random() < 0.2:  # 20% chance of being discontinued
                days_since_intro = (now - introduced_dt).days
                discontinued_dt = introduced_dt + timedelta(days=random.randint(0, days_since_intro))
                is_discontinued = True                
            else:
                discontinued_dt = date(9999, 12, 31)
                is_discontinued = False
                product_ids.append(i)
            f.write(f"{i},{nk},{fake.ecommerce_name()},{fake.ecommerce_category()},{fake.ecommerce_material()},{current_price},{fake.currency_code()},{introduced_dt},{discontinued_dt},{is_discontinued}\n")
    #Stores
    stores_path = out/'stores.csv'
    with stores_path.open('w', encoding='utf-8') as f:
        f.write('store_id,store_code,name,channel,region,state,latitude,longitude,open_dt,close_dt\n')
        for i in range(1, store_count):             
            if random.random() < 0.5: # 50/50 online or retail
                channel = 'online'
                nk =  'O-' + rstr.rstr(charset, 4)
            else:
                channel = 'retail'
                nk =  'R-' + rstr.rstr(charset, 4)
            
            open_dt = date.today() - timedelta(days=random.randint(0, 2000))
            # Determine discontinued date and indicator
            if random.random() < 0.2:  # 20% chance of being discontinued
                days_since_intro = (now - open_dt).days
                close_dt = open_dt + timedelta(days=random.randint(0, days_since_intro))
            else:
                close_dt = '' 
                store_ids.append(i)
            f.write(f"{i},{nk},{'Insight ' + fake.city().replace(',',' ')},{channel},{fake.country().replace(',',' ')},{fake.state()},{fake.latitude()},{fake.longitude()},{open_dt}, {close_dt}\n")
    #Suppliers
    suppliers_path = out/'suppliers.csv'
    with suppliers_path.open('w', encoding='utf-8') as f:
        f.write('supplier_id,supplier_code,name,country_code,lead_time_days,preffered\n')
        for i in range(1, supplier_count):  
#            supplier_ids.append(i)
            nk =  'S-' + rstr.rstr(charset, 4)         
            ltd = random.randint(1, 28) # 1 to 28 days
            f.write(f"{i},{nk},{fake.company().replace(',',' ')},{fake.country_code().replace(',',' ')},{ltd},{fake.boolean()}\n")
### FACTS TABLES

    # ordersheader
    ordersheader_path = out/'orders_header.csv'
    with ordersheader_path.open('w', encoding='utf-8') as f:
        f.write('order_id,order_dt_month,order_ts,order_dt_local,customer_id,store_id,channel,payment_method,coupon_code,shipping_fee,currency\n')
        for i in range(1, 1000001):  
            # Generate a random date within the last 200 days
            order_ids.append(i)
            random_days_ago = random.randint(0, 200)
            raw_date = now - timedelta(days=random_days_ago)
            #start of month for partioning 
            
            order_dt_month = raw_date.replace(day=1)
            # Create a timestamp by combining raw_date with a random time offset
            random_seconds = random.randint(0, 86399)  # Seconds in a day
            order_ts = datetime.combine(raw_date, datetime.min.time()) + timedelta(seconds=random_seconds)
            order_dt_local = raw_date
            join_ts = datetime(2024,1,1) + timedelta(days=random.randint(0, 400), seconds=random.randint(0, 86399))
            if random.random() < 0.5:  # 50/50 online or retail
                channel = 'online'
                rand = random.random()
                if rand < 0.3:
                    payment_method = 'debit'
                elif rand < 0.6:
                    payment_method = 'bitcoin'
                else:
                    payment_method = 'afterpay'
            else:
                channel = 'retail'
                if random.random() < 0.5:
                    payment_method = 'debit'
                else:
                    payment_method = 'cash'
            if random.random() < 0.7:
                coupon_code = rstr.rstr(charset, 10)
            else:
                coupon_code = ''                    
            f.write(f"{i},{order_dt_month},{order_ts},{order_dt_local},{random.choice(customer_ids)},{random.choice(store_ids)},{channel},{payment_method},{rstr.rstr(charset, 10)},{round(random.uniform(1, 20), 2)},{fake.currency_code()}\n")

    #ordersLines
    orderslines_path = out/'orders_lines.csv'
    with orderslines_path.open('w', encoding='utf-8') as f:
        f.write('order_id,order_dt_month, line_number,product_id,qty,unit_price,line_discount_pct,tax_pct\n')
        for i in range(1, 3000001):  
            # Generate a random date within the last 200 days
            random_days_ago = random.randint(0, 200)
            raw_date = now - timedelta(days=random_days_ago)
            #start of month for partioning 
            
            order_dt_month = raw_date.replace(day=1)
            # Create a timestamp by combining raw_date with a random time offset
            random_seconds = random.randint(0, 86399)  # Seconds in a day
            order_ts = datetime.combine(raw_date, datetime.min.time()) + timedelta(seconds=random_seconds)
            order_dt_local = raw_date
            join_ts = datetime(2024,1,1) + timedelta(days=random.randint(0, 400), seconds=random.randint(0, 86399))
            if random.random() < 0.5:  # 50/50 online or retail
                channel = 'online'
                rand = random.random()
                if rand < 0.3:
                    payment_method = 'debit'
                elif rand < 0.6:
                    payment_method = 'bitcoin'
                else:
                    payment_method = 'afterpay'
            else:
                channel = 'retail'
                if random.random() < 0.5:
                    payment_method = 'debit'
                else:
                    payment_method = 'cash'
            if random.random() < 0.7:
                coupon_code = rstr.rstr(charset, 10)
            else:
                coupon_code = ''                    
            f.write(f"{i},{order_dt_month},{order_ts},{order_dt_local},{random.choice(customer_ids)},{random.choice(store_ids)}}\n")

    # Shipments parquet sample
    tbl = pa.table({
        'shipment_id': pa.array(range(1, 10001), type=pa.int64()),
        'order_id': pa.array(range(1, 10001), type=pa.int64()),
        'carrier': pa.array(['AUSPOST']*10000, type=pa.string()),
        'shipped_at': pa.array([datetime(2024,1,1)+timedelta(days=i%90) for i in range(10000)], type=pa.timestamp('us')),
        'delivered_at': pa.array([datetime(2024,1,2)+timedelta(days=i%90) for i in range(10000)], type=pa.timestamp('us')),
        'ship_cost': pa.array([1995]*10000, type=pa.int64()).cast(pa.decimal128(21,2)),
    })
    pq.write_table(tbl, out/'shipments.parquet', compression='snappy')
    

    print(f"✅ Sample raw written to {out}. Expand to required volumes per /docs.")
if __name__ == '__main__':
    main()
