from app import app, db
from models_sqlalchemy import HealthInfo, Patient
from datetime import datetime, timedelta
import random

def add_test_symptoms():
    with app.app_context():
        # Create a test patient if none exists
        patient = Patient.query.first()
        if not patient:
            patient = Patient(
                phone_number='+254700000001',
                name='Test Patient',
                age=30,
                gender='Male',
                location='Nairobi, Kenya'
            )
            db.session.add(patient)
            db.session.commit()

        # Sample symptoms with different categories
        symptoms = [
            {
                'title': 'Headache',
                'content': 'Headache\nSeverity: Moderate\nLocation: Head\nDuration: 2 days',
                'category': 'symptom'
            },
            {
                'title': 'Cough',
                'content': 'Cough\nSeverity: Mild\nLocation: Throat\nWith phlegm',
                'category': 'symptom'
            },
            {
                'title': 'Fever',
                'content': 'Fever\nSeverity: High\nTemperature: 38.5°C\nDuration: 1 day',
                'category': 'symptom'
            },
            {
                'title': 'Stomach Pain',
                'content': 'Stomach Pain\nSeverity: Severe\nLocation: Abdomen\nWith nausea',
                'category': 'symptom'
            },
            {
                'title': 'Fatigue',
                'content': 'Fatigue\nSeverity: Mild\nDuration: 1 week\nWith dizziness',
                'category': 'symptom'
            }
        ]

        # Add symptoms with different dates (last 7 days)
        for i, symptom in enumerate(symptoms):
            record = HealthInfo(
                title=symptom['title'],
                content=symptom['content'],
                category=symptom['category'],
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 6))
            )
            db.session.add(record)
        
        try:
            db.session.commit()
            print("Successfully added test symptoms!")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding test symptoms: {str(e)}")

if __name__ == '__main__':
    add_test_symptoms()
