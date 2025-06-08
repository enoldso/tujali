from app import app, db_ext
from sqlalchemy import inspect

def check_users_schema():
    with app.app_context():
        # Get the database engine
        engine = db_ext.engine
        
        # Create an inspector
        inspector = inspect(engine)
        
        # Check if users table exists
        if 'users' not in inspector.get_table_names():
            print("Error: 'users' table does not exist in the database.")
            return
        
        # Get columns for users table
        columns = inspector.get_columns('users')
        print("\nColumns in 'users' table:")
        for column in columns:
            print(f"- {column['name']}: {column['type']} (Nullable: {column['nullable']})")
            if column.get('default'):
                print(f"  Default: {column['default']}")
        
        # Print primary key
        pk_constraint = inspector.get_pk_constraint('users')
        if pk_constraint and 'constrained_columns' in pk_constraint:
            print(f"\nPrimary Key: {', '.join(pk_constraint['constrained_columns'])}")
        
        # Print any constraints
        print("\nConstraints:")
        unique_constraints = inspector.get_unique_constraints('users')
        for uc in unique_constraints:
            print(f"- Unique constraint on columns: {', '.join(uc['column_names'])}")
        
        # Check for any NOT NULL constraints without defaults
        print("\nRequired fields (NOT NULL without default):")
        for column in columns:
            if not column['nullable'] and column.get('default') is None and not column.get('autoincrement', False):
                print(f"- {column['name']}: {column['type']}")

if __name__ == '__main__':
    print("Checking users table schema...")
    check_users_schema()
