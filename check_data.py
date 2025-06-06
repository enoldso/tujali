from app import app, db_ext
from models_sqlalchemy import Provider, Patient, Prescription, User, Pharmacy

def check_data():
    with app.app_context():
        try:
            print("Checking database contents...")
            
            # Check database URL
            print(f"\nDatabase URL: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
            
            # Check users
            users = User.query.all()
            print(f"\nFound {len(users)} users:")
            for u in users:
                print(f"- ID: {u.id}, Username: {u.username}, Email: {u.email}")
            
            # Check providers
            providers = Provider.query.all()
            print(f"\nFound {len(providers)} providers:")
            for p in providers:
                user = User.query.get(p.user_id)
                print(f"- ID: {p.id}, Name: {p.name}, User ID: {p.user_id}, "
                      f"Username: {user.username if user else 'N/A'}, "
                      f"Specialization: {p.specialization}")
            
            # Check patients
            patients = Patient.query.all()
            print(f"\nFound {len(patients)} patients:")
            for p in patients:
                print(f"- ID: {p.id}, Name: {p.name}, Phone: {p.phone_number}, "
                      f"Location: {p.location}")
            
            # Check pharmacies
            pharmacies = Pharmacy.query.all()
            print(f"\nFound {len(pharmacies)} pharmacies:")
            for p in pharmacies:
                print(f"- ID: {p.id}, Name: {p.name}, Location: {p.city}, {p.state}")
            
            # Check existing prescriptions
            prescriptions = Prescription.query.all()
            print(f"\nFound {len(prescriptions)} prescriptions:")
            for rx in prescriptions:
                patient = Patient.query.get(rx.patient_id)
                provider = Provider.query.get(rx.provider_id)
                print(f"- ID: {rx.id}, Status: {rx.status}")
                print(f"  Provider: {provider.name if provider else 'N/A'} (ID: {rx.provider_id})")
                print(f"  Patient: {patient.name if patient else 'N/A'} (ID: {rx.patient_id})")
                print(f"  Created: {rx.created_at}, Updated: {rx.updated_at}")
                if rx.pharmacy_id:
                    pharmacy = Pharmacy.query.get(rx.pharmacy_id)
                    print(f"  Pharmacy: {pharmacy.name if pharmacy else 'N/A'} (ID: {rx.pharmacy_id})")
                if rx.medication_details:
                    print("  Medications:")
                    for med in rx.medication_details:
                        print(f"    - {med.get('name', 'Unknown')}: {med.get('dosage', '')} "
                              f"({med.get('frequency', '')} for {med.get('duration', '')})")
                if rx.instructions:
                    print(f"  Instructions: {rx.instructions}")
                print()
            
        except Exception as e:
            print(f"Error checking data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_data()
