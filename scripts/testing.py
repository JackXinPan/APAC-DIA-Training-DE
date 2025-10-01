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


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--out', type=str, default='data_raw')
    return ap.parse_args()

def ensure_dir(p): pathlib.Path(p).mkdir(parents=True, exist_ok=True)


args = parse_args()
random.seed(args.seed); np.random.seed(args.seed)
out = pathlib.Path(args.out); ensure_dir(out)

#Add duplicate order_id for anomaly
ordersheader_path = out/'orders_header.csv'
orders_data = pd.read_csv(ordersheader_path)
transaction_count = len(orders_data)

# Determine how many duplicates to insert (0.5% of total)
duplicate_count = int(transaction_count * 0.005)

# Randomly select indices to duplicate
duplicate_indices = random.sample(range(len(orders_data)), duplicate_count)

# Append duplicates to the CSV
with ordersheader_path.open('a', encoding='utf-8') as f:
    for idx in duplicate_indices:
        row = orders_data.iloc[idx]
        f.write(','.join(map(str, row.values)) + '\n')
