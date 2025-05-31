import requests
import time
import re
import os
import json
from datetime import datetime, timedelta

class OpenRouterClient:
    """Client for interacting with the OpenRouter API"""
    
    def __init__(self, api_key):
        """Initialize the client with the API key"""
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.models_cache = None
        self.models_cache_time = None
        self.cache_duration = timedelta(minutes=30)  # Cache models for 30 minutes
    
    def get_models(self):
        """Get all available models from OpenRouter"""
        # Check if we have a valid cache
        if self.models_cache and self.models_cache_time and datetime.now() - self.models_cache_time < self.cache_duration:
            print("Using cached models list")
            return self.models_cache
            
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            models = response.json().get("data", [])
            
            # Update cache
            self.models_cache = models
            self.models_cache_time = datetime.now()
            
            return models
        except Exception as e:
            print(f"Error fetching models: {e}")
            # If we have a cache, return it even if expired
            if self.models_cache:
                print("Returning expired cache due to error")
                return self.models_cache
            raise
    
    def get_free_models(self):
        """Get all free models from OpenRouter"""
        all_models = self.get_models()
        
        # Filter for models that are free (prompt and completion costs are 0)
        free_models = []
        for model in all_models:
            pricing = model.get("pricing", {})
            if (pricing.get("prompt") == "0" and pricing.get("completion") == "0"):
                free_models.append(model)
        
        return free_models
    
    def send_math_problem(self, model_id, problem_text):
        """Send a math problem to a specific model and return the response"""
        try:
            print(f"Attempting to send problem to model: {model_id}", flush=True) # Log start with flush
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful math assistant. Solve the given problem step by step and provide the final answer clearly."
                        },
                        {
                            "role": "user",
                            "content": problem_text
                        }
                    ]
                },
                timeout=60  # Add a timeout to prevent hanging requests
            )
            
            print(f"Received response status code: {response.status_code} for model: {model_id}", flush=True) # Log status code with flush
            if not response.ok:
                 print(f"Error Response Text: {response.text}", flush=True) # Log error text if status not OK with flush
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            response_data = response.json()
            print(f"Successfully received and parsed JSON response for model: {model_id}", flush=True) # Log success with flush
            print(f"Raw response data for model {model_id}: {json.dumps(response_data, indent=2)}", flush=True)
            end_time = time.time()
            response_time = end_time - start_time
            
            # Extract the response text and token usage
            response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens) # Calculate if not provided

            return {
                "response_text": response_text,
                "response_time_seconds": response_time,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens # Add total_tokens
            }
        except requests.exceptions.Timeout:
            return {
                "response_text": "Request timed out after 60 seconds",
                "response_time_seconds": 60,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0, # Add total_tokens
                "error": "timeout"
            }
        except requests.exceptions.Timeout as e: # Catch specific timeout errors first
             print(f"Request Timed Out for model {model_id}: {e}", flush=True)
             # Return the specific timeout error structure we had before
             return {
                 "response_text": "Request timed out after 60 seconds",
                 "response_time_seconds": 60,
                 "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                 "error": "timeout"
             }
        except requests.exceptions.RequestException as e: # Catch other request errors
            print(f"Network/Request Error for model {model_id}: {e}", flush=True)
            return {
                "response_text": f"Network/Request Error: {str(e)}",
                "response_time_seconds": time.time() - start_time if 'start_time' in locals() else 0,
                "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                "error": f"Network/Request Error: {str(e)}"
            }
        except json.JSONDecodeError as e: # Catch JSON parsing errors
             print(f"JSON Decode Error for model {model_id}: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}", flush=True)
             return {
                "response_text": f"Invalid JSON Response: {response.text if 'response' in locals() else 'N/A'}",
                "response_time_seconds": time.time() - start_time if 'start_time' in locals() else 0,
                "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                "error": f"JSON Decode Error: {str(e)}"
             }
        except Exception as e: # Catch any other errors
            print(f"Generic Error testing model {model_id}: {type(e).__name__} - {e}", flush=True)
            # Log traceback for unexpected errors
            import traceback
            traceback.print_exc()
            return {
                "response_text": f"Unexpected Error: {str(e)}",
                "response_time_seconds": time.time() - start_time if 'start_time' in locals() else 0,
                "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                "error": f"Unexpected Error: {str(e)}"
            }
    
    def evaluate_response(self, response_text, problem_type="geometry_height"):
        """Evaluate if the response contains the correct answer based on problem type"""
        
        # Ensure response_text is a string
        if not isinstance(response_text, str):
            print(f"Warning: evaluate_response received non-string input: {type(response_text)}")
            return False, None

        if problem_type == "geometry_height":
            # Look for 2.4 or 2,4 possibly followed by 'm' or units like 'metros'
            # Allows for variations in spacing and phrasing.
            patterns = [
                r'2[,.]4\s*m(?:etros)?',  # Matches "2,4m", "2.4m", "2,4 m", "2.4 metros" etc.
                r'(?:é|is|equals|=)\s*2[,.]4', # Matches "= 2,4", "é 2.4" etc.
                r'\b2[,.]4\b' # Matches the number 2,4 or 2.4 as a whole word
            ]
            expected_value = "2.4" # Canonical value for comparison/logging

            print(f"Evaluating response for geometry height (expected ~{expected_value})...") # Debugging print
            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    print(f"Found match with pattern '{pattern}': {match.group(0)}") # Debugging print
                    # Simple check: return True if any pattern matches
                    return True, match.group(0) # Return the matched text

            print("No matching pattern found for geometry height.") # Debugging print
            return False, None

        elif problem_type == "xy":
            # Look for xy = 12 or similar patterns
            patterns = [
                r'xy\s*=\s*12',
                r'x\s*\*\s*y\s*=\s*12',
                r'product\s*(?:of\s*x\s*and\s*y|xy)\s*(?:is|equals|=)\s*12',
                r'value\s*of\s*xy\s*(?:is|equals|=)\s*12',
                r'xy\s*(?:is|equals)\s*12',
                r'\b12\b'  # Just the number 12 as a whole word
            ]
            expected_value = "12"

            print(f"Evaluating response for xy problem (expected {expected_value})...") # Debugging print
            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    print(f"Found match with pattern '{pattern}': {match.group(0)}") # Debugging print
                    return True, match.group(0)

            print("No matching pattern found for xy problem.") # Debugging print
            return False, None

        # Add other problem types here if needed
        # elif problem_type == "another_type":
        #    ...

        else:
            print(f"Warning: Unknown problem_type '{problem_type}' in evaluate_response.")
            return False, None

