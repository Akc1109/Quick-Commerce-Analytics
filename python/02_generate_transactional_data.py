import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

# ---------- LOAD BASE TABLES ----------
customers = pd.read_csv('../data/customers.csv')
dark_stores = pd.read_csv('../data/dark_stores.csv')
products = pd.read_csv('../data/products.csv')
riders = pd.read_csv('../data/riders.csv')

END_DATE = datetime.now().date()
START_DATE = END_DATE - timedelta(days=90)
DATE_LIST = [START_DATE + timedelta(days=i) for i in range(91)]

city_to_stores = dark_stores.groupby('city')['store_id'].apply(list).to_dict()
store_to_zone = dict(zip(dark_stores['store_id'], dark_stores['zone']))
store_to_riders = riders.groupby('store_id')['rider_id'].apply(list).to_dict()

print("Step 1/4: Generating weather/traffic flags...")

# ---------- WEATHER / TRAFFIC FLAGS ----------
zones = dark_stores[['zone']].drop_duplicates().reset_index(drop=True)

def traffic_probs(hour):
    if hour in [12, 13, 18, 19, 20, 21]:
        return [0.1, 0.3, 0.6]
    elif hour in range(0, 6):
        return [0.8, 0.15, 0.05]
    else:
        return [0.4, 0.4, 0.2]

traffic_rows = []
flag_id = 1
for z in zones['zone']:
    for d in DATE_LIST:
        for h in range(24):
            probs = traffic_probs(h)
            level = np.random.choice(['low', 'medium', 'high'], p=probs)
            weather = np.random.choice(['Clear', 'Rain', 'Cloudy'], p=[0.75, 0.1, 0.15])
            traffic_rows.append((flag_id, d, z, h, level, weather))
            flag_id += 1

weather_traffic_flags = pd.DataFrame(traffic_rows, columns=[
    'flag_id', 'date', 'zone', 'hour', 'traffic_level', 'weather'
])
weather_traffic_flags.to_csv('../data/weather_traffic_flags.csv', index=False)
print(f"  Done: {len(weather_traffic_flags)} rows")

print("Step 2/4: Generating orders (this may take 1-2 minutes)...")

# ---------- ORDERS ----------
HOUR_WEIGHTS = []
for h in range(24):
    if h in [12, 13, 18, 19, 20, 21]:
        HOUR_WEIGHTS.append(3.0)
    elif h in [8, 9, 10, 11, 14, 15, 16, 17, 22]:
        HOUR_WEIGHTS.append(1.5)
    else:
        HOUR_WEIGHTS.append(0.3)

DATE_WEIGHTS = [1.5 if d.weekday() >= 5 else 1.0 for d in DATE_LIST]

order_rows = []
order_id = 1
for cust_id, city in zip(customers['customer_id'], customers['city']):
    tier_roll = random.random()
    if tier_roll < 0.70:
        num_orders = random.randint(1, 3)
    elif tier_roll < 0.95:
        num_orders = random.randint(4, 8)
    else:
        num_orders = random.randint(9, 20)

    for _ in range(num_orders):
        store_id = random.choice(city_to_stores[city])
        order_date = random.choices(DATE_LIST, weights=DATE_WEIGHTS, k=1)[0]
        order_hour = random.choices(range(24), weights=HOUR_WEIGHTS, k=1)[0]
        order_minute = random.randint(0, 59)
        order_time = datetime.combine(order_date, datetime.min.time()) + timedelta(hours=order_hour, minutes=order_minute)

        promised_delivery_time = order_time + timedelta(minutes=random.randint(12, 18))

        rider_list = store_to_riders.get(store_id, [])
        rider_id = random.choice(rider_list) if rider_list and random.random() > 0.02 else None

        order_rows.append((order_id, cust_id, store_id, rider_id, order_time, promised_delivery_time))
        order_id += 1

orders = pd.DataFrame(order_rows, columns=[
    'order_id', 'customer_id', 'store_id', 'rider_id', 'order_time', 'promised_delivery_time'
])
print(f"  Base orders created: {len(orders)}")

# ---------- SLA BREACH LOGIC ----------
orders['date'] = orders['order_time'].dt.date
orders['hour'] = orders['order_time'].dt.hour
orders['zone'] = orders['store_id'].map(store_to_zone)

# concurrent load per store-hour
load = orders.groupby(['store_id', 'date', 'hour']).size().reset_index(name='concurrent_orders')
orders = orders.merge(load, on=['store_id', 'date', 'hour'], how='left')

# merge traffic level and weather
orders = orders.merge(
    weather_traffic_flags[['zone', 'date', 'hour', 'traffic_level', 'weather']],
    on=['zone', 'date', 'hour'], how='left'
)
orders['traffic_level'] = orders['traffic_level'].fillna('medium')
orders['weather'] = orders['weather'].fillna('Clear')

