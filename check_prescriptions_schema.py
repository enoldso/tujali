from app import app, db_ext
from sqlalchemy import text

def check_schema():
    with app.app_context():
        try:
            # Check if the prescriptions table exists
            result = db_ext.session.execute(
                text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'prescriptions'
                ORDER BY ordinal_position;
                """)
            )
            
            columns = result.fetchall()
            
            if not columns:
                print("The 'prescriptions' table does not exist in the database.")
                return
                
            print("\nPrescriptions table structure:")
            print("-" * 50)
            for col in columns:
                print(f"{col.column_name}: {col.data_type} (Nullable: {col.is_nullable})")
            print("-" * 50)
            
            # Check for any constraints
            result = db_ext.session.execute(
                text("""
                SELECT tc.constraint_name, tc.constraint_type, 
                       kcu.column_name, ccu.table_name AS foreign_table_name,
                       ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc 
                LEFT JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                LEFT JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_name = 'prescriptions';
                """)
            )
            
            constraints = result.fetchall()
            if constraints:
                print("\nTable constraints:")
                for c in constraints:
                    if c.constraint_type == 'FOREIGN KEY':
                        print(f"- {c.constraint_type}: {c.column_name} -> {c.foreign_table_name}({c.foreign_column_name})")
                    else:
                        print(f"- {c.constraint_type} on {c.column_name}")
            
        except Exception as e:
            print(f"Error checking schema: {e}")
        finally:
            db_ext.session.rollback()

if __name__ == '__main__':
    check_schema()
