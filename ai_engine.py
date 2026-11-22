
import os
import time
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

# Connect to Gemini
client = genai.Client(api_key=api_key) if api_key else None


def generate_content(prompt):

    if not client:
        return "Error: Gemini API key not found. Check your .env file."

    # Try generating content up to 3 times
    for attempt in range(3):

        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )

            return response.text or "No content was generated."

        except Exception as e:

            error_message = str(e)

            # Retry if Gemini is temporarily unavailable
            if "503" in error_message or "UNAVAILABLE" in error_message:

                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue

                return (
                    "Gemini is currently experiencing high demand. "
                    "Please wait a few minutes and try again."
                )

            return f"Error generating content: {error_message}"

    return "Unable to generate content. Please try again later."
