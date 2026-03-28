from core.db import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE "TBL_LAPTOP_BRANDS" ADD COLUMN brand_img_url TEXT;'))
        conn.commit()
    print("Column added successfully!")
except Exception as e:
    print(f"Error: {e}")
