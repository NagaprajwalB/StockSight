-- Inventory Analytics Dashboard Schema
CREATE DATABASE IF NOT EXISTS inventory_db;
USE inventory_db;

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    contact_email VARCHAR(150),
    contact_phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    category_id INT,
    supplier_id INT,
    description TEXT,
    unit_price DECIMAL(10,2) NOT NULL,
    cost_price DECIMAL(10,2) NOT NULL,
    quantity_in_stock INT DEFAULT 0,
    reorder_level INT DEFAULT 10,
    unit VARCHAR(50) DEFAULT 'piece',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

-- Stock movements / transactions
CREATE TABLE IF NOT EXISTS stock_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    movement_type ENUM('purchase', 'sale', 'adjustment', 'return', 'damage') NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ── Seed Data ──────────────────────────────────────────────────────────────

INSERT IGNORE INTO categories (name, description) VALUES
('Electronics',    'Electronic devices and components'),
('Clothing',       'Apparel and fashion accessories'),
('Food & Beverage','Consumable food and drinks'),
('Office Supplies', 'Stationery and office equipment'),
('Tools & Hardware','Hand tools and hardware supplies');

INSERT IGNORE INTO suppliers (name, contact_email, contact_phone, address) VALUES
('TechCorp India',        'orders@techcorp.in',    '+91-80-12345678', 'Bengaluru, Karnataka'),
('Fashion Hub Ltd',       'supply@fashionhub.in',  '+91-22-87654321', 'Mumbai, Maharashtra'),
('Fresh Farms Co',        'fresh@freshfarms.in',   '+91-40-11223344', 'Hyderabad, Telangana'),
('Office World',          'b2b@officeworld.in',    '+91-11-99887766', 'New Delhi, Delhi'),
('Hardware Solutions Inc','info@hardwaresol.in',   '+91-44-55443322', 'Chennai, Tamil Nadu');

INSERT IGNORE INTO products (name, sku, category_id, supplier_id, unit_price, cost_price, quantity_in_stock, reorder_level, unit) VALUES
('Wireless Bluetooth Headphones', 'ELEC-001', 1, 1, 2999.00, 1800.00, 45,  10, 'piece'),
('USB-C Charging Cable 2m',       'ELEC-002', 1, 1, 399.00,  180.00,  200, 30, 'piece'),
('Mechanical Keyboard',           'ELEC-003', 1, 1, 5499.00, 3200.00, 20,   5, 'piece'),
('Wireless Mouse',                'ELEC-004', 1, 1, 1299.00, 700.00,  60,  15, 'piece'),
('LED Desk Lamp',                 'ELEC-005', 1, 1, 1799.00, 900.00,  8,   10, 'piece'),
('Cotton T-Shirt (Blue, M)',      'CLTH-001', 2, 2, 599.00,  250.00,  120, 20, 'piece'),
('Denim Jeans (32)',              'CLTH-002', 2, 2, 1999.00, 900.00,  75,  15, 'piece'),
('Sports Hoodie',                 'CLTH-003', 2, 2, 1499.00, 700.00,  5,   10, 'piece'),
('Running Shoes (Size 9)',        'CLTH-004', 2, 2, 3499.00, 1800.00, 30,  10, 'piece'),
('Organic Green Tea (250g)',      'FOOD-001', 3, 3, 299.00,  120.00,  300, 50, 'box'),
('Whole Wheat Biscuits',         'FOOD-002', 3, 3, 89.00,   40.00,   500, 100,'pack'),
('Cold Brew Coffee Sachets',      'FOOD-003', 3, 3, 449.00,  200.00,  150, 30, 'pack'),
('A4 Paper Ream (500 sheets)',    'OFFC-001', 4, 4, 349.00,  180.00,  80,  20, 'ream'),
('Ballpoint Pens (Box of 12)',    'OFFC-002', 4, 4, 149.00,   60.00,  200, 40, 'box'),
('Stapler Heavy Duty',           'OFFC-003', 4, 4, 499.00,  220.00,  25,   5, 'piece'),
('Sticky Notes 3x3 (Pack of 5)', 'OFFC-004', 4, 4, 99.00,   40.00,   350, 60, 'pack'),
('Hammer 500g',                  'TOOL-001', 5, 5, 449.00,  200.00,  40,  10, 'piece'),
('Screwdriver Set (12pcs)',       'TOOL-002', 5, 5, 899.00,  400.00,  35,  10, 'set'),
('Measuring Tape 5m',            'TOOL-003', 5, 5, 249.00,  100.00,  60,  15, 'piece'),
('Safety Gloves (Pair)',         'TOOL-004', 5, 5, 199.00,   80.00,  4,   20, 'pair');

