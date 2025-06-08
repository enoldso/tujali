from app import app, db_ext
from sqlalchemy import inspect

def list_tables():
    with app.app_context():
        inspector = inspect(db_ext.engine)
        tables = inspector.get_table_names()
        print("\nTables in the database:")
        for table in tables:
            print(f"\nTable: {table}")
            # Get columns
            columns = inspector.get_columns(table)
            print("Columns:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
            
            # Get primary key
            pk = inspector.get_pk_constraint(table)
            if pk and 'constrained_columns' in pk:
                print(f"  Primary Key: {', '.join(pk['constrained_columns'])}")
            
            # Get foreign keys
            fks = inspector.get_foreign_keys(table)
            if fks:
                print("  Foreign Keys:")
                for fk in fks:
                    print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}({fk['referred_columns']})")

if __name__ == '__main__':
    list_tables()
