from app import app, db_ext
from sqlalchemy import text

def query_prescriptions():
    with app.app_context():
        try:
            # Execute a raw SQL query to get all prescriptions
            result = db_ext.session.execute(text("SELECT * FROM prescriptions"))
            
            # Get column names
            columns = result.keys()
            
            # Fetch all rows
            rows = result.fetchall()
            
            print(f"Found {len(rows)} prescriptions in the database")
            
            if rows:
                print("\nSample prescription:")
                for i, row in enumerate(rows[:5]):  # Show first 5 rows
                    print(f"\nPrescription {i+1}:")
                    for col in columns:
                        print(f"  {col}: {getattr(row, col, 'N/A')}")
            
            # Also check the provider_id of the current user
            from flask_login import current_user
            if current_user.is_authenticated:
                print(f"\nCurrent user ID: {current_user.id}")
                # Get provider for current user
                from models_sqlalchemy import Provider
                provider = Provider.query.filter_by(user_id=current_user.id).first()
                if provider:
                    print(f"Current user is provider with ID: {provider.id}")
                    # Get prescriptions for this provider
                    result = db_ext.session.execute(
                        text("SELECT * FROM prescriptions WHERE provider_id = :provider_id"),
                        {"provider_id": provider.id}
                    )
                    provider_prescriptions = result.fetchall()
                    print(f"Found {len(provider_prescriptions)} prescriptions for current provider")
                else:
                    print("Current user is not a provider")
            
        except Exception as e:
            print(f"Error querying database: {e}")

if __name__ == '__main__':
    query_prescriptions()