def test_openrouter_client():
    """Test function for the OpenRouter client"""
    api_key = os.environ.get("OPENROUTER_API_KEY", "your_api_key_here")
    client = OpenRouterClient(api_key)
    
    # Get all models
    print("Getting all models...")
    models = client.get_models()
    print(f"Found {len(models)} models")
    
    # Get free models
    print("\nGetting free models...")
    free_models = client.get_free_models()
    print(f"Found {len(free_models)} free models")
    
    for model in free_models[:3]:  # Test only the first 3 free models
        model_id = model.get("id")
        model_name = model.get("name", model_id)
        print(f"\nTesting model: {model_name}")
        
        # Test with a math problem
        problem = "If x² + y² = 25 and x + y = 7, what is the value of xy?"
        print(f"Sending problem: {problem}")
        
        result = client.send_math_problem(model_id, problem)
        print(f"Response time: {result['response_time_seconds']:.2f} seconds")
        print(f"Token usage: {result['prompt_tokens']} prompt, {result['completion_tokens']} completion")
        print(f"Response: {result['response_text'][:100]}...")
        
        # Evaluate the response
        is_correct, found_answer = client.evaluate_response(result["response_text"])
        print(f"Correct answer found: {is_correct}")
        if found_answer:
            print(f"Found answer: {found_answer}")

if __name__ == "__main__":
    test_openrouter_client()