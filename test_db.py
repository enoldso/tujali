import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def test_database_connection():
    # Load environment variables from env_config.txt file
    load_dotenv('env_config.txt')
    
    # Get database URL from environment variables
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print(" Error: DATABASE_URL not found in .env file")
        return
    
    print(f" Attempting to connect to: {db_url.split('@')[-1]}")
    
    try:
        # Create engine and connect
        engine = create_engine(db_url)
        connection = engine.connect()
        
        # Test the connection with a simple query
        result = connection.execute(text("SELECT version();"))
        db_version = result.scalar()
        
        print(" Successfully connected to PostgreSQL!")
        print(f" Database version: {db_version}")
        
        # Test if we can access the tables
        try:
            connection.execute(text("SELECT 1 FROM pg_tables WHERE schemaname = 'public'"))
            print(" Successfully queried the database schema")
        except Exception as e:
            print(f" Could not query tables: {e}")
        
        connection.close()
        
    except Exception as e:
        print(f" Failed to connect to the database: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL is running")
        print("2. Verify the database 'tujali_telehealth' exists")
        print("3. Check if the user 'tujali_user' has the correct permissions")
        print("4. Verify the password in the .env file matches the PostgreSQL user password")
        print("5. Ensure PostgreSQL is listening on port 5432")

if __name__ == "__main__":
    test_database_connection()