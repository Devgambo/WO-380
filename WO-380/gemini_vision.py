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
    """Analyze the image using Gemini Vision API directly."""
    base64_image = encode_image(image_path)
    if base64_image is None:
        raise ValueError("Failed to encode the image.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 12000,  # Higher token limit for more detailed responses
            "temperature": 0.1,  # Lower temperature for more focused responses
            "topP": 0.8,
            "topK": 40
        }
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
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise RuntimeError(f"Error calling Gemini API: {e}")
    except KeyError as e:
        print(f"Key error in response: {e}")
        print(f"Response content: {result}")
        raise RuntimeError(f"Unexpected response format from API: {e}")
    except Exception as e:
        print(f"General error: {e}")
        raise RuntimeError(f"Error processing API response: {e}")