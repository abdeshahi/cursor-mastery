INSERT INTO plans (name, traffic_gb, duration_days, price, currency, is_active, sort_order)
SELECT '۳۰ گیگ / ۳۰ روز', 30, 30, 150000, 'TOMAN', TRUE, 10
WHERE NOT EXISTS (SELECT 1 FROM plans WHERE name = '۳۰ گیگ / ۳۰ روز');

INSERT INTO plans (name, traffic_gb, duration_days, price, currency, is_active, sort_order)
SELECT '۵۰ گیگ / ۳۰ روز', 50, 30, 200000, 'TOMAN', TRUE, 20
WHERE NOT EXISTS (SELECT 1 FROM plans WHERE name = '۵۰ گیگ / ۳۰ روز');

INSERT INTO plans (name, traffic_gb, duration_days, price, currency, is_active, sort_order)
SELECT '۱۰۰ گیگ / ۳۰ روز', 100, 30, 280000, 'TOMAN', TRUE, 30
WHERE NOT EXISTS (SELECT 1 FROM plans WHERE name = '۱۰۰ گیگ / ۳۰ روز');

INSERT INTO plans (name, traffic_gb, duration_days, price, currency, is_active, sort_order)
SELECT '۱۰۰ گیگ / ۹۰ روز', 100, 90, 750000, 'TOMAN', TRUE, 40
WHERE NOT EXISTS (SELECT 1 FROM plans WHERE name = '۱۰۰ گیگ / ۹۰ روز');
