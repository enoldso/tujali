import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def check_symptoms():
    # Load environment variables
    load_dotenv('env_config.txt')
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("Error: DATABASE_URL not found in environment variables")
        return
    
    try:
        # Create engine and connect
        engine = create_engine(db_url)
        connection = engine.connect()
        
        # Check user_interactions table
        print("\nChecking user_interactions table...")
        result = connection.execute(text("""
            SELECT interaction_type, COUNT(*) as count 
            FROM user_interactions 
            WHERE interaction_type = 'symptom_report' 
            GROUP BY interaction_type
        """))
        
        symptom_count = 0
        for row in result:
            print(f"Found {row.count} {row.interaction_type} records")
            if row.interaction_type == 'symptom_report':
                symptom_count = row.count
        
        if symptom_count == 0:
            print("\nNo symptom reports found in the database.")
            print("\nTo test the display, let's add a test symptom report...")
            
            # Get a patient ID
            patient_result = connection.execute(text("SELECT id FROM patients LIMIT 1"))
            patient = patient_result.fetchone()
            
            if patient:
                patient_id = patient[0]
                print(f"Found patient with ID: {patient_id}")
                
                        # Check if interaction_metadata column exists, if not add it
                try:
                    connection.execute(text("""
                        ALTER TABLE user_interactions 
                        ADD COLUMN IF NOT EXISTS interaction_metadata JSONB
                    """))
                    connection.commit()
                    print("Added interaction_metadata column to user_interactions table")
                except Exception as e:
                    print(f"Error adding column: {e}")
                
                # Insert a test symptom report
                try:
                    connection.execute(text("""
                        INSERT INTO user_interactions 
                        (patient_id, interaction_type, description, interaction_metadata, created_at)
                        VALUES 
                        (:patient_id, 'symptom_report', 'Test symptom description', 
                         '{"severity": "medium", "duration": "3 days"}'::jsonb, NOW())
                        RETURNING id
                    """), {"patient_id": patient_id})
                    
                    connection.commit()
                    print("Added test symptom report for patient", patient_id)
                except Exception as e:
                    print(f"Error inserting test data: {e}")
                    connection.rollback()
            else:
                print("No patients found in the database. Please add a patient first.")
        
        # Check the structure of the user_interactions table
        print("\nChecking user_interactions table structure...")
        columns = connection.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_interactions'
        """))
        
        print("\nuser_interactions table columns:")
        for col in columns:
            print(f"- {col.column_name}: {col.data_type}")
        
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_symptoms()
