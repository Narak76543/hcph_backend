import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(".env")

try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "tdd"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_SERVER", "localhost"),
        port=os.getenv("DB_PORT", 5432)
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute('ALTER TABLE "TBL_LAPTOP_BRANDS" ADD COLUMN brand_img_url TEXT;')
    print("Column brand_img_url added via psycopg2")
    cursor.close()
    conn.close()
except psycopg2.errors.DuplicateColumn:
    print("Column brand_img_url already exists!")
except Exception as e:
    print(f"Failed: {e}")
