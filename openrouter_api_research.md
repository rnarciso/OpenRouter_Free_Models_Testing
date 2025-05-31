# OpenRouter API Research

## Overview
OpenRouter provides a unified API that gives access to over 300 AI models through a single endpoint. It offers automatic model fallbacks, routing, and supports text-based AI models from various providers.

## Free Models Available on OpenRouter API

Based on direct API calls, OpenRouter offers 58 free models (as of April 2025). Here are some notable ones:

1. **NVIDIA Models**:
   - Llama 3.1 Nemotron Nano 8B v1
   - Llama 3.1 Nemotron Ultra 253B v1
   - Llama 3.3 Nemotron Super 49B v1
   - Llama 3.1 Nemotron 70B Instruct

2. **Meta Models**:
   - Llama 4 Maverick
   - Llama 4 Scout
   - Llama 3.3 70B Instruct
   - Llama 3.2 (1B, 3B, 11B Vision) Instruct
   - Llama 3.1 8B Instruct

3. **Google Models**:
   - Gemini 2.5 Pro Experimental
   - Gemini 2.0 Flash Thinking Experimental
   - Gemini 2.0 Flash Experimental
   - Gemma 3 (1B, 4B, 12B, 27B)
   - Gemma 2 9B

4. **DeepSeek Models**:
   - DeepSeek V3 Base
   - DeepSeek V3 0324
   - DeepSeek R1
   - DeepSeek R1 Zero
   - DeepSeek R1 Distill variants

5. **Qwen Models**:
   - Qwen2.5 VL (3B, 7B, 32B, 72B) Instruct
   - Qwen2.5 7B Instruct
   - Qwen2.5 72B Instruct
   - QwQ 32B

6. **Mistral Models**:
   - Mistral Small 3.1 24B
   - Mistral Small 3
   - Mistral Nemo
   - Mistral 7B Instruct

7. **Other Notable Free Models**:
   - Moonshot AI: Kimi VL A3B Thinking
   - Optimus Alpha
   - Quasar Alpha
   - Reka: Flash 3
   - AllenAI: Molmo 7B D
   - Hugging Face: Zephyr 7B

## API Usage with Python

### Basic API Structure

1. **API Endpoints**:
   - Base URL: `https://openrouter.ai/api/v1`
   - Models endpoint: `GET /models`
   - Chat completion endpoint: `POST /chat/completions`
   - Key information: `GET /auth/key`

2. **Authentication**:
   ```python
   headers = {
       "Authorization": f"Bearer {api_key}",
       "HTTP-Referer": "https://your-site.example.com",  # Required by OpenRouter
       "Content-Type": "application/json"
   }
   ```

3. **Request Format for Chat Completions**:
   ```python
   payload = {
       "model": "model_id",  # e.g., "moonshotai/kimi-vl-a3b-thinking:free"
       "messages": [
           {"role": "system", "content": "You are a helpful assistant."},
           {"role": "user", "content": "Hello, what model are you?"}
       ]
   }
   ```

4. **Response Structure**:
   ```json
   {
     "id": "gen-1744324582-0M54dHRkebI5ZBG3vA3h",
     "provider": "Chutes",
     "model": "moonshotai/kimi-vl-a3b-thinking",
     "object": "chat.completion",
     "created": 1744324582,
     "choices": [
       {
         "logprobs": null,
         "finish_reason": "stop",
         "native_finish_reason": "stop",
         "index": 0,
         "message": {
           "role": "assistant",
           "content": "Hello! I'm here to provide helpful, respectful, and accurate information to the best of my ability. How can I assist you today? 😊",
           "refusal": null,
           "reasoning": null
         }
       }
     ],
     "usage": {
       "prompt_tokens": 24,
       "completion_tokens": 321,
       "total_tokens": 345
     }
   }
   ```

### Complete Python Example

```python
import requests
import time

# API key
api_key = "your_api_key_here"

# Get list of available models
def get_models():
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://your-site.example.com"
    }
    
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

# Make a chat completion request
def chat_completion(model_id, messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://your-site.example.com",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_id,
        "messages": messages
    }
    
    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    end_time = time.time()
    
    response_time = end_time - start_time
    
    if response.status_code == 200:
        result = response.json()
        return result, response_time
    else:
        return None, response_time

# Get API key information
def get_key_info():
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://your-site.example.com"
    }
    
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None
```

## Token Usage Tracking and Response Time Measurement

1. **Token Usage Tracking**:
   - The API response includes a `usage` object with token counts:
     ```json
     "usage": {
       "prompt_tokens": 24,
       "completion_tokens": 321,
       "total_tokens": 345
     }
     ```
   - You can track cumulative usage by summing these values across requests

2. **API Key Information**:
   - The `/api/v1/auth/key` endpoint provides information about your API key:
     ```json
     {
       "data": {
         "label": "sk-or-v1-134...2f1",
         "limit": null,
         "usage": 0,
         "is_provisioning_key": false,
         "limit_remaining": null,
         "is_free_tier": true,
         "rate_limit": {
           "requests": 10,
           "interval": "10s"
         }
       }
     }
     ```
   - This shows if your key is on the free tier and any rate limits

3. **Response Time Measurement**:
   - You can measure response time by recording timestamps before and after API calls:
     ```python
     start_time = time.time()
     response = requests.post(url, headers=headers, json=payload)
     end_time = time.time()
     response_time = end_time - start_time
     ```

4. **Activity Page**:
   - OpenRouter provides an Activity page where you can view historic usage
   - You can filter usage by model, provider, and API key

## Pricing Structure

OpenRouter models fall into different pricing categories:

1. **Free Models (0 cost)**: 58 models with no charge for usage
2. **Very Low Cost Models (≤0.0001)**: 233 models with minimal pricing
3. **Low Cost Models (≤0.001)**: 4 models
4. **Medium and High Cost Models**: Available but fewer in number

## Additional Notes

1. **Rate Limits**:
   - Free tier has rate limits (e.g., 10 requests per 10 seconds)
   - These limits are returned in the key information response

2. **Context Length**:
   - Models have varying context lengths, from 4,096 to over 1,000,000 tokens
   - Free models like Llama 4 Scout support up to 512,000 tokens

3. **Model Selection**:
   - When using the API, specify the exact model ID (e.g., `moonshotai/kimi-vl-a3b-thinking:free`)
   - Adding `:free` suffix typically indicates the free version of a model