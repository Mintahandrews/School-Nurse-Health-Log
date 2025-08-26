import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app
from app.models.db import get_db_connection

def run_migration():
    app = create_app()
    
    with app.app_context():
        # Read the migration SQL file
        migration_file = os.path.join(os.path.dirname(__file__), 'update_schema.sql')
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration
        conn = get_db_connection()
        try:
            # Split the SQL into individual statements and execute them
            statements = migration_sql.split(';')
            for statement in statements:
                if statement.strip():
                    conn.cursor().execute(statement)
            conn.commit()
            print("Database migration completed successfully!")
        except Exception as e:
            conn.rollback()
            print(f"Error during migration: {str(e)}")
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    run_migration()
