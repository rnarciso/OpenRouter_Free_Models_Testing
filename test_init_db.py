import database
import sys

try:
    print("Attempting to initialize database...")
    database.init_db()
    print("database.init_db() executed.")
except Exception as e:
    print(f"Error during database.init_db(): {e}", file=sys.stderr)
    sys.exit(1)
