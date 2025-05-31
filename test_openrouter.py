#!/usr/bin/env python3
"""
Test script for the OpenRouter client module.
"""

import os
from openrouter_client import OpenRouterClient

def main():
    # Use the API key from environment variable
    API_KEY = os.getenv('OPENROUTER_API_KEY')
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        return
    
    # The math problem to test
    MATH_PROBLEM = "Temos: CA = 4m DB = 6m ABC e ABD são triângulos retângulos E é a intersecção de CB e AD F é a projeção de E em AB ABC e EFC são semelhantes ABD e EFD são semelhantes Qual a altura do segmento EF?"
    
    # Initialize the client
    client = OpenRouterClient(API_KEY)
    
    # Get and display available models
    print("Fetching available models...")
    models = client.get_models()
    print(f"Found {len(models)} models")
    
    # Get and display free models
    print("\nFetching free models...")
    free_models = client.get_free_models()
    print(f"Found {len(free_models)} free models")
    
    if not free_models:
        print("No free models found. Exiting test.")
        return
    
    # Display the first 5 free models (or fewer if less are available)
    print("\nAvailable free models:")
    for i, model in enumerate(free_models[:5]):
        print(f"{i+1}. {model.get('id')} - {model.get('name', 'Unknown name')}")
    
    # Select a free model to test
    selected_model_index = 3 # Try the fourth model (index 3)
    if len(free_models) <= selected_model_index:
        print(f"Error: Not enough free models available to select index {selected_model_index}. Trying the first one.")
        selected_model_index = 0
        if not free_models: # Double check if list became empty somehow
             print("No free models found. Exiting test.")
             return

    selected_model = free_models[selected_model_index]
    model_id = selected_model.get("id")
    model_name = selected_model.get("name", "Unknown model")
    
    print(f"\nTesting with model: {model_name} (ID: {model_id})")
    print(f"Sending math problem: {MATH_PROBLEM}")
    # Send the math problem to the selected model
    result = client.send_math_problem(model_id, MATH_PROBLEM)
    print(f"\nFull raw result dictionary: {result}") # Added for debugging

    # Check if the client returned an error
    if 'error' in result:
        print(f"\nError received from client: {result['error']}")
        print("Skipping further processing due to error.")
        return # Exit if there was an error like timeout

    print(f"Raw response text: {result.get('response_text', 'N/A')}") # Use .get for safety
    
    # Display the results
    print("\n===== RESULTS =====")
    print(f"Model: {model_name}")
    print(f"Response time: {result['response_time_seconds']:.2f} seconds")
    print(f"Token usage: {result['prompt_tokens']} prompt + {result['completion_tokens']} completion = {result.get('total_tokens', 0)} total")
    print("\n----- Response Text -----")
    print(result['response_text'])
    print(f"Response tokens: {result['prompt_tokens']}, {result['completion_tokens']}")
    print("--------------------------")
    
    
    # Evaluate the correctness of the response
    is_correct, found_answer = client.evaluate_response(result.get('response_text', ''), problem_type="geometry_height") # Use .get and specify problem type
    if is_correct:
        print(f"\n✅ CORRECT: Answer found in response: {found_answer}")
    else:
        print("\n❌ INCORRECT: The expected answer (2,4m or equivalent) was not found in the response.")
    
    print("\nTest completed successfully.")

if __name__ == "__main__":
    main()