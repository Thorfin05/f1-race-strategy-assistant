import sqlite3

conn = sqlite3.connect("data/f1_history.db")

rows = conn.execute("""
    SELECT driverId, givenName, familyName
    FROM drivers
    WHERE givenName LIKE '%Sergio%'
       OR familyName LIKE '%Perez%'
       OR familyName LIKE '%Pérez%'
""").fetchall()

for row in rows:
    print(row)

conn.close()