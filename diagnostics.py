"""
Diagnostics tool for Tujali Telehealth

This script helps diagnose and test the AI service and other critical
components of the Tujali Telehealth system.
"""

import os
import logging
import json
from openai import OpenAI
from anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_openai_connection():
    """
    Test the connection to OpenAI API
    """
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {"success": False, "error": "OPENAI_API_KEY not found in environment variables"}

        # Print the first few characters of the API key (for debugging only)
        logger.info(f"Using OpenAI API key starting with: {api_key[:5]}...")
        
        client = OpenAI(api_key=api_key)
        
        # Try a simple request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=10
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "model": "gpt-3.5-turbo"
        }
    
    except Exception as e:
        logger.error(f"OpenAI test error: {str(e)}")
        return {"success": False, "error": str(e)}

def test_anthropic_connection():
    """
    Test the connection to Anthropic API
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"success": False, "error": "ANTHROPIC_API_KEY not found in environment variables"}

        # Print the first few characters of the API key (for debugging only)
        logger.info(f"Using Anthropic API key starting with: {api_key[:5]}...")
        
        client = Anthropic(api_key=api_key)
        
        # Try a simple request
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # The newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Say hello!"}
            ]
        )
        
        return {
            "success": True,
            "response": response.content[0].text,
            "model": "claude-3-5-sonnet-20241022"  # The newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        }
    
    except Exception as e:
        logger.error(f"Anthropic test error: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("\n=== Tujali Telehealth Diagnostics ===\n")
    
    print("\n--- OpenAI API Test ---")
    openai_result = test_openai_connection()
    if openai_result["success"]:
        print(f"✅ OpenAI API working! Response: {openai_result['response']}")
    else:
        print(f"❌ OpenAI API error: {openai_result['error']}")
    
    print("\n--- Anthropic API Test ---")
    anthropic_result = test_anthropic_connection()
    if anthropic_result["success"]:
        print(f"✅ Anthropic API working! Response: {anthropic_result['response']}")
    else:
        print(f"❌ Anthropic API error: {anthropic_result['error']}")