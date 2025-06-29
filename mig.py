import sqlite3

# Connect to your database
conn = sqlite3.connect("reselling.db")
cursor = conn.cursor()

# Run the ALTER TABLE command
try:
    cursor.execute("ALTER TABLE gadgets ADD COLUMN seller_price REAL;")
    conn.commit()
    print("✅ Column 'status' added successfully.")
except Exception as e:
    print("❌ Error:", e)

# Close the connection
conn.close()
