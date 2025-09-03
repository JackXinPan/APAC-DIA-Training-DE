import argparse, os, pathlib, random
from datetime import datetime, timedelta, date
import numpy as np
from faker import Faker
from faker_commerce import Provider
from mimesis import Person, Address
import rstr
import pyarrow as pa
import pyarrow.parquet as pq
import xlsxwriter

from faker import Faker
from faker_commerce import Provider
from decimal import Decimal, ROUND_HALF_UP

fake = Faker()
fake.add_provider(Provider)

def get_capped_price(max_value=10000):
    # Generate raw price
    raw_price = fake.ecommerce_price()
    
    # Convert to Decimal and round to 4 places
    price = Decimal(str(raw_price)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    # Cap the price
    return min(price, Decimal(str(max_value)))

# Generate 5 products
for _ in range(5):
    print("Product Name:", fake.ecommerce_name())
    print("Product Category:", fake.ecommerce_category())
    print("Product Subcategory:", fake.ecommerce_material())
    print("Price: $", get_capped_price())
    print("---")


import random
from decimal import Decimal, ROUND_HALF_UP


print(dir(fake))
# List of common currency codes
currency_codes = ['USD', 'EUR', 'GBP', 'AUD', 'CAD', 'JPY', 'CHF', 'CNY']

# Generate random price between 1 and 10000, rounded to 4 decimal places
price = Decimal(str(random.uniform(1, 10000))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

# Pick a random currency
currency = random.choice(currency_codes)

print("Current Price:", price)
print("Currency:", currency)

# Random price (DECIMAL 12,4 style)
price = round(random.uniform(1, 10000), 4)
print(price)