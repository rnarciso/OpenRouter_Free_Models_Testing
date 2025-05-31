"""
OpenRouter API Example Script

This script demonstrates how to use the OpenRouter API to:
1. Get a list of available models
2. Filter for free models
3. Make a chat completion request
4. Track token usage and response time

API Key is required to run this script.
"""

import requests
import json
import time
from datetime import datetime

def get_models(api_key):
    """Get a list of all available models from OpenRouter API"""
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://research-project.example.com"  # Required by OpenRouter
    }
    
    print("Fetching available models...")
    start_time = time.time()
    response = requests.get(url, headers=headers)
    end_time = time.time()
    
    print(f"Response time: {end_time - start_time:.2f} seconds")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        models_data = response.json()
        return models_data
    else:
        print(f"Error: {response.text}")
        return None

def get_free_models(models_data):
    """Extract free models from the models data"""
    if not models_data or "data" not in models_data:
        return []
    
    free_models = []
    for model in models_data.get("data", []):
        model_id = model.get("id")
        model_name = model.get("name")
        context_length = model.get("context_length")
        provider = model.get("provider", {}).get("name", "Unknown")
        pricing = model.get("pricing", {})
        
        # Convert pricing values to float, handling potential string values
        try:
            prompt_cost = float(pricing.get("prompt", 0))
        except (TypeError, ValueError):
            prompt_cost = 0
            
        try:
            completion_cost = float(pricing.get("completion", 0))
        except (TypeError, ValueError):
            completion_cost = 0
        
        # Check if the model is free
        if prompt_cost == 0 and completion_cost == 0:
            free_models.append({
                "id": model_id,
                "name": model_name,
                "context_length": context_length,
                "provider": provider
            })
    
    return free_models

def chat_completion(api_key, model_id, messages):
    """Make a chat completion request to OpenRouter API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://research-project.example.com",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_id,
        "messages": messages
    }
    
    print(f"\nSending request to model: {model_id}")
    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    end_time = time.time()
    
    response_time = end_time - start_time
    print(f"Response time: {response_time:.2f} seconds")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        completion_data = response.json()
        return completion_data, response_time
    else:
        print(f"Error: {response.text}")
        return None, response_time

def get_key_info(api_key):
    """Get information about the API key"""
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://research-project.example.com"
    }
    
    print("\nFetching API key information...")
    response = requests.get(url, headers=headers)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        key_data = response.json()
        return key_data
    else:
        print(f"Error: {response.text}")
        return None

def display_token_usage(completion_data):
    """Display token usage information from completion response"""
    if not completion_data or "usage" not in completion_data:
        print("No token usage information available")
        return
    
    usage = completion_data.get("usage", {})
    print("\nToken Usage:")
    print(f"Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
    print(f"Completion tokens: {usage.get('completion_tokens', 'N/A')}")
    print(f"Total tokens: {usage.get('total_tokens', 'N/A')}")

def main():
    """Main function to demonstrate OpenRouter API usage"""
    # Replace with your API key
    api_key = "YOUR_API_KEY_HERE"  # Replace with actual API key
    
    # Get all available models
    models_data = get_models(api_key)
    if not models_data:
        print("Failed to retrieve models. Exiting.")
        return
    
    # Extract free models
    free_models = get_free_models(models_data)
    print(f"\nFound {len(free_models)} free models")
    
    # Display some free models
    print("\nSample of free models:")
    for i, model in enumerate(free_models[:5], 1):
        print(f"{i}. {model['name']} (ID: {model['id']})")
        print(f"   Context Length: {model['context_length']}")
        print(f"   Provider: {model['provider']}")
        print()
    
    # Select a model for testing (using the first free model)
    if free_models:
        test_model = free_models[0]
        print(f"Selected model for testing: {test_model['name']} ({test_model['id']})")
        
        # Create a simple conversation
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What can you tell me about OpenRouter API?"}
        ]
        
        # Make a completion request
        completion_data, response_time = chat_completion(api_key, test_model['id'], messages)
        
        # Display the response
        if completion_data:
            print("\nResponse content:")
            content = completion_data.get("choices", [{}])[0].get("message", {}).get("content", "No content")
            print(content)
            
            # Display token usage
            display_token_usage(completion_data)
            
            # Calculate cost (which is 0 for free models)
            print("\nCost: $0.00 (Free model)")
    else:
        print("No free models found for testing.")
    
    # Get API key information
    key_info = get_key_info(api_key)
    if key_info:
        print("\nAPI Key Information:")
        is_free_tier = key_info.get("data", {}).get("is_free_tier", False)
        rate_limit = key_info.get("data", {}).get("rate_limit", {})
        
        print(f"Free tier: {is_free_tier}")
        if rate_limit:
            print(f"Rate limit: {rate_limit.get('requests')} requests per {rate_limit.get('interval')}")

if __name__ == "__main__":
    main()