-- Stock movements seed (recent 60 days)
INSERT INTO stock_movements (product_id, movement_type, quantity, unit_price, created_at) VALUES
(1,  'purchase', 50,  1800.00, NOW() - INTERVAL 58 DAY),
(1,  'sale',    -12,  2999.00, NOW() - INTERVAL 50 DAY),
(1,  'sale',     -8,  2999.00, NOW() - INTERVAL 35 DAY),
(1,  'sale',     -5,  2999.00, NOW() - INTERVAL 10 DAY),
(2,  'purchase',220,   180.00, NOW() - INTERVAL 55 DAY),
(2,  'sale',    -20,   399.00, NOW() - INTERVAL 45 DAY),
(3,  'purchase', 25,  3200.00, NOW() - INTERVAL 52 DAY),
(3,  'sale',     -5,  5499.00, NOW() - INTERVAL 30 DAY),
(4,  'purchase', 70,   700.00, NOW() - INTERVAL 48 DAY),
(4,  'sale',    -10,  1299.00, NOW() - INTERVAL 25 DAY),
(5,  'purchase', 15,   900.00, NOW() - INTERVAL 40 DAY),
(5,  'sale',     -7,  1799.00, NOW() - INTERVAL 20 DAY),
(6,  'purchase',140,   250.00, NOW() - INTERVAL 57 DAY),
(6,  'sale',    -20,   599.00, NOW() - INTERVAL 40 DAY),
(7,  'purchase', 90,   900.00, NOW() - INTERVAL 53 DAY),
(7,  'sale',    -15,  1999.00, NOW() - INTERVAL 28 DAY),
(8,  'purchase', 18,   700.00, NOW() - INTERVAL 45 DAY),
(8,  'sale',    -13,  1499.00, NOW() - INTERVAL 15 DAY),
(9,  'purchase', 40,  1800.00, NOW() - INTERVAL 42 DAY),
(9,  'sale',    -10,  3499.00, NOW() - INTERVAL 18 DAY),
(10, 'purchase',350,   120.00, NOW() - INTERVAL 60 DAY),
(10, 'sale',    -50,   299.00, NOW() - INTERVAL 30 DAY),
(11, 'purchase',600,    40.00, NOW() - INTERVAL 59 DAY),
(11, 'sale',   -100,    89.00, NOW() - INTERVAL 20 DAY),
(12, 'purchase',180,   200.00, NOW() - INTERVAL 50 DAY),
(12, 'sale',    -30,   449.00, NOW() - INTERVAL 22 DAY),
(13, 'purchase',100,   180.00, NOW() - INTERVAL 55 DAY),
(13, 'sale',    -20,   349.00, NOW() - INTERVAL 35 DAY),
(14, 'purchase',240,    60.00, NOW() - INTERVAL 50 DAY),
(14, 'sale',    -40,   149.00, NOW() - INTERVAL 25 DAY),
(17, 'purchase', 50,   200.00, NOW() - INTERVAL 47 DAY),
(17, 'sale',    -10,   449.00, NOW() - INTERVAL 20 DAY),
(18, 'purchase', 40,   400.00, NOW() - INTERVAL 44 DAY),
(18, 'sale',     -5,   899.00, NOW() - INTERVAL 12 DAY),
(20, 'purchase', 30,    80.00, NOW() - INTERVAL 38 DAY),
(20, 'sale',    -26,   199.00, NOW() - INTERVAL  5 DAY),
(5,  'damage',   -2,     0.00, NOW() - INTERVAL  3 DAY),
(8,  'adjustment',3,    0.00, NOW() - INTERVAL  2 DAY);
