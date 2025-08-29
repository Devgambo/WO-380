import base64
import os
import requests
import json

def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def analyse_image(image_path, prompt):
    """Analyze the image using Grok Vision API via OpenRouter."""
    base64_image = encode_image(image_path)
    if base64_image is None:
        raise ValueError("Failed to encode the image.")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/your-username/your-repo",  # Optional
        "X-Title": "PDF Data Extraction Tool",  # Optional
    }
    
    data = {
        "model": "x-ai/grok-4",
        "max_tokens": 8000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        print(f"Making API call to: {url}")
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            response.raise_for_status()
        
        result = response.json()
        print("API call successful!")
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise RuntimeError(f"Error calling OpenRouter API: {e}")
    except KeyError as e:
        print(f"Key error in response: {e}")
        print(f"Response content: {result}")
        raise RuntimeError(f"Unexpected response format from API: {e}")
    except Exception as e:
        print(f"General error: {e}")
        raise RuntimeError(f"Error processing API response: {e}")