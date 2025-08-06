"""
AI Service for Tujali Telehealth

This module provides AI-powered personalized health recommendations
using OpenAI's API with Anthropic Claude as a fallback. It generates 
health tips based on patient data, symptoms, and regional health concerns.
"""

import os
import json
import logging
from openai import OpenAI
from anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Setup Anthropic client as fallback
anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
anthropic_client = None
if anthropic_key:
    try:
        anthropic_client = Anthropic(api_key=anthropic_key)
        logger.info("Anthropic client initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Anthropic client: {str(e)}")
else:
    logger.warning("ANTHROPIC_API_KEY not found in environment variables")

def generate_health_tips(patient_data, symptoms=None, language="en"):
    """
    Generate personalized health tips based on patient data and symptoms
    
    Args:
        patient_data (dict): Patient demographic information and medical history
        symptoms (list, optional): List of symptoms reported by the patient
        language (str): Language code for the response (e.g., 'en', 'sw', 'fr')
        
    Returns:
        dict: JSON response containing health tips and recommendations
    """
    # Prepare prompt based on patient data and symptoms
    patient_age = patient_data.get('age', 'unknown')
    patient_gender = patient_data.get('gender', 'unknown')
    patient_location = patient_data.get('location', 'unknown')
    
    prompt = f"""
    You are a medical assistant providing personalized health tips for a patient in Africa.
    
    Patient Information:
    - Age: {patient_age}
    - Gender: {patient_gender}
    - Location: {patient_location}
    """
    
    if symptoms:
        prompt += "\nReported Symptoms:\n"
        for symptom in symptoms:
            severity = symptom.get('severity', 'Unknown')
            category = symptom.get('category', 'General')
            prompt += f"- {symptom.get('description', 'Unknown symptom')} (Severity: {severity}, Category: {category})\n"
    
    prompt += """
    Based on the above information, provide 3-5 personalized health tips and recommendations.
    Consider:
    1. Age-appropriate advice
    2. Gender-specific health concerns if relevant
    3. Regional health issues common in their location
    4. Specific advice for managing reported symptoms
    5. Simple lifestyle recommendations
    
    Format your response as JSON with the following structure:
    {
        "health_tips": [
            {"title": "Brief title", "description": "Detailed explanation of the health tip"}
        ],
        "symptom_management": [
            {"symptom": "Specific symptom", "advice": "Advice for managing this symptom"}
        ],
        "follow_up": "Advice on when to seek further medical attention"
    }
    
    Keep all descriptions concise, clear, and culturally appropriate for the region.
    """
    
    # Define appropriate language models for different languages
    language_prompts = {
        "en": "Provide the response in English.",
        "sw": "Provide the response in Swahili.",
        "fr": "Provide the response in French.",
        "or": "Provide the response in Oromo if possible, otherwise in English.",
        "so": "Provide the response in Somali if possible, otherwise in English.",
        "am": "Provide the response in Amharic if possible, otherwise in English."
    }
    
    # Add language instruction
    lang_instruction = language_prompts.get(language, language_prompts["en"])
    prompt += f"\n\n{lang_instruction}"
    
    # Try OpenAI first
    try:
        logger.info("Attempting to generate health tips with OpenAI")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use the available model
            messages=[
                {"role": "system", "content": "You are a medical advisor with expertise in African healthcare contexts, providing culturally appropriate health advice."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        # Extract and parse the JSON response
        result = json.loads(response.choices[0].message.content)
        logger.info("Successfully generated health tips with OpenAI")
        return result
    
    except Exception as e:
        logger.warning(f"OpenAI error: {str(e)}")
        
        # Try Anthropic as fallback
        if anthropic_client:
            try:
                logger.info("Attempting to generate health tips with Anthropic Claude")
                response = anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",  # The newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                    max_tokens=1024,
                    system="You are a medical advisor with expertise in African healthcare contexts, providing culturally appropriate health advice. Always respond in valid JSON format.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract and parse the JSON response
                result = json.loads(response.content[0].text)
                logger.info("Successfully generated health tips with Anthropic Claude")
                return result
            
            except Exception as anthropic_error:
                logger.error(f"Anthropic fallback error: {str(anthropic_error)}")
        else:
            logger.error("No Anthropic client available for fallback")
        
        # Return an error message if both APIs fail
        return {
            "health_tips": [
                {"title": "Error", "description": "Unable to generate health tips at this time."}
            ],
            "follow_up": "Please consult with a healthcare provider for personalized advice."
        }

def generate_health_education(topic, language="en"):
    """
    Generate general health education content on a specific topic
    
    Args:
        topic (str): Health topic to generate information about
        language (str): Language code for the response
        
    Returns:
        dict: JSON response containing educational content
    """
    language_prompts = {
        "en": "Provide the response in English.",
        "sw": "Provide the response in Swahili.",
        "fr": "Provide the response in French.",
        "or": "Provide the response in Oromo if possible, otherwise in English.",
        "so": "Provide the response in Somali if possible, otherwise in English.",
        "am": "Provide the response in Amharic if possible, otherwise in English."
    }
    
    lang_instruction = language_prompts.get(language, language_prompts["en"])
    
    prompt = f"""
    Generate educational health content about "{topic}" for patients in rural Africa.
    
    Keep the information:
    1. Simple and easy to understand
    2. Relevant to typical health conditions in Africa
    3. Actionable with limited resources
    4. Culturally appropriate
    
    Format your response as JSON with the following structure:
    {{
        "title": "Title for the health topic",
        "overview": "Brief overview of the topic",
        "key_points": [
            "Important point 1",
            "Important point 2"
        ],
        "prevention": [
            "Prevention tip 1",
            "Prevention tip 2"
        ],
        "when_to_seek_help": "Guidance on when to seek medical assistance"
    }}
    
    {lang_instruction}
    """
    
    # Try OpenAI first
    try:
        logger.info("Attempting to generate health education with OpenAI")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use the available model
            messages=[
                {"role": "system", "content": "You are a health educator specializing in public health in African communities."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        # Extract and parse the JSON response
        result = json.loads(response.choices[0].message.content)
        logger.info("Successfully generated health education with OpenAI")
        return result
    
    except Exception as e:
        logger.warning(f"OpenAI error: {str(e)}")
        
        # Try Anthropic as fallback
        if anthropic_client:
            try:
                logger.info("Attempting to generate health education with Anthropic Claude")
                response = anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",  # The newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                    max_tokens=1024,
                    system="You are a health educator specializing in public health in African communities. Always respond in valid JSON format.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract and parse the JSON response
                result = json.loads(response.content[0].text)
                logger.info("Successfully generated health education with Anthropic Claude")
                return result
            
            except Exception as anthropic_error:
                logger.error(f"Anthropic fallback error: {str(anthropic_error)}")
        else:
            logger.error("No Anthropic client available for fallback")
        
        # Return a fallback message if both APIs fail
        return {
            "title": topic,
            "overview": "Information temporarily unavailable.",
            "key_points": ["Please try again later."],
            "prevention": ["Consult with a healthcare provider for advice."],
            "when_to_seek_help": "If you have concerns, please contact a healthcare facility."
        }