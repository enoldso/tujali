import psycopg2
from app import app

def check_prescriptions():
    try:
        # Get database connection parameters from app config
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Parse the database URL
        # Format: postgresql://username:password@host:port/database
        parts = db_url.replace('postgresql://', '').split('@')
        user_pass, host_db = parts[0], parts[1]
        user, password = user_pass.split(':')
        host_port, database = host_db.split('/')
        
        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host = host_port
            port = '5432'  # Default PostgreSQL port
        
        print(f"Connecting to database: {database} on {host}:{port} as user {user}")
        
        # Connect to the database
        conn = psycopg2.connect(
            dbname=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        
        # Create a cursor
        cur = conn.cursor()
        
        # Check if prescriptions table exists and has data
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'prescriptions'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("ERROR: The 'prescriptions' table does not exist in the database!")
            return
            
        print("The 'prescriptions' table exists in the database.")
        
        # Count prescriptions
        cur.execute("SELECT COUNT(*) FROM prescriptions;")
        count = cur.fetchone()[0]
        print(f"Total prescriptions in database: {count}")
        
        if count > 0:
            # Get sample data
            cur.execute("SELECT * FROM prescriptions LIMIT 5;")
            print("\nSample prescription data:")
            for row in cur.fetchall():
                print(row)
        
        # Check for any foreign key constraints that might prevent inserts
        cur.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
            WHERE 
                tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'prescriptions';
        """)
        
        print("\nForeign key constraints for prescriptions table:")
        for row in cur.fetchall():
            print(f"- {row[1]} references {row[2]}({row[3]})")
        
        # Check for any triggers that might interfere with inserts
        cur.execute("""
            SELECT trigger_name, event_manipulation, event_object_table, action_statement
            FROM information_schema.triggers
            WHERE event_object_table = 'prescriptions';
        """)
        
        triggers = cur.fetchall()
        if triggers:
            print("\nTriggers on prescriptions table:")
            for trigger in triggers:
                print(f"- {trigger[0]}: {trigger[1]} -> {trigger[3][:100]}...")
        else:
            print("\nNo triggers found on prescriptions table.")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    with app.app_context():
        check_prescriptions()
