from core.db import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:

        print("Fixing userrole enum casing...")
        conn.execute(text("""
            DO $$ BEGIN
                ALTER TYPE userrole RENAME VALUE 'user'      TO 'USER';
            EXCEPTION WHEN invalid_parameter_value THEN NULL;
            END $$;
        """))
        conn.execute(text("""
            DO $$ BEGIN
                ALTER TYPE userrole RENAME VALUE 'technical' TO 'TECHNICAL';
            EXCEPTION WHEN invalid_parameter_value THEN NULL;
            END $$;
        """))
        conn.execute(text("""
            DO $$ BEGIN
                ALTER TYPE userrole RENAME VALUE 'admin'     TO 'ADMIN';
            EXCEPTION WHEN invalid_parameter_value THEN NULL;
            END $$;
        """))
        conn.commit()
        print("✅ userrole fixed!")

        print("Fixing authprovider enum casing...")
        conn.execute(text("""
            DO $$ BEGIN
                ALTER TYPE authprovider RENAME VALUE 'local'    TO 'LOCAL';
            EXCEPTION WHEN invalid_parameter_value THEN NULL;
            END $$;
        """))
        conn.execute(text("""
            DO $$ BEGIN
                ALTER TYPE authprovider RENAME VALUE 'google'   TO 'GOOGLE';
            EXCEPTION WHEN invalid_parameter_value THEN NULL;
            END $$;
        """))
        conn.execute(text("""
            DO $$ BEGIN
                ALTER TYPE authprovider RENAME VALUE 'telegram' TO 'TELEGRAM';
            EXCEPTION WHEN invalid_parameter_value THEN NULL;
            END $$;
        """))
        conn.commit()
        print("✅ authprovider fixed!")

except Exception as e:
    print(f"❌ Error: {e}")