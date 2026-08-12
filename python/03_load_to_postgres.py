import pandas as pd
from sqlalchemy import create_engine

# ---- UPDATE THESE WITH YOUR POSTGRES DETAILS ----
DB_USER = 'postgres'
DB_PASSWORD = 'ac1104ac'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'quick_commerce'
# ---------------------------------------------------

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# order matters: parents before children (foreign key dependencies)
load_order = [
    ('customers', 'customers.csv'),
    ('dark_stores', 'dark_stores.csv'),
    ('products', 'products.csv'),
    ('riders', 'riders.csv'),
    ('inventory_stock', 'inventory_stock.csv'),
    ('orders', 'orders.csv'),
    ('order_items', 'order_items.csv'),
    ('weather_traffic_flags', 'weather_traffic_flags.csv'),
]

for table_name, filename in load_order:
    print(f"Loading {filename} into '{table_name}'...")
    df = pd.read_csv(f'../data/{filename}')
    df.to_sql(table_name, engine, if_exists='append', index=False, method='multi', chunksize=5000)
    print(f"  Done: {len(df)} rows loaded")

print("\nAll tables loaded successfully.")