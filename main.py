from dotenv import load_dotenv
from pdf_to_image import pdf_to_image
from gemini_vision import analyse_image
from prompt import prompt1
import os
from datetime import datetime

# Load API key from .env
load_dotenv()

# Step 1: Convert PDF page to image
pdf_path = "1st floor Slab details.pdf"  # Change file name here
image_path = "1st floor Slab details.jpg"  # Use JPG for ConvertAPI

try:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    image_path = pdf_to_image(pdf_path, image_path, page_number=1, zoom=2)
    print(f"✅ PDF converted to image: {image_path}")
except Exception as e:
    print(f"❌ Error converting PDF to image: {e}")
    exit(1)

# Step 2: Check if API key is available
if not os.getenv("GEMINI_API_KEY"):
    print("\n⚠️ GEMINI_API_KEY not found in environment variables.")
    print("To use Gemini Vision AI analysis, please:")
    print("1. Get a Gemini API key from https://makersuite.google.com/app/apikey")
    print("2. Create a .env file with: GEMINI_API_KEY=your_api_key_here")
    print("3. Or set the environment variable: export GEMINI_API_KEY=your_api_key_here")
    print(f"\n📄 Image file created successfully: {image_path}")
    print("You can manually view this image to see the PDF content.")
    exit(1)

# Step 3: Analyse with Gemini Vision
try:
    result = analyse_image(image_path, prompt1)
    print("\n📄 Gemini Vision Response:\n", result)
    
    # Step 4: Save extracted data to markdown file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_filename = f"extracted_data_{timestamp}.md"
    
    with open(md_filename, 'w', encoding='utf-8') as md_file:
        md_file.write(f"# Data Extraction Report\n\n")
        md_file.write(f"**Source PDF:** {pdf_path}\n")
        md_file.write(f"**Extraction Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_file.write(f"**Generated Image:** {image_path}\n\n")
        md_file.write("---\n\n")
        md_file.write(result)
    
    print(f"\n💾 Extracted data saved to: {md_filename}")
    
except Exception as e:
    print(f"\n❌ Error calling Gemini API: {e}")
    print(f"📄 Image file created successfully: {image_path}")