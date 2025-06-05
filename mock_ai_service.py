"""
Mock AI Service for Tujali Telehealth

This module provides mock responses for personalized health recommendations
when the AI services are unavailable or exceeding quota limits. It follows
the same interface as the ai_service module but does not make actual API calls.
"""

import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_health_tips(patient_data, symptoms=None, language="en"):
    """
    Generate mock personalized health tips based on patient data and symptoms

    Args:
        patient_data (dict): Patient demographic information and medical history
        symptoms (list, optional): List of symptoms reported by the patient
        language (str): Language code for the response (e.g., 'en', 'sw', 'fr')

    Returns:
        dict: JSON response containing health tips and recommendations
    """
    logger.info(f"Generating mock health tips for patient in language: {language}")

    # Extract patient information
    patient_age = patient_data.get('age', 'unknown')
    patient_gender = patient_data.get('gender', 'unknown')
    patient_location = patient_data.get('location', 'unknown')

    # Create basic response structure
    response = {
        "health_tips": [],
        "symptom_management": [],
        "follow_up": ""
    }

    # General health tips for everyone
    general_tips = [
        {
            "title": "Stay Hydrated",
            "description": "Drink at least 8 glasses of clean water daily, especially in hot weather."
        },
        {
            "title": "Balanced Diet",
            "description": "Eat a variety of fruits, vegetables, and whole grains when available. Limit processed foods and excess sugar."
        },
        {
            "title": "Regular Exercise",
            "description": "Aim for at least 30 minutes of physical activity most days, even if it's just walking or household chores."
        },
        {
            "title": "Hand Hygiene",
            "description": "Wash hands frequently with soap and water for at least 20 seconds to prevent infections."
        },
        {
            "title": "Adequate Sleep",
            "description": "Try to get 7-8 hours of sleep per night to support your immune system and overall health."
        }
    ]

    # Add age-specific tips
    age_tips = {}
    try:
        patient_age_int = int(patient_age)
        if patient_age_int < 18:
            age_tips = {
                "title": "Childhood Health",
                "description": "Ensure children receive all recommended vaccinations and have regular health check-ups."
            }
        elif patient_age_int >= 18 and patient_age_int < 50:
            age_tips = {
                "title": "Adult Preventive Care",
                "description": "Have regular health screenings appropriate for your age and risk factors."
            }
        else:
            age_tips = {
                "title": "Senior Health",
                "description": "Pay special attention to blood pressure monitoring and joint health. Stay mentally active."
            }
    except:
        age_tips = {
            "title": "Regular Check-ups",
            "description": "Have regular health check-ups regardless of your age."
        }

    # Add gender-specific tips
    gender_tips = {}
    if patient_gender.lower() == 'female':
        gender_tips = {
            "title": "Women's Health",
            "description": "Consider regular breast examinations and reproductive health check-ups."
        }
    elif patient_gender.lower() == 'male':
        gender_tips = {
            "title": "Men's Health",
            "description": "Be aware of risks for heart disease and consider regular prostate health check-ups."
        }
    else:
        gender_tips = {
            "title": "General Health Monitoring",
            "description": "Monitor your body for unexpected changes and consult healthcare providers when needed."
        }

    # Location-specific tips
    location_tips = {}
    if "rural" in patient_location.lower():
        location_tips = {
            "title": "Rural Health Access",
            "description": "Know the nearest health facility and keep emergency contact numbers readily available."
        }
    elif "urban" in patient_location.lower():
        location_tips = {
            "title": "Urban Health",
            "description": "Be mindful of air quality and take steps to reduce exposure to pollution when possible."
        }
    else:
        location_tips = {
            "title": "Local Health Resources",
            "description": "Familiarize yourself with health resources available in your community."
        }

    # Add symptom management advice if symptoms:
    if symptoms:
        # Group symptoms by category for better organization
        symptom_groups = {}
        for symptom in symptoms:
            description = symptom.get('description', '').lower()
            severity = symptom.get('severity', 'Unknown')
            category = symptom.get('category', 'General')

            if category not in symptom_groups:
                symptom_groups[category] = []
            symptom_groups[category].append((description, severity))

        # Generate advice for each symptom category
        for category, symptom_list in symptom_groups.items():
            if category == 'respiratory':
                severe = any(sev == 'Severe' for _, sev in symptom_list)
                response["symptom_management"].append({
                    "symptom": "Respiratory symptoms",
                    "advice": "Rest, stay hydrated, and use a humidifier if available. " + 
                            ("Seek immediate medical attention." if severe else "Monitor symptoms and seek medical help if they worsen.")
                })
            elif category == 'digestive':
                response["symptom_management"].append({
                    "symptom": "Digestive issues",
                    "advice": "Stay hydrated, eat bland foods, and consider oral rehydration. Avoid spicy or heavy foods."
                })
            elif category == 'pain':
                locations = [desc for desc, _ in symptom_list]
                response["symptom_management"].append({
                    "symptom": f"Pain management ({', '.join(locations)})",
                    "advice": "Rest affected areas, use appropriate pain relief if available, apply cold/hot compress as needed."
                })
            elif category == 'fever':
                severe = any(sev == 'Severe' for _, sev in symptom_list)
                response["symptom_management"].append({
                    "symptom": "Fever management",
                    "advice": "Stay hydrated, rest, and monitor temperature. " +
                            ("Seek immediate medical attention if fever is very high." if severe else "Use fever reducers if available.")
                })
            elif category == 'skin':
                response["symptom_management"].append({
                    "symptom": "Skin conditions",
                    "advice": "Keep affected areas clean and dry. Avoid scratching. Use appropriate topical treatments if available."
                })

    # Add tips to response
    response["health_tips"] = [general_tips[0], general_tips[1], age_tips, gender_tips, location_tips]

    # Add follow-up advice
    response["follow_up"] = "If symptoms persist or worsen after 48-72 hours, please seek medical attention at your nearest health facility."

    # Translate response based on language if needed
    # For the mock service, we'll just add a note about the language
    if language != "en":
        language_names = {
            "sw": "Swahili",
            "fr": "French",
            "or": "Oromo",
            "so": "Somali",
            "am": "Amharic"
        }
        lang_name = language_names.get(language, language)
        response["language_note"] = f"These recommendations would normally be provided in {lang_name}."

    logger.info("Successfully generated mock health tips")
    return response

