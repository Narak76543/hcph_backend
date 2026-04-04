from core.db import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        print("Adding columns to TBL_SHOPS...")
        conn.execute(text('ALTER TABLE "TBL_SHOPS" ADD COLUMN IF NOT EXISTS province VARCHAR(100);'))
        conn.execute(text('ALTER TABLE "TBL_SHOPS" ADD COLUMN IF NOT EXISTS district VARCHAR(100);'))
        conn.execute(text('ALTER TABLE "TBL_SHOPS" ADD COLUMN IF NOT EXISTS detail VARCHAR(255);'))
        conn.execute(text('ALTER TABLE "TBL_SHOPS" ADD COLUMN IF NOT EXISTS google_maps_url TEXT;'))
        
        # Make address nullable if it was NOT NULL
        conn.execute(text('ALTER TABLE "TBL_SHOPS" ALTER COLUMN address DROP NOT NULL;'))
        
        print("Adding column to TBL_PART_CATEGORIES...")
        conn.execute(text('ALTER TABLE "TBL_PART_CATEGORIES" ADD COLUMN IF NOT EXISTS part_category_img_url TEXT;'))
        
        print("Adding created_by to TBL_LAPTOP_MODELS...")
        conn.execute(text('ALTER TABLE "TBL_LAPTOP_MODELS" ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES "TBL_USERS" (id);'))

        conn.commit()
    print("Columns added successfully!")
except Exception as e:
    print(f"Error: {e}")
