import pathlib

import duckdb


ROOT = pathlib.Path(__file__).parent.parent
seed_sql = (ROOT / "fixtures" / "seed.sql").read_text()
db_path = ROOT / "fixtures" / "warehouse.db"

con = duckdb.connect(str(db_path))

for stmt in seed_sql.split(";"):
    stmt = stmt.strip()
    if stmt:
        con.execute(stmt)

enterprise_count = con.execute(
    """
    SELECT COUNT(*) FROM accounts
    WHERE segment IN ('ENT','ENTERPRISE') AND is_test = false
    """
).fetchone()[0]
print(
    "Enterprise non-test account count:",
    enterprise_count,
)

revenue_sum = con.execute(
    """
    SELECT SUM(net_revenue) FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    WHERE a.segment IN ('ENT','ENTERPRISE')
      AND a.is_test = false
      AND t.recognized_at >= '2024-02-01'
      AND t.recognized_at < '2024-05-01'
      AND t.status = 'recognized'
    """
).fetchone()[0]
print("Fiscal Q1 enterprise recognized net revenue:", revenue_sum)

subscription_count = con.execute(
    "SELECT COUNT(*) FROM subscriptions"
).fetchone()[0]
print("Subscription count:", subscription_count)

con.close()
print(f"Built {db_path}")
