from app import app, db_ext
from sqlalchemy import inspect

def check_database():
    with app.app_context():
        # Get database URL
        print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Check if we can connect to the database
        try:
            with db_ext.engine.connect() as conn:
                print("Successfully connected to the database")
                
                # Get all tables
                inspector = inspect(db_ext.engine)
                tables = inspector.get_table_names()
                print(f"\nTables in database ({len(tables)}):")
                for table in tables:
                    print(f"- {table}")
                    
                    # If this is the prescriptions table, show its columns
                    if table == 'prescriptions':
                        print("  Columns:")
                        for column in inspector.get_columns(table):
                            print(f"  - {column['name']} ({column['type']})")
                            
        except Exception as e:
            print(f"Error connecting to database: {e}")

if __name__ == '__main__':
    check_database()
