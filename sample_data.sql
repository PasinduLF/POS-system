-- A default admin is created by the app if not present; this is a placeholder
INSERT OR IGNORE INTO users (username, password_hash, role)
VALUES ('admin', 'PLACEHOLDER_HASH_WILL_BE_SET_BY_APP', 'admin');

INSERT OR IGNORE INTO categories (name) VALUES
 ('Cosmetics'),
 ('Jewelry'),
 ('Accessories');

INSERT OR IGNORE INTO brands (name) VALUES
 ('GlamCo'),
 ('Roselle'),
 ('GoldTouch'),
 ('CarryMe');

INSERT OR IGNORE INTO products (name, brand, brand_id, category_id, description, price, cost_price, stock_quantity, barcode, low_stock_threshold)
SELECT 'Lipstick Classic', 'GlamCo', b.id, c.id, 'Matte finish', 1200.00, 700.00, 50, '8901234567890', 5
FROM categories c, brands b WHERE c.name = 'Cosmetics' AND b.name='GlamCo';

INSERT OR IGNORE INTO products (name, brand, brand_id, category_id, description, price, cost_price, stock_quantity, barcode, low_stock_threshold)
SELECT 'Perfume Rose 50ml', 'Roselle', b.id, c.id, 'Floral scent', 4800.00, 3200.00, 20, '8901234567891', 3
FROM categories c, brands b WHERE c.name = 'Cosmetics' AND b.name='Roselle';

INSERT OR IGNORE INTO products (name, brand, brand_id, category_id, description, price, cost_price, stock_quantity, barcode, low_stock_threshold)
SELECT 'Imitation Necklace Set', 'GoldTouch', b.id, c.id, 'Gold tone', 3500.00, 2000.00, 10, '8901234567892', 2
FROM categories c, brands b WHERE c.name = 'Jewelry' AND b.name='GoldTouch';

INSERT OR IGNORE INTO products (name, brand, brand_id, category_id, description, price, cost_price, stock_quantity, barcode, low_stock_threshold)
SELECT 'Makeup Pouch', 'CarryMe', b.id, c.id, 'Small zip pouch', 900.00, 500.00, 30, '8901234567893', 5
FROM categories c, brands b WHERE c.name = 'Accessories' AND b.name='CarryMe';

