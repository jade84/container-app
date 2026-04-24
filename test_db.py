import mysql.connector

conn = mysql.connector.connect(
    host="localhost",   # 👈 hardcode test
    user="root",
    password="123456",
    database="container_db",
    port=3306
)

print("✅ CONNECT OK")