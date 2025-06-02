# OpenRouter Fallback Mechanism

This document explains the improved fallback mechanism for handling models that require different request formats in the OpenRouter API.

## Problem

Some models like `meta-llama/llama-4-scout:free` require a specific request format (completion-style) instead of the standard chat completion format. The original implementation had several issues:

1. Only worked for one specific model
2. Inefficient (tried standard format first, then fallback)
3. Not extensible for other models

## Solution

The improved fallback mechanism provides:

### 1. Smart Model Detection
- Maintains a set of known completion-style models
- Automatically detects new models that require completion-style requests
- Uses the appropriate format on first try for known models

### 2. Flexible Fallback Strategy
- **For known completion-style models**: Try completion-style first, fallback to standard if needed
- **For other models**: Try standard first, fallback to completion-style if needed
- **Auto-learning**: Automatically adds models to completion-style list when fallback succeeds

### 3. Manual Management
- Add models manually: `client.add_completion_style_model(model_id)`
- Remove models: `client.remove_completion_style_model(model_id)`
- List current models: `client.get_completion_style_models()`

## Request Formats

### Standard Chat Completion Format
```python
{
    "model": "model_id",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant..."
        },
        {
            "role": "user", 
            "content": "User's question"
        }
    ]
}
```

### Completion-Style Format
```python
{
    "model": "model_id",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Combined system + user message"
                }
            ]
        }
    ]
}
```

## Usage Examples

### Basic Usage
```python
from openrouter_client import OpenRouterClient

client = OpenRouterClient(api_key)

# The client automatically handles the appropriate format
result = client.send_math_problem("meta-llama/llama-4-scout:free", "What is 2+2?")
```

### Manual Model Management
```python
# Add a model that requires completion-style requests
client.add_completion_style_model("some-model:free")

# Remove a model from the completion-style list
client.remove_completion_style_model("some-model:free")

# Check which models are using completion-style
completion_models = client.get_completion_style_models()
print(f"Completion-style models: {completion_models}")
```

### Testing the Mechanism
```python
# Run the test script
python test_fallback_mechanism.py
```

## Benefits

1. **Efficiency**: Uses the correct format on first try for known models
2. **Reliability**: Automatic fallback ensures requests succeed when possible
3. **Extensibility**: Easy to add new models that require special handling
4. **Auto-learning**: Automatically discovers models that need completion-style requests
5. **Maintainability**: Clean separation of concerns with helper methods

## Pre-configured Models

The following models are pre-configured to use completion-style requests:
- `meta-llama/llama-4-scout:free`

Additional models will be automatically detected and added to this list as they're discovered.

## Error Handling

The fallback mechanism includes comprehensive error handling:
- Network timeouts
- JSON parsing errors
- HTTP errors
- Automatic retry with alternative format
- Detailed logging for debugging

## Headers

Completion-style requests include additional headers:
- `HTTP-Referer`: For site rankings on openrouter.ai
- `X-Title`: Site title for rankings

These can be customized by modifying the `_make_request` method in the `OpenRouterClient` class.