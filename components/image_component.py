import requests
import cv2
import numpy as np
import pytesseract
import os
from pytesseract import TesseractNotFoundError

class ImageComponent:

    def image_to_text(image_url: str) -> list[str]:
        try:
            # Fetch the image content
            response = requests.get(image_url)
            response.raise_for_status()

            # Convert image content to a NumPy array
            image_array = np.frombuffer(response.content, np.uint8)

            # Decode the image using OpenCV
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            # Convert to grayscale if needed
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Use Pytesseract to extract text
            pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_CMD_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
            extracted_text = pytesseract.image_to_string(gray_image)

            # Return the extracted text as a list of lines
            return extracted_text.splitlines()

        except TesseractNotFoundError:
            print("Tesseract is not installed or not found. Please install Tesseract.")
            return []  # Return an empty list in case Tesseract is not found

        except requests.RequestException as e:
            print(f"Error fetching the image: {e}")
            return []  # Handle network-related errors

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []  # Handle any other errors
        # Split text into lines
        #lines = extracted_text.split("\n")

        # Add line numbers
        #return [f"{i + 1}: {line}" for i, line in enumerate(lines)]