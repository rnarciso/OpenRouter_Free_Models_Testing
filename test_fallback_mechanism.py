#!/usr/bin/env python3
"""
Test script to demonstrate the improved fallback mechanism for OpenRouter models
"""

import os
from openrouter_client import OpenRouterClient

def test_fallback_mechanism():
    """Test the fallback mechanism with different model types"""
    
    # Get API key from environment
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        return
    
    # Initialize client
    client = OpenRouterClient(api_key)
    
    # Test problem
    problem = "What is 15 + 27?"
    
    print("=== Testing Fallback Mechanism ===\n")
    
    # Test 1: Model that requires completion-style requests (pre-configured)
    print("1. Testing pre-configured completion-style model:")
    print("   Model: meta-llama/llama-4-scout:free")
    result = client.send_math_problem("meta-llama/llama-4-scout:free", problem)
    print(f"   Result: {result['response_text'][:100]}...")
    print(f"   Response time: {result['response_time_seconds']:.2f}s")
    print()
    
    # Test 2: Add a model manually to completion-style list
    print("2. Testing manually added completion-style model:")
    test_model = "meta-llama/llama-3.1-8b-instruct:free"
    client.add_completion_style_model(test_model)
    print(f"   Added {test_model} to completion-style models")
    result = client.send_math_problem(test_model, problem)
    print(f"   Result: {result['response_text'][:100]}...")
    print(f"   Response time: {result['response_time_seconds']:.2f}s")
    print()
    
    # Test 3: Test automatic fallback detection
    print("3. Testing automatic fallback detection:")
    print("   This will try standard format first, then fallback to completion-style if needed")
    unknown_model = "microsoft/phi-3-mini-128k-instruct:free"
    result = client.send_math_problem(unknown_model, problem)
    print(f"   Result: {result['response_text'][:100]}...")
    print(f"   Response time: {result['response_time_seconds']:.2f}s")
    print()
    
    # Show current completion-style models
    print("4. Current completion-style models:")
    completion_models = client.get_completion_style_models()
    for model in completion_models:
        print(f"   - {model}")
    print()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_fallback_mechanism()