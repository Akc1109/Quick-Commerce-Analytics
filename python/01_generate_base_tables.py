import pandas as pd
import numpy as np
from faker import Faker
import random

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ---------- CUSTOMERS ----------
CITIES = ['Bengaluru', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad']
NUM_CUSTOMERS = 30000

customers = pd.DataFrame({
    'customer_id': range(1, NUM_CUSTOMERS + 1),
    'city': [random.choice(CITIES) for _ in range(NUM_CUSTOMERS)]
})

# ---------- DARK STORES ----------
ZONES_PER_CITY = {
    'Bengaluru': ['Koramangala', 'Indiranagar', 'Whitefield', 'HSR Layout'],
    'Mumbai': ['Andheri', 'Bandra', 'Powai', 'Dadar'],
    'Delhi': ['Saket', 'Dwarka', 'Rohini', 'Karol Bagh'],
    'Pune': ['Kothrud', 'Viman Nagar', 'Hinjewadi'],
    'Hyderabad': ['Gachibowli', 'Madhapur', 'Banjara Hills']
}

store_rows = []
store_id = 1
for city, zones in ZONES_PER_CITY.items():
    for zone in zones:
        store_rows.append({
            'store_id': store_id,
            'city': city,
            'zone': zone,
            'capacity': random.randint(800, 2500),
            'opening_date': fake.date_between(start_date='-2y', end_date='-3M')
        })
        store_id += 1

dark_stores = pd.DataFrame(store_rows)

# ---------- PRODUCTS ----------
CATEGORIES = {
    'Dairy': (2, 7),
    'Fruits & Vegetables': (1, 5),
    'Bakery': (2, 4),
    'Snacks': (180, 365),
    'Beverages': (180, 365),
    'Personal Care': (365, 730),
    'Household': (365, 730),
    'Frozen Foods': (60, 180)
}

PRODUCT_NAMES = {
    'Dairy': ['Milk 1L', 'Curd 400g', 'Paneer 200g', 'Butter 100g', 'Cheese Slices'],
    'Fruits & Vegetables': ['Bananas 1kg', 'Tomatoes 1kg', 'Onions 1kg', 'Apples 1kg', 'Spinach 250g'],
    'Bakery': ['Bread Loaf', 'Croissant', 'Bun Pack', 'Cake Slice'],
    'Snacks': ['Chips 100g', 'Biscuits Pack', 'Namkeen 200g', 'Chocolate Bar'],
    'Beverages': ['Cola 750ml', 'Juice 1L', 'Energy Drink', 'Mineral Water 1L'],
    'Personal Care': ['Shampoo 200ml', 'Soap Bar', 'Toothpaste', 'Face Wash'],
    'Household': ['Detergent 1kg', 'Dish Soap', 'Floor Cleaner', 'Tissue Pack'],
    'Frozen Foods': ['Frozen Peas', 'Ice Cream Tub', 'Frozen Paratha', 'Frozen Nuggets']
}

product_rows = []
product_id = 1
for category, (min_shelf, max_shelf) in CATEGORIES.items():
    for name in PRODUCT_NAMES[category]:
        unit_cost = round(random.uniform(15, 200), 2)
        markup = random.uniform(1.2, 1.6)
        product_rows.append({
            'product_id': product_id,
            'product_name': name,
            'category': category,
            'shelf_life_days': random.randint(min_shelf, max_shelf),
            'unit_cost': unit_cost,
            'price': round(unit_cost * markup, 2)
        })
        product_id += 1

products = pd.DataFrame(product_rows)

# ---------- RIDERS ----------
rider_rows = []
rider_id = 1
for _, store in dark_stores.iterrows():
    num_riders = random.randint(4, 10)
    for _ in range(num_riders):
        rider_rows.append({
            'rider_id': rider_id,
            'store_id': store['store_id'],
            'join_date': fake.date_between(start_date=store['opening_date'], end_date='today')
        })
        rider_id += 1

riders = pd.DataFrame(rider_rows)

# ---------- SAVE TO CSV ----------
customers.to_csv('../data/customers.csv', index=False)
dark_stores.to_csv('../data/dark_stores.csv', index=False)
products.to_csv('../data/products.csv', index=False)
riders.to_csv('../data/riders.csv', index=False)

print("Base tables generated:")
print(f"Customers: {len(customers)}")
print(f"Dark Stores: {len(dark_stores)}")
print(f"Products: {len(products)}")
print(f"Riders: {len(riders)}")