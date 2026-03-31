import os
import base64
import httpx
import litellm
from typing import Optional

# Set litellm to not print verbose logs
litellm.suppress_debug_info = True

async def extract_image_description(image_url: str, prompt: str = "Describe this image in detail.") -> Optional[str]:
    """
    Use a multimodal model via litellm to extract description from an image URL.
    """
    model = os.getenv("VLM_MODEL", "gemini/gemini-3-flash-preview")
    
    # Download the image and encode as base64
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            # Telegram photos are typically JPEGs
            data_url = f"data:image/jpeg;base64,{base64_image}"
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": data_url,
                    },
                },
            ],
        }
    ]
    
    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error extracting image description: {e}")
        return None
