#!/usr/bin/env python3
"""
OpenRouter Model Testing System

A Flask web application for testing and evaluating AI models using the OpenRouter API.
The application tests models on mathematical reasoning tasks and scores their performance.
"""

import os
import re
import time
import json
# import sqlite3 # Removed as database.py now handles DB choice
from flask import Flask, render_template, jsonify, request, Response
from openrouter_client import OpenRouterClient
import database  # Import the database module

# Initialize Flask app
app = Flask(__name__)

# Get API key from environment variable
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Initialize OpenRouter client
client = OpenRouterClient(API_KEY)

# Initialize the database
database.init_db()

# --- Global Problem State ---
DEFAULT_PROBLEM = "If x² + y² = 25 and x + y = 7, what is the value of xy?"
DEFAULT_CORRECT_ANSWER = "12"

current_problem = DEFAULT_PROBLEM
current_correct_answer = DEFAULT_CORRECT_ANSWER

def load_or_initialize_global_problem():
    global current_problem, current_correct_answer
    print("Attempting to load global problem from database...")
    problem_data = database.get_global_problem()
    if problem_data:
        current_problem = problem_data["problem_text"]
        current_correct_answer = problem_data["correct_answer"]
        print(f"Loaded global problem: '{current_problem[:50]}...' Answer: '{current_correct_answer}'")
    else:
        print("No global problem found in database, saving default problem.")
        current_problem = DEFAULT_PROBLEM
        current_correct_answer = DEFAULT_CORRECT_ANSWER
        database.save_global_problem(current_problem, current_correct_answer)
        print(f"Saved default global problem: '{current_problem[:50]}...' Answer: '{current_correct_answer}'")

load_or_initialize_global_problem()
# --- End Global Problem State ---


@app.route('/')
def index():
    """Render the main testing interface."""
    # current_problem and current_correct_answer are already global
    return render_template('index.html',
                           current_problem=current_problem,
                           current_correct_answer=current_correct_answer)

@app.route('/dashboard')
def dashboard():
    """Render the dashboard overview page."""
    return render_template('dashboard.html')

@app.route('/api/models')
def get_models():
    """
    Get a list of available free models.
    
    Returns:
        JSON: A list of free models with their details.
    """
    try:
        # Get free models from the client
        free_models = client.get_free_models()
        
        # Format the models for the frontend
        formatted_models = []
        for model in free_models:
            formatted_models.append({
                "id": model.get("id"),
                "name": model.get("name", "Unknown Model"),
                "provider": model.get("provider", "Unknown Provider")
            })
        
        return jsonify({"models": formatted_models})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['POST'])