# each store has its own baked-in efficiency (some stores are just better run than others)
store_ids = dark_stores['store_id'].unique()
store_effect_map = dict(zip(store_ids, np.random.normal(0, 3, size=len(store_ids)).clip(-5, 8)))
orders['store_effect'] = orders['store_id'].map(store_effect_map)

traffic_effect_map = {'low': 0, 'medium': 3, 'high': 9}
orders['traffic_effect'] = orders['traffic_level'].map(traffic_effect_map)
orders['weather_effect'] = np.where(orders['weather'] == 'Rain', 4, 0)
orders['load_effect'] = np.clip((orders['concurrent_orders'] - 15) * 0.4, 0, None)
orders['base_delay'] = np.random.normal(7, 1.5, size=len(orders)).clip(min=2)
orders['noise'] = np.random.normal(0, 1.5, size=len(orders))

orders['delivery_minutes'] = (orders['base_delay'] + orders['store_effect'] + orders['traffic_effect'] +
                               orders['weather_effect'] + orders['load_effect'] + orders['noise']).clip(lower=2)
orders['actual_delivery_time'] = orders['order_time'] + pd.to_timedelta(orders['delivery_minutes'], unit='m')

orders = orders.drop(columns=['date', 'hour', 'zone', 'concurrent_orders', 'traffic_level', 'weather',
                               'store_effect', 'traffic_effect', 'weather_effect', 'load_effect',
                               'base_delay', 'noise', 'delivery_minutes'])

print("Step 3/4: Generating order items...")

# ---------- ORDER ITEMS ----------
category_weights = {
    'Dairy': 3.0, 'Fruits & Vegetables': 3.0, 'Bakery': 1.5, 'Snacks': 2.5,
    'Beverages': 2.0, 'Personal Care': 0.8, 'Household': 0.8, 'Frozen Foods': 1.2
}
products['weight'] = products['category'].map(category_weights)

item_rows = []
item_id = 1
for oid in orders['order_id']:
    n_items = random.randint(1, 6)
    chosen = products.sample(n=n_items, weights=products['weight'], replace=True)
    for _, prod in chosen.iterrows():
        qty = random.randint(1, 3)
        item_rows.append((item_id, oid, prod['product_id'], qty, prod['price']))
        item_id += 1

order_items = pd.DataFrame(item_rows, columns=[
    'order_item_id', 'order_id', 'product_id', 'quantity', 'price_at_order'
])
print(f"  Order items created: {len(order_items)}")

# compute order_value from items and merge back
order_value = (order_items['quantity'] * order_items['price_at_order']).groupby(order_items['order_id']).sum()
orders = orders.merge(order_value.rename('order_value'), left_on='order_id', right_index=True, how='left')

orders.to_csv('../data/orders.csv', index=False)
order_items.to_csv('../data/order_items.csv', index=False)

print("Step 4/4: Generating inventory stock...")

# ---------- INVENTORY STOCK (demand-aware) ----------
# calculate actual demand per store-product from the orders we just generated
oi_with_store = order_items.merge(orders[['order_id', 'store_id']], on='order_id', how='left')
demand_per_store_product = oi_with_store.groupby(['store_id', 'product_id'])['quantity'].sum().reset_index()
demand_per_store_product.rename(columns={'quantity': 'total_demand'}, inplace=True)
demand_lookup = demand_per_store_product.set_index(['store_id', 'product_id'])['total_demand'].to_dict()

stock_rows = []
stock_id = 1
for _, store in dark_stores.iterrows():
    for _, prod in products.iterrows():
        key = (store['store_id'], prod['product_id'])
        actual_demand = demand_lookup.get(key, 30)  # fallback for rare zero-demand cases

        mismatch_roll = random.random()
        if mismatch_roll < 0.15:
            target_total = actual_demand * random.uniform(1.4, 1.8)   # overstocked
        elif mismatch_roll < 0.30:
            target_total = actual_demand * random.uniform(0.6, 0.85)  # understocked
        else:
            target_total = actual_demand * random.uniform(0.9, 1.1)   # roughly matched

        is_perishable = prod['shelf_life_days'] <= 10
        restock_gap = random.randint(2, 3) if is_perishable else random.randint(10, 18)
        num_restocks = max(1, int(90 / restock_gap))
        qty_per_restock = max(5, int(target_total / num_restocks))

        d = START_DATE
        for _ in range(num_restocks):
            if d > END_DATE:
                break
            noise = random.uniform(0.85, 1.15)
            qty = max(1, int(qty_per_restock * noise))
            stock_rows.append((stock_id, store['store_id'], prod['product_id'], d, qty, f"B{stock_id}"))
            stock_id += 1
            d += timedelta(days=restock_gap)

inventory_stock = pd.DataFrame(stock_rows, columns=[
    'stock_id', 'store_id', 'product_id', 'stock_in_date', 'quantity', 'batch_id'
])
inventory_stock.to_csv('../data/inventory_stock.csv', index=False)
print(f"  Inventory rows: {len(inventory_stock)}")