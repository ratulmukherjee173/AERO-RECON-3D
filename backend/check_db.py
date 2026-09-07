import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "data" / "db" / "aerorecon.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
users = cur.execute('SELECT id, email FROM users').fetchall()
print(f"Stored users:")
for u in users:
    print(f"ID: {u[0]}, Email: '{u[1]}'")
conn.close()