def test_model():
    """
    Test a specific model with the math problem.
    
    Request body:
        model_id: The ID of the model to test.
    
    Returns:
        JSON: The test results including correctness, response time, and score.
    """
    try:
        # Get model ID from request
        data = request.json
        model_id = data.get("model_id")
        
        if not model_id:
            return jsonify({"error": "Model ID is required"}), 400
        
        # Get model details to fetch the name
        all_models = client.get_models() # Use cached if available
        model_details = next((m for m in all_models if m.get("id") == model_id), None)
        model_name = model_details.get("name", model_id) if model_details else model_id # Use ID if name not found

        # Send the math problem to the model
        result = client.send_math_problem(model_id, current_problem)
        # app.logger.debug(f"DEBUG: Result from send_math_problem for {model_id}: {result}") # Replaced by more specific log below

        # Log before evaluation
        response_text_snippet = result.get('response_text', '')[:100]
        app.logger.debug(f"Calling client.evaluate_response for model {model_id}. Expected answer: '{current_correct_answer}'. Model response (first 100 chars): '{response_text_snippet}'")
        
        # Evaluate the response
        is_correct, found_answer = client.evaluate_response(result.get("response_text", ""), current_correct_answer)
        
        # Calculate score
        score = calculate_score(is_correct, result.get("response_time_seconds", 0), result.get("total_tokens", 0))
        
        # Format the response
        response = {
            "model_name": model_name, # Use the fetched model name
            "correct": is_correct,
            "response_time": round(result["response_time_seconds"], 2),
            "token_usage": {
                "prompt": result["prompt_tokens"],
                "completion": result["completion_tokens"],
                "total": result.get("total_tokens", 0)
            },
            "answer": found_answer if is_correct else "Incorrect",
            "score": score,
            "response_text": result.get("response_text", "N/A") # Add response text
        }
        
        # Save the result to the database
        result_to_save = {
            "model_id": model_id,
            "model_name": model_name,
            "prompt": current_problem,
            "response_text": result.get("response_text", ""),
            "is_correct": is_correct,
            "answer_found": found_answer if is_correct else "Incorrect",
            "response_time": result["response_time_seconds"],
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
            "total_tokens": result.get("total_tokens", 0),
            "score": score,
            "expected_answer": current_correct_answer
        }
        database.save_result(result_to_save)
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-all')
def test_all_models():
    """
    Test all available free models and stream the results.
    
    Returns:
        Stream: Server-sent events with test results for each model.
    """
    def generate():
        try:
            # Get free models
            free_models = client.get_free_models()
            
            # Limit to first 5 models to prevent timeouts
            models_to_test = free_models[:5] # For actual testing, consider removing or increasing this limit
            total_models = len(models_to_test)
            
            # Send the total number of models to test
            yield f"data: {json.dumps({'type': 'total', 'data': {'total_models': total_models}})}\n\n"
            
            # Test each model
            for i, model in enumerate(models_to_test):
                model_id = model.get("id")
                model_name = model.get("name", "Unknown Model")
                
                try:
                    # Send progress update
                    progress_data = {
                        "current_model_count": i + 1,
                        "total_models": total_models,
                        "testing_model_name": model_name
                    }
                    yield f"data: {json.dumps({'type': 'progress', 'data': progress_data})}\n\n"
                    
                    # Test the model
                    result = client.send_math_problem(model_id, current_problem)
                    
                    # Check for errors from client.send_math_problem (e.g. timeout, network error)
                    if result.get("error"):
                        raise Exception(result.get("response_text", "Unknown error during model test"))

                    # Log before evaluation
                    response_text_snippet_all = result.get('response_text', '')[:100]
                    app.logger.debug(f"Calling client.evaluate_response in test_all_models for model {model_name}. Expected answer: '{current_correct_answer}'. Model response (first 100 chars): '{response_text_snippet_all}'")

                    # Evaluate the response
                    is_correct, found_answer = client.evaluate_response(result.get("response_text", ""), current_correct_answer)
                    
                    # Calculate score
                    score = calculate_score(is_correct, result.get("response_time_seconds", 0), result.get("total_tokens", 0))
                    
                    # Format the result
                    test_result = {
                        "model_id": model_id,
                        "model_name": model_name,
                        "correct": is_correct,
                        "response_time": round(result["response_time_seconds"], 2),
                        "token_usage": {
                            "prompt": result["prompt_tokens"],
                            "completion": result["completion_tokens"],
                            "total": result.get("total_tokens", 0)
                        },
                        "answer": found_answer if is_correct else "Incorrect",
                        "score": score
                    }
                    
                    # Send the result
                    # Save the result to the database
                    result_to_save = {
                        "model_id": model_id,
                        "model_name": model_name,
                        "prompt": current_problem,
                        "response_text": result.get("response_text", ""),
                        "is_correct": is_correct,
                        "answer_found": found_answer if is_correct else "Incorrect",
                        "response_time": result["response_time_seconds"],
                        "prompt_tokens": result["prompt_tokens"],
                        "completion_tokens": result["completion_tokens"],
                        "total_tokens": result.get("total_tokens", 0),
                        "score": score,
                        "expected_answer": current_correct_answer
                    }
                    database.save_result(result_to_save)
                    
                    # Send the result to the client
                    yield f"data: {json.dumps({'type': 'result', 'data': test_result})}\n\n"
                    
                except Exception as e:
                    # Send error for this model
                    error_data = {
                        "model_name": model_name,
                        "error_message": str(e)
                    }
                    yield f"data: {json.dumps({'type': 'error', 'data': error_data})}\n\n"
            
            # Send completion message
            completion_data = {"message": "All models tested successfully."}
            yield f"data: {json.dumps({'type': 'complete', 'data': completion_data})}\n\n"
            
        except Exception as e:
            # Send overall error
            overall_error_data = {"error_message": "Overall error: " + str(e)}
            yield f"data: {json.dumps({'type': 'error', 'data': overall_error_data})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/test-subset')
