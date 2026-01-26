import sqlite3

conn = sqlite3.connect('datanova.db')
cursor = conn.cursor()

print("\nTables dans datanova.db:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for table in cursor.fetchall():
    print(f"  - {table[0]}")

conn.close()
