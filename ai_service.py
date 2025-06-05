"""
AI Service for Tujali Telehealth

This module provides AI-powered personalized health recommendations
using DeepSeek API. It generates health tips based on patient data, 
symptoms, and regional health concerns.
"""

import os
import json
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepSeek API configuration
DEEPSEEK_API_KEY = "sk-b55f33daac7b41b59c62cd01c276eba3"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Headers for DeepSeek API
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
}

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
    try:
        # Prepare the prompt for the AI
        prompt = f"""You are a helpful medical assistant. Please provide health recommendations based on the following patient information:
        
Patient Data: {json.dumps(patient_data, indent=2)}"""
        
        if symptoms:
            prompt += f"\n\nSymptoms: {', '.join(symptoms)}"
            
        prompt += "\n\nPlease provide personalized health recommendations in a JSON format with the following structure:"
        prompt += """
        {
            "overview": "Brief summary of the health assessment",
            "recommendations": [
                {
                    "category": "Category name",
                    "description": "Detailed recommendation",
                    "priority": "high/medium/low"
                }
            ],
            "follow_up": "When and under what conditions to seek further medical attention"
        }
        """
        
        # Prepare the request payload for DeepSeek
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful medical assistant that provides health recommendations in JSON format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Make the API call to DeepSeek
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload
        )
        
        # Check for successful response
        response.raise_for_status()
        
        # Parse the response
        response_data = response.json()
        content = response_data['choices'][0]['message']['content']
        
        # Clean and parse the JSON response
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:-3].strip()  # Remove markdown code block
            
        return json.loads(content)
        
    except Exception as e:
        logger.error(f"Error in generate_health_tips: {str(e)}")
        # Return a safe default response in case of errors
        return {
            "overview": "We're having trouble generating personalized recommendations at the moment.",
            "recommendations": [
                {
                    "category": "General Health",
                    "description": "Please consult with a healthcare professional for personalized advice.",
                    "priority": "high"
                }
            ],
            "follow_up": "Contact a healthcare provider if you have any immediate concerns."
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
    try:
        # Prepare the prompt for the AI
        prompt = f"""You are a helpful health educator. Please provide educational content on the topic of "{topic}".
        
Please provide the content in a JSON format with the following structure:
{
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
}
"""
        
        # Prepare the request payload for DeepSeek
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful health educator that provides educational content in JSON format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Make the API call to DeepSeek
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload
        )
        
        # Check for successful response
        response.raise_for_status()
        
        # Parse the response
        response_data = response.json()
        content = response_data['choices'][0]['message']['content']
        
        # Clean and parse the JSON response
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:-3].strip()  # Remove markdown code block
            
        return json.loads(content)
        
    except Exception as e:
        logger.error(f"Error in generate_health_education: {str(e)}")
        # Return a safe default response in case of errors
        return {
            "title": topic,
            "overview": "Information temporarily unavailable.",
            "key_points": ["Please try again later."],
            "prevention": ["Consult with a healthcare provider for advice."],
            "when_to_seek_help": "If you have concerns, please contact a healthcare facility."
        }