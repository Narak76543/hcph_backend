from core.db import engine
from sqlalchemy import text

enums_to_check = ['requeststatus', 'shopstatus', 'partcondition', 'userrole', 'authprovider']

with engine.connect() as conn:
    for enum_name in enums_to_check:
        print(f"\nValues for {enum_name}:")
        try:
            res = conn.execute(text(f"""
                SELECT enumlabel 
                FROM pg_enum 
                JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
                WHERE pg_type.typname = '{enum_name}';
            """)).fetchall()
            if not res:
                print("  (No values found or enum doesn't exist)")
            for row in res:
                print(f"  - {row[0]}")
        except Exception as e:
            print(f"  Error: {e}")
