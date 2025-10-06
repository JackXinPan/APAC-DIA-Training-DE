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

now = 
erdate = now - timedelta(days=i)
    
if erdate.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            continue  # Skip weekends