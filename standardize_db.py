from core.db import engine
from sqlalchemy import text

def fix_enum(conn, type_name, mapping):
    print(f"Fixing {type_name}...")
    for old_val, new_val in mapping.items():
        try:
            # PostgreSQL doesn't allow RENAME VALUE if the value doesn't exist, 
            # so we use a DO block to handle exceptions.
            conn.execute(text(f"""
                DO $$ BEGIN
                    ALTER TYPE {type_name} RENAME VALUE '{old_val}' TO '{new_val}';
                EXCEPTION WHEN invalid_parameter_value THEN 
                    RAISE NOTICE 'Value {old_val} not found in {type_name}, skipping.';
                END $$;
            """))
            print(f"  - Renamed {old_val} -> {new_val}")
        except Exception as e:
            print(f"  - Could not rename {old_val}: {e}")
    conn.commit()

with engine.connect() as conn:
    # 1. Fix userrole (Currently UPPERCASE in DB)
    fix_enum(conn, 'userrole', {
        'USER': 'user',
        'TECHNICAL': 'technical',
        'ADMIN': 'admin'
    })

    # 2. Fix authprovider (Currently UPPERCASE in DB)
    fix_enum(conn, 'authprovider', {
        'LOCAL': 'local',
        'GOOGLE': 'google',
        'TELEGRAM': 'telegram'
    })

    # 3. Ensure requeststatus (Already lowercase, but let's be sure)
    fix_enum(conn, 'requeststatus', {
        'PENDING': 'pending',
        'APPROVED': 'approved',
        'REJECTED': 'rejected'
    })

    # 4. Ensure shopstatus
    fix_enum(conn, 'shopstatus', {
        'ACTIVE': 'active',
        'INACTIVE': 'inactive',
        'PENDING': 'pending'
    })

    # 5. Ensure partcondition
    fix_enum(conn, 'partcondition', {
        'NEW': 'new',
        'USED': 'used',
        'REFURBISHED': 'refurbished'
    })

print("\n✅ Database enums standardized to lowercase!")
