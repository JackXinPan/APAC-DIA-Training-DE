
import os
import json
import pandas as pd
from datetime import datetime

# Paths
run_results_path = os.path.join('target', 'run_results.json')
parquet_path = os.path.join('seeds', 'run_results_table.parquet')
csv_path = os.path.join('seeds', 'run_results_table.csv')

# Load run_results.json
with open(run_results_path, 'r') as f:
    data = json.load(f)

# Normalize raw results
results = data.get('results', [])
results_df = pd.json_normalize(results)

# Add ingestion timestamp
results_df['ingestion_ts'] = datetime.utcnow()

# Create seeds folder if needed
os.makedirs('seeds', exist_ok=True)

# Save to Parquet
results_df.to_parquet(parquet_path, index=False)
print("✅ Parquet file saved:", parquet_path)

# Save to CSV
results_df.to_csv(csv_path, index=False)
print("✅ CSV file saved:", csv_path)