def test_subset():
    """
    Test a subset of free models (first 3) for quick testing.
    
    Returns:
        JSON: The test results for each model.
    """
    try:
        # Get free models
        free_models = client.get_free_models()
        
        # Take only the first 3 models
        models_to_test = free_models[:3]
        
        results = []
        for model in models_to_test:
            model_id = model.get("id")
            model_name = model.get("name", "Unknown Model")
            
            try:
                # Test the model
                result = client.send_math_problem(model_id, current_problem)

                # Log before evaluation
                response_text_snippet_subset = result.get('response_text', '')[:100]
                app.logger.debug(f"Calling client.evaluate_response in test_subset for model {model_name}. Expected answer: '{current_correct_answer}'. Model response (first 100 chars): '{response_text_snippet_subset}'")
                
                # Evaluate the response
                is_correct, found_answer = client.evaluate_response(result.get("response_text", ""), current_correct_answer)
                
                # Calculate score
                score = calculate_score(is_correct, result.get("response_time_seconds", 0), result.get("total_tokens", 0))
                
                # Format the result
                test_result = {
                    "model_id": model_id,
                    "model_name": model_name,
                    "correct": is_correct,
                    "response_time": round(result["response_time_seconds"], 2),
                    "token_usage": {
                        "prompt": result["prompt_tokens"],
                        "completion": result["completion_tokens"],
                        "total": result.get("total_tokens", 0)
                    },
                    "answer": found_answer if is_correct else "Incorrect",
                    "score": score
                }
                
                # Save the result to the database
                result_to_save = {
                    "model_id": model_id,
                    "model_name": model_name,
                    "prompt": current_problem,
                    "response_text": result.get("response_text", ""),
                    "is_correct": is_correct,
                    "answer_found": found_answer if is_correct else "Incorrect",
                    "response_time": result["response_time_seconds"],
                    "prompt_tokens": result["prompt_tokens"],
                    "completion_tokens": result["completion_tokens"],
                    "total_tokens": result.get("total_tokens", 0),
                        "score": score,
                        "expected_answer": current_correct_answer
                }
                database.save_result(result_to_save)
                
                results.append(test_result)
                
            except Exception as e:
                # Add error result for this model
                error_result = {
                    "model_id": model_id,
                    "model_name": model_name,
                    "error": str(e)
                }
                results.append(error_result)
        
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def calculate_score(is_correct, response_time, total_tokens):
    """
    Calculate the score for a model based on correctness, response time, and token usage.
    
    Args:
        is_correct (bool): Whether the model provided the correct answer.
        response_time (float): The response time in seconds.
        total_tokens (int): The total number of tokens used.
    
    Returns:
        int: The calculated score (0-100).
    """
    # Correctness score (70 points)
    correctness_score = 70 if is_correct else 0
    
    # Response time score (20 points)
    if response_time <= 1:
        time_score = 20
    elif response_time <= 2:
        time_score = 15
    elif response_time <= 3:
        time_score = 10
    elif response_time <= 4:
        time_score = 5
    else:
        time_score = 0
    
    # Token efficiency score (10 points)
    if total_tokens <= 100:
        token_score = 10
    elif total_tokens <= 200:
        token_score = 8
    elif total_tokens <= 300:
        token_score = 6
    elif total_tokens <= 400:
        token_score = 4
    elif total_tokens <= 500:
        token_score = 2
    else:
        token_score = 0
    
    # Total score
    return correctness_score + time_score + token_score

@app.route('/api/problem', methods=['POST'])
def update_problem():
    """Update the current math problem and its correct answer."""
    global current_problem, current_correct_answer
    data = request.json
    new_problem_text = data.get('problem_text')
    new_correct_answer = data.get('correct_answer')

    if not new_problem_text or not new_correct_answer:
        return jsonify({"error": "Both problem_text and correct_answer are required"}), 400
    
    # Save to database
    database.save_global_problem(new_problem_text, new_correct_answer)
    
    # Update global variables
    current_problem = new_problem_text
    current_correct_answer = new_correct_answer

    return jsonify({
        "message": "Problem and answer updated successfully",
        "current_problem": current_problem,
        "current_correct_answer": current_correct_answer
    })

@app.route('/api/results')
def get_results():
    """Get all saved test results from the database."""
    try:
        results_list = database.get_all_results()
        return jsonify(results_list)
    except Exception as e:
        # Log the exception for more detailed debugging if needed
        app.logger.error(f"Error fetching results: {e}")
        return jsonify({"error": "An error occurred while fetching results."}), 500

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5002)