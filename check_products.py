import sqlite3
from pathlib import Path

db_path = Path("data/app.db")
if not db_path.exists():
    print("❌ Database does not exist at data/app.db")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check if products table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pulgarin_products';")
table = cursor.fetchone()

if not table:
    print("❌ Table pulgarin_products does not exist")
    exit(1)

# Count products
cursor.execute("SELECT COUNT(*) FROM pulgarin_products")
count = cursor.fetchone()[0]
print(f"✅ Found {count} products in database")

if count > 0:
    # Show first 5 products
    cursor.execute("SELECT codigo, descripcion, peso, um FROM pulgarin_products LIMIT 5")
    products = cursor.fetchall()
    print("\nFirst 5 products:")
    for p in products:
        print(f"  - Codigo: {p[0]}, Descripcion: {p[1]}, Peso: {p[2]}, U/M: {p[3]}")

conn.close()
