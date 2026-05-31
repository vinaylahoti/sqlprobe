DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    segment VARCHAR,
    is_test BOOLEAN,
    tier VARCHAR
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER,
    amount DECIMAL(12,2),
    net_revenue DECIMAL(12,2),
    recognized_at DATE,
    created_at DATE,
    status VARCHAR
);

CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER,
    status VARCHAR,
    started_at DATE,
    cancelled_at DATE,
    plan VARCHAR,
    mrr DECIMAL(10,2)
);

INSERT INTO accounts (id, name, segment, is_test, tier) VALUES
    (1, 'Acme Enterprise', 'ENT', false, 'platinum'),
    (2, 'Globex Corp', 'ENTERPRISE', false, 'gold'),
    (3, 'Initech', 'ENT', false, 'gold'),
    (4, 'Umbrella Analytics', 'ENTERPRISE', false, 'platinum'),
    (5, 'Hooli Data', 'ENT', false, 'silver'),
    (6, 'Northwind SMB', 'SMB', false, 'standard'),
    (7, 'Bluebird Bakery', 'SMB', false, 'starter'),
    (8, 'Demo Enterprise', 'ENTERPRISE', true, 'demo'),
    (9, 'Internal Test Account', 'SMB', true, 'demo');

INSERT INTO transactions (
    id,
    account_id,
    amount,
    net_revenue,
    recognized_at,
    created_at,
    status
) VALUES
    (1, 1, 920000.00, 800000.00, '2024-02-05', '2024-02-01', 'recognized'),
    (2, 2, 880000.00, 750000.00, '2024-02-20', '2024-02-15', 'recognized'),
    (3, 3, 760000.00, 650000.00, '2024-03-12', '2024-03-10', 'recognized'),
    (4, 4, 700000.00, 600000.00, '2024-04-04', '2024-04-01', 'recognized'),
    (5, 5, 590000.00, 500000.00, '2024-04-25', '2024-04-20', 'recognized'),
    (6, 1, 300000.00, 250000.00, '2024-01-15', '2024-01-10', 'recognized'),
    (7, 2, 450000.00, 400000.00, '2024-05-03', '2024-05-01', 'recognized'),
    (8, 3, 200000.00, 180000.00, '2024-03-20', '2024-03-18', 'pending'),
    (9, 4, 150000.00, 120000.00, '2024-04-10', '2024-04-08', 'refunded'),
    (10, 6, 90000.00, 75000.00, '2024-03-08', '2024-03-05', 'recognized'),
    (11, 7, 65000.00, 52000.00, '2024-04-12', '2024-04-10', 'recognized'),
    (12, 8, 9999999.00, 9999999.00, '2024-03-15', '2024-03-12', 'recognized'),
    (13, 9, 500000.00, 450000.00, '2024-02-18', '2024-02-17', 'recognized');

INSERT INTO subscriptions (
    id,
    account_id,
    status,
    started_at,
    cancelled_at,
    plan,
    mrr
) VALUES
    (1, 1, 'active', '2023-06-01', NULL, 'enterprise', 2000.00),
    (2, 2, 'cancelled', '2023-03-15', '2024-03-31', 'enterprise', 1800.00),
    (3, 3, 'active', '2024-01-10', NULL, 'growth', 950.00),
    (4, 4, 'cancelled', '2023-11-01', '2024-04-15', 'enterprise', 1500.00),
    (5, 5, 'active', '2024-02-01', NULL, 'growth', 700.00),
    (6, 6, 'cancelled', '2023-09-01', '2024-02-28', 'starter', 50.00),
    (7, 7, 'active', '2024-03-05', NULL, 'starter', 75.00),
    (8, 8, 'active', '2024-01-01', NULL, 'demo', 100.00),
    (9, 9, 'cancelled', '2023-12-01', '2024-04-01', 'demo', 125.00);
