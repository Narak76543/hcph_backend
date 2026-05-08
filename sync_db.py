"""
sync_db.py  —  Run this whenever you add/change models or enums.

What it does:
  1. Reads all Python enum definitions from your models.
  2. Compares them against what's currently in PostgreSQL.
  3. Renames any mismatched enum values (case or name changes).
  4. Adds any missing enum values.
  5. Adds any missing columns to existing tables (safe ALTER TABLE).
  6. Creates any brand-new tables that don't exist yet.

Usage:
  .\\venv\\Scripts\\python.exe sync_db.py
"""

import sys
from sqlalchemy import text, inspect
from core.db import engine

# ── Colour helpers (Windows-safe fallback) ──────────────────────────────────
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    GREEN  = Fore.GREEN
    RED    = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN   = Fore.CYAN
    RESET  = Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = CYAN = RESET = ""


def ok(msg):   print(f"{GREEN}  [OK]{RESET}  {msg}")
def warn(msg): print(f"{YELLOW}  [!!]{RESET}  {msg}")
def err(msg):  print(f"{RED}  [ERR]{RESET} {msg}")
def info(msg): print(f"{CYAN}  [>>]{RESET}  {msg}")


# ── 1. Sync enums ────────────────────────────────────────────────────────────

# Define the DESIRED state: { pg_type_name: [ordered values] }
DESIRED_ENUMS = {
    "userrole":      ["user", "technical", "admin"],
    "authprovider":  ["local", "telegram", "google"],
    "requeststatus": ["pending", "approved", "rejected"],
    "shopstatus":    ["pending", "active", "inactive"],
    "partcondition": ["new", "used", "refurbished"],
}


def get_db_enum_values(conn, type_name):
    rows = conn.execute(text("""
        SELECT enumlabel
        FROM pg_enum
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
        WHERE pg_type.typname = :name
        ORDER BY pg_enum.enumsortorder;
    """), {"name": type_name}).fetchall()
    return [r[0] for r in rows]


def sync_enums(conn):
    print("\n--- Syncing Enums ---")
    for type_name, desired_values in DESIRED_ENUMS.items():
        current_values = get_db_enum_values(conn, type_name)

        if not current_values:
            warn(f"Enum '{type_name}' not found in DB — will be created with tables.")
            continue

        # Rename values that exist in DB but with wrong casing
        # (only when the desired value is completely absent from DB)
        for i, desired in enumerate(desired_values):
            if desired not in current_values:
                # Find a likely candidate to rename (same position or similar name)
                if i < len(current_values):
                    current = current_values[i]
                    if current not in desired_values:  # only rename if it's not a valid desired value
                        try:
                            conn.execute(text(f"""
                                DO $$ BEGIN
                                    ALTER TYPE {type_name} RENAME VALUE '{current}' TO '{desired}';
                                EXCEPTION WHEN invalid_parameter_value THEN NULL;
                                END $$;
                            """))
                            conn.commit()
                            ok(f"{type_name}: '{current}' -> '{desired}'")
                        except Exception as e:
                            err(f"{type_name}: rename '{current}' -> '{desired}' failed: {e}")
                            conn.rollback()
                    else:
                        ok(f"{type_name}: '{current}' is correct (order differs but value exists)")

        # Add any new values that don't exist yet
        refreshed = get_db_enum_values(conn, type_name)
        for desired in desired_values:
            if desired not in refreshed:
                try:
                    conn.execute(text(f"ALTER TYPE {type_name} ADD VALUE IF NOT EXISTS '{desired}';"))
                    conn.commit()
                    ok(f"{type_name}: added new value '{desired}'")
                except Exception as e:
                    err(f"{type_name}: add value '{desired}' failed: {e}")
                    conn.rollback()


# ── 2. Sync tables & columns ─────────────────────────────────────────────────

def sync_tables():
    print("\n--- Syncing Tables & Columns ---")

    # Import ALL models so SQLAlchemy's metadata is fully populated
    import api.users.models          # noqa
    import api.role_request.models   # noqa
    import api.shops.models          # noqa
    import api.shop_listing.models   # noqa
    import api.part.models           # noqa

    # Try optional model modules gracefully
    optional_modules = [
        "api.part_specs.models",
        "api.laptop_models.models",
    ]
    for mod in optional_modules:
        try:
            __import__(mod)
        except Exception:
            pass

    from core.db import Base
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            # Create the whole table
            try:
                table.create(engine)
                ok(f"Created new table '{table_name}'")
            except Exception as e:
                err(f"Could not create table '{table_name}': {e}")
        else:
            # Table exists — check for missing columns
            existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
            for col in table.columns:
                if col.name not in existing_cols:
                    col_type = col.type.compile(dialect=engine.dialect)
                    nullable  = "" if col.nullable else " NOT NULL"
                    default   = ""
                    if col.server_default is not None:
                        default = f" DEFAULT {col.server_default.arg}"
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(
                                f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {col_type}{nullable}{default};'
                            ))
                            conn.commit()
                        ok(f"'{table_name}': added column '{col.name}' ({col_type})")
                    except Exception as e:
                        err(f"'{table_name}': add column '{col.name}' failed: {e}")
                else:
                    ok(f"'{table_name}'.'{col.name}' exists")


# ── 3. Verify final state ────────────────────────────────────────────────────

def verify(conn):
    print("\n--- Final Verification ---")
    all_good = True
    for type_name, desired_values in DESIRED_ENUMS.items():
        current = get_db_enum_values(conn, type_name)
        if not current:
            warn(f"{type_name}: not found (may be in a new table — OK if just created)")
            continue
        for v in desired_values:
            if v not in current:
                err(f"{type_name}: MISSING value '{v}' (db has {current})")
                all_good = False
            else:
                ok(f"{type_name}: '{v}' confirmed")
    return all_good


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  HCPH Backend — Database Sync Script")
    print("=" * 55)

    with engine.connect() as conn:
        sync_enums(conn)

    sync_tables()

    with engine.connect() as conn:
        all_good = verify(conn)

    print("\n" + "=" * 55)
    if all_good:
        print(f"{GREEN}  DATABASE SYNC COMPLETE — All checks passed!{RESET}")
    else:
        print(f"{RED}  SYNC FINISHED WITH WARNINGS — Check errors above.{RESET}")
    print("=" * 55)
    sys.exit(0 if all_good else 1)
