from app import app, db_ext
from sqlalchemy import inspect

def check_database_structure():
    with app.app_context():
        # Get the database engine
        engine = db_ext.engine
        
        # Create an inspector
        inspector = inspect(engine)
        
        # Get table names
        tables = inspector.get_table_names()
        print("\nTables in the database:")
        for table in tables:
            print(f"\nTable: {table}")
            columns = inspector.get_columns(table)
            print("Columns:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
            
            # Print primary keys
            pk_constraint = inspector.get_pk_constraint(table)
            if pk_constraint and 'constrained_columns' in pk_constraint:
                print(f"  Primary Key: {', '.join(pk_constraint['constrained_columns'])}")
            
            # Print foreign keys
            fk_constraints = inspector.get_foreign_keys(table)
            if fk_constraints:
                print("  Foreign Keys:")
                for fk in fk_constraints:
                    print(f"    - {fk['constrained_columns']} references {fk['referred_table']}({fk['referred_columns']})")

if __name__ == '__main__':
    print("Checking database structure...")
    check_database_structure()
