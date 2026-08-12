CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    city VARCHAR(50)
);

CREATE TABLE dark_stores (
    store_id SERIAL PRIMARY KEY,
    city VARCHAR(50),
    zone VARCHAR(50),
    capacity INT,
    opening_date DATE
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    shelf_life_days INT,      -- high number (e.g. 9999) for non-perishables
    unit_cost NUMERIC(10,2),
    price NUMERIC(10,2)
);

CREATE TABLE riders (
    rider_id SERIAL PRIMARY KEY,
    store_id INT REFERENCES dark_stores(store_id),
    join_date DATE
);

CREATE TABLE inventory_stock (
    stock_id SERIAL PRIMARY KEY,
    store_id INT REFERENCES dark_stores(store_id),
    product_id INT REFERENCES products(product_id),
    stock_in_date DATE,
    quantity INT,
    batch_id VARCHAR(20)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    store_id INT REFERENCES dark_stores(store_id),
    rider_id INT REFERENCES riders(rider_id),
    order_time TIMESTAMP,
    promised_delivery_time TIMESTAMP,
    actual_delivery_time TIMESTAMP,
    order_value NUMERIC(10,2)
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT,
    price_at_order NUMERIC(10,2)
);

CREATE TABLE weather_traffic_flags (
    flag_id SERIAL PRIMARY KEY,
    date DATE,
    zone VARCHAR(50),
    hour INT CHECK (hour BETWEEN 0 AND 23),
    traffic_level VARCHAR(10) CHECK (traffic_level IN ('low','medium','high')),
    weather VARCHAR(20)
);