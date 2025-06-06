from app import app, db_ext
from models_sqlalchemy import Prescription, Provider, Patient
from sqlalchemy import inspect

def check_prescriptions():
    with app.app_context():
        # Check if the prescriptions table exists
        print("Checking if prescriptions table exists...")
        inspector = inspect(db_ext.engine)
        if 'prescriptions' not in inspector.get_table_names():
            print("ERROR: prescriptions table does not exist in the database!")
            return
        
        print("Tables in database:", inspector.get_table_names())
        
        # Get all providers
        providers = Provider.query.all()
        print(f"Found {len(providers)} providers")
        
        if not providers:
            print("No providers found in the database!")
            return
            
        # Check prescriptions for each provider
        for provider in providers:
            print(f"\nChecking provider ID: {provider.id}, User ID: {provider.user_id}")
            
            # Get all prescriptions for this provider
            prescriptions = Prescription.query.filter_by(provider_id=provider.id).all()
            print(f"Found {len(prescriptions)} prescriptions for this provider")
            
            for i, rx in enumerate(prescriptions, 1):
                print(f"\nPrescription {i}:")
                print(f"  ID: {rx.id}")
                print(f"  Patient ID: {rx.patient_id}")
                print(f"  Created At: {rx.created_at}")
                print(f"  Status: {getattr(rx, 'status', 'N/A')}")
                print(f"  Medications: {getattr(rx, 'medication_details', 'N/A')}")
                
        # Also check all prescriptions regardless of provider
        all_prescriptions = Prescription.query.all()
        print(f"\nTotal prescriptions in database: {len(all_prescriptions)}")
        if all_prescriptions:
            print("Sample prescription:", all_prescriptions[0].__dict__)

if __name__ == '__main__':
    check_prescriptions()