def generate_health_education(topic, language="en"):
    """
    Generate mock health education content on a specific topic

    Args:
        topic (str): Health topic to generate information about
        language (str): Language code for the response

    Returns:
        dict: JSON response containing educational content
    """
    logger.info(f"Generating mock health education about '{topic}' in language: {language}")

    # Clean and lowercase the topic for matching
    clean_topic = topic.lower().strip()

    # Define some common health topics and prepared responses
    topics = {
        "malaria": {
            "title": "Understanding Malaria",
            "overview": "Malaria is a serious disease spread by mosquitoes that causes fever, chills, and flu-like symptoms.",
            "key_points": [
                "Malaria is caused by a parasite spread through mosquito bites",
                "Symptoms include fever, chills, headache, and fatigue",
                "It's preventable and treatable, but can be fatal if not addressed promptly"
            ],
            "prevention": [
                "Sleep under insecticide-treated mosquito nets",
                "Use mosquito repellent when outdoors",
                "Eliminate standing water where mosquitoes breed",
                "Take preventive medication if prescribed by healthcare providers"
            ],
            "when_to_seek_help": "Seek medical help immediately if you develop fever, chills, headache, or muscle aches after being in a malaria-endemic area."
        },
        "hiv": {
            "title": "HIV Awareness and Prevention",
            "overview": "HIV is a virus that attacks the immune system and can lead to AIDS if left untreated.",
            "key_points": [
                "HIV can be transmitted through certain body fluids",
                "With proper treatment, people with HIV can live long, healthy lives",
                "Regular testing is important for early detection and treatment"
            ],
            "prevention": [
                "Practice safe sex by using condoms correctly",
                "Never share needles or other injection equipment",
                "Get tested regularly if you are sexually active",
                "Consider pre-exposure prophylaxis (PrEP) if at high risk"
            ],
            "when_to_seek_help": "Get tested for HIV if you've had unprotected sex, shared needles, or had other potential exposure. Early treatment is crucial."
        },
        "nutrition": {
            "title": "Proper Nutrition for Good Health",
            "overview": "Good nutrition is essential for health and can help prevent many diseases.",
            "key_points": [
                "A balanced diet includes a variety of foods from all food groups",
                "Proper nutrition strengthens the immune system",
                "Local, seasonal foods are often the most nutritious options"
            ],
            "prevention": [
                "Eat plenty of fruits and vegetables when available",
                "Choose whole grains over refined grains when possible",
                "Limit sugar, salt, and processed foods",
                "Stay hydrated by drinking clean water"
            ],
            "when_to_seek_help": "If you experience unexpected weight loss, constant fatigue, or other nutrition-related concerns, consult a healthcare provider."
        },
        "diabetes": {
            "title": "Understanding and Managing Diabetes",
            "overview": "Diabetes is a condition where the body cannot properly regulate blood sugar levels.",
            "key_points": [
                "Type 2 diabetes is increasingly common in Africa",
                "Risk factors include family history, obesity, and physical inactivity",
                "Symptoms may include increased thirst, frequent urination, and fatigue"
            ],
            "prevention": [
                "Maintain a healthy weight through diet and exercise",
                "Limit consumption of sugary foods and beverages",
                "Eat regular meals with balanced nutrition",
                "Stay physically active with daily movement"
            ],
            "when_to_seek_help": "If you experience excessive thirst, frequent urination, unexplained weight loss, or blurred vision, seek medical attention."
        },
        "covid": {
            "title": "COVID-19 Prevention and Care",
            "overview": "COVID-19 is a contagious respiratory illness caused by the SARS-CoV-2 virus.",
            "key_points": [
                "COVID-19 spreads mainly through respiratory droplets",
                "Symptoms include fever, cough, fatigue, and loss of taste or smell",
                "Vaccination is an effective way to prevent severe illness"
            ],
            "prevention": [
                "Wash hands frequently with soap and water",
                "Consider wearing a mask in crowded or poorly ventilated areas",
                "Stay home if feeling unwell",
                "Get vaccinated if vaccines are available"
            ],
            "when_to_seek_help": "Seek immediate medical attention if you experience difficulty breathing, persistent chest pain, or confusion."
        }
    }

    # Default response for topics not in our database
    default_response = {
        "title": f"Health Information: {topic}",
        "overview": f"Information about {topic} is important for maintaining good health.",
        "key_points": [
            "Regular check-ups help detect health issues early",
            "Consult healthcare providers for personalized advice",
            "Preventive measures are better than curing illnesses"
        ],
        "prevention": [
            "Maintain overall good health with proper nutrition",
            "Stay physically active with regular exercise",
            "Practice good hygiene to prevent infections",
            "Avoid harmful substances like tobacco and excess alcohol"
        ],
        "when_to_seek_help": "If you have specific concerns or symptoms related to this topic, consult a healthcare provider."
    }

    # Find the best matching topic or use default
    selected_response = None
    for key, content in topics.items():
        if key in clean_topic or clean_topic in key:
            selected_response = content
            break

    if not selected_response:
        selected_response = default_response
        # Update the title if we're using the default
        selected_response["title"] = f"Health Information: {topic}"

    # Translate response based on language if needed
    # For the mock service, we'll just add a note about the language
    if language != "en":
        language_names = {
            "sw": "Swahili",
            "fr": "French",
            "or": "Oromo",
            "so": "Somali",
            "am": "Amharic"
        }
        lang_name = language_names.get(language, language)
        selected_response["language_note"] = f"This information would normally be provided in {lang_name}."

    logger.info("Successfully generated mock health education content")
    return selected_response