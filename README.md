# WO-380
# Automated IS Code Compliance Checker for Structural Design Drawings

## 🚀 Project Overview

Manual verification of structural design drawings for IS code compliance is a **tedious, error-prone, and time-consuming process.** This project brings cutting-edge automation to civil engineering workflows by transforming structural drawings (PDFs) into machine-checked compliance reports using document parsing, OCR, and intelligent rule engines.

> Imagine uploading your RCC slab drawing and—within moments—receiving a detailed report that highlights every conforming and non-conforming measurement, each one checked against the relevant Indian Standards (IS 456, IS 1786, IS 13920, and more). No more missed errors, no more guesswork—just **peace of mind and regulatory confidence**!

---

## 🔍 What Does This System Do?

- **Uploads Structural Design PDFs Straight from Your Desktop**
- **Parses and Extracts** critical information, including:
  - Dimensions, bar diameters, spacings
  - Reinforcement details, cover depths
  - Concrete and steel grades
- **Validates Every Parameter** against IS codes by:
  - Checking minimum/maximum values and formulas
  - Flagging any non-conformities with clear, actionable feedback
- **Generates Professional-Grade Compliance Reports** in seconds

---

## ✨ Why This Project Matters

- **Faster Design Approvals:** Slash the time from submission to regulatory approval.
- **Fewer Mistakes:** Minimize costly rework and site delays.
- **Enhanced Safety:** Ensure every drawing meets the highest standards of structural integrity.
- **First-of-its-Kind Automation:** Blends document AI, machine learning, and civil engineering knowledge.

---

## 🔧 Key Technologies

- **Python, OCR (Tesseract/EasyOCR/Google Vision), pdfplumber, PyMuPDF**
- **Natural Language Processing (spaCy, transformers)**
- **Custom Rule Engine for IS Codes**
- **Scalable Web Interface (React/Vue/Angular + FastAPI/Django)**

---

## 📈 Roadmap Highlights

- ✅ Upload PDFs & extract data
- ✅ Normalize measurements and parse drawing annotations
- ✅ Cross-reference every value with the latest IS code rulebook
- 🚧 Next: User feedback loop and machine learning-driven entity extraction
- 🚧 Future: Auto-correction suggestions, badge-based report sign-off

---
code for ... extracting data from pdf, dk if it works or not
claude gave it
someone please check it
(2110 21/8/25)

import PyPDF2
import fitz  # PyMuPDF
import cv2
import numpy as np
import pytesseract
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Union
import json
import logging
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractedParameter:
    name: str
    value: Optional[Union[float, str]]
    unit: Optional[str]
    context: str  # surrounding text for verification
    confidence: float  # confidence score (0-1)
    page_number: int
    coordinates: Optional[Tuple[float, float, float, float]] = None  # x1, y1, x2, y2

class PDFDataExtractor:
    """
    Comprehensive PDF data extractor for construction/building parameters
    Handles both text-based PDFs and scanned documents
    """
    
    def __init__(self):
        self.setup_patterns()
        
    def setup_patterns(self):
        """Define regex patterns for common construction parameters"""
        self.parameter_patterns = {
            # Dimensions
            'length': [
                r'length\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'L\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)\s*length'
            ],
            'width': [
                r'width\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'W\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)\s*width'
            ],
            'height': [
                r'height\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'H\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)\s*height'
            ],
            'thickness': [
                r'thickness\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'thick\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r't\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)'
            ],
            'diameter': [
                r'diameter\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'dia\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'ø\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'Φ\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)'
            ],
            
            # Structural parameters
            'concrete_strength': [
                r'concrete\s+strength\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mpa|psi|n/mm2)',
                r'fck\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mpa|psi|n/mm2)',
                r'f\'c\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mpa|psi|n/mm2)',
                r'compressive\s+strength\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mpa|psi|n/mm2)'
            ],
            'steel_grade': [
                r'steel\s+grade\s*[:\-=]\s*(\w+\d+)',
                r'reinforcement\s*[:\-=]\s*(\w+\d+)',
                r'rebar\s*[:\-=]\s*(\w+\d+)'
            ],
            'rebar_diameter': [
                r'rebar\s+diameter\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm)',
                r'bar\s+diameter\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm)',
                r'#(\d+)\s*bar',
                r'(\d+)mm\s*bar'
            ],
            'spacing': [
                r'spacing\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'c/c\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'center\s+to\s+center\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)'
            ],
            
            # Areas and volumes
            'area': [
                r'area\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(m2|sq\.m|sqm|ft2|sq\.ft)',
                r'(\d+(?:\.\d+)?)\s*(m2|sq\.m|sqm|ft2|sq\.ft)\s*area'
            ],
            'volume': [
                r'volume\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(m3|cu\.m|cum|ft3|cu\.ft)',
                r'(\d+(?:\.\d+)?)\s*(m3|cu\.m|cum|ft3|cu\.ft)\s*volume'
            ],
            
            # Loads
            'dead_load': [
                r'dead\s+load\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(kn/m2|kpa|psf|lb/ft2)',
                r'dl\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(kn/m2|kpa|psf|lb/ft2)'
            ],
            'live_load': [
                r'live\s+load\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(kn/m2|kpa|psf|lb/ft2)',
                r'll\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(kn/m2|kpa|psf|lb/ft2)'
            ],
            
            # Generic dimensions (x by y format)
            'dimensions': [
                r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)',
                r'(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in)'
            ]
        }
        
        # Material patterns
        self.material_patterns = [
            r'concrete\s+grade\s*[:\-=]\s*([A-Z]\d+)',
            r'cement\s+type\s*[:\-=]\s*([\w\s]+)',
            r'aggregate\s+size\s*[:\-=]\s*(\d+(?:\.\d+)?)\s*(mm)',
        ]
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, List[ExtractedParameter]]:
        """
        Main extraction function that handles both text and image-based PDFs
        """
        logger.info(f"Starting extraction from PDF: {pdf_path}")
        
        extracted_data = {
            'text_based': [],
            'ocr_based': [],
            'summary': {}
        }
        
        try:
            # First, try text-based extraction
            text_data = self.extract_text_based_data(pdf_path)
            extracted_data['text_based'] = text_data
            
            # Then, try OCR-based extraction for images/scanned content
            ocr_data = self.extract_ocr_based_data(pdf_path)
            extracted_data['ocr_based'] = ocr_data
            
            # Combine and deduplicate results
            extracted_data['summary'] = self.combine_and_deduplicate(text_data, ocr_data)
            
            logger.info(f"Extraction completed. Found {len(extracted_data['summary'])} unique parameters")
            
        except Exception as e:
            logger.error(f"Error during PDF extraction: {str(e)}")
            raise
        
        return extracted_data
    
    def extract_text_based_data(self, pdf_path: str) -> List[ExtractedParameter]:
        """Extract data from text-based PDF content"""
        extracted_params = []
        
        # Using PyMuPDF for better text extraction
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Get text blocks with positions
            text_dict = page.get_text("dict")
            
            # Extract plain text for pattern matching
            plain_text = page.get_text()
            
            # Apply pattern matching
            page_params = self.apply_patterns(plain_text, page_num + 1)
            
            # Try to get coordinates for text-based parameters
            for param in page_params:
                # Find approximate coordinates by searching text blocks
                param.coordinates = self.find_text_coordinates(text_dict, param.context)
            
            extracted_params.extend(page_params)
        
        doc.close()
        return extracted_params
    
    def extract_ocr_based_data(self, pdf_path: str) -> List[ExtractedParameter]:
        """Extract data using OCR on PDF images"""
        extracted_params = []
        
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Convert page to image
            mat = fitz.Matrix(2, 2)  # Increase resolution
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to OpenCV format
            image = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
            
            # Preprocess image for better OCR
            processed_image = self.preprocess_image(image)
            
            # Perform OCR
            ocr_text = pytesseract.image_to_string(processed_image)
            
            # Apply pattern matching to OCR text
            page_params = self.apply_patterns(ocr_text, page_num + 1)
            
            # Mark as OCR-based and adjust confidence
            for param in page_params:
                param.confidence *= 0.8  # Slightly reduce confidence for OCR
            
            extracted_params.extend(page_params)
        
        doc.close()
        return extracted_params
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Noise removal
        kernel = np.ones((1,1), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Dilation and erosion
        thresh = cv2.dilate(thresh, kernel, iterations=1)
        
        return thresh
    
    def apply_patterns(self, text: str, page_num: int) -> List[ExtractedParameter]:
        """Apply regex patterns to extract parameters"""
        extracted_params = []
        text_lower = text.lower()
        
        for param_name, patterns in self.parameter_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    try:
                        # Handle different pattern structures
                        groups = match.groups()
                        
                        if param_name == 'dimensions' and len(groups) >= 3:
                            # Special handling for dimension patterns (length x width)
                            value1, value2, unit = groups[0], groups[1], groups[2]
                            
                            # Create two separate parameters
                            extracted_params.append(ExtractedParameter(
                                name=f"{param_name}_length",
                                value=float(value1),
                                unit=unit.lower(),
                                context=self.get_context(text, match.start(), match.end()),
                                confidence=0.9,
                                page_number=page_num
                            ))
                            
                            extracted_params.append(ExtractedParameter(
                                name=f"{param_name}_width",
                                value=float(value2),
                                unit=unit.lower(),
                                context=self.get_context(text, match.start(), match.end()),
                                confidence=0.9,
                                page_number=page_num
                            ))
                        
                        elif len(groups) >= 2:
                            # Standard value-unit pattern
                            value_str, unit = groups[0], groups[1] if len(groups) > 1 else ""
                            
                            # Try to convert to float, keep as string if it fails
                            try:
                                value = float(value_str)
                            except ValueError:
                                value = value_str
                            
                            extracted_params.append(ExtractedParameter(
                                name=param_name,
                                value=value,
                                unit=unit.lower() if unit else None,
                                context=self.get_context(text, match.start(), match.end()),
                                confidence=0.9,
                                page_number=page_num
                            ))
                    
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error processing match for {param_name}: {e}")
                        continue
        
        return extracted_params
    
    def get_context(self, text: str, start: int, end: int, context_length: int = 50) -> str:
        """Get surrounding context for a match"""
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        return text[context_start:context_end].strip()
    
    def find_text_coordinates(self, text_dict: dict, search_text: str) -> Optional[Tuple[float, float, float, float]]:
        """Find approximate coordinates of text in the page"""
        # This is a simplified implementation
        # In practice, you might need more sophisticated text matching
        search_words = search_text.lower().split()[:3]  # Use first 3 words
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        line_text += span["text"].lower() + " "
                    
                    if any(word in line_text for word in search_words):
                        bbox = line["bbox"]  # [x0, y0, x1, y1]
                        return bbox
        
        return None
    
    def combine_and_deduplicate(self, text_data: List[ExtractedParameter], 
                               ocr_data: List[ExtractedParameter]) -> Dict[str, ExtractedParameter]:
        """Combine results from text and OCR extraction, removing duplicates"""
        combined = {}
        
        # Process text-based data first (higher confidence)
        for param in text_data:
            key = f"{param.name}_{param.page_number}"
            combined[key] = param
        
        # Add OCR data only if not already found in text-based extraction
        for param in ocr_data:
            key = f"{param.name}_{param.page_number}"
            if key not in combined:
                # Check for similar parameters with different confidence
                similar_found = False
                for existing_key, existing_param in combined.items():
                    if (existing_param.name == param.name and 
                        existing_param.page_number == param.page_number and
                        abs(float(existing_param.value or 0) - float(param.value or 0)) < 0.1):
                        similar_found = True
                        break
                
                if not similar_found:
                    combined[key] = param
        
        return combined
    
    def export_to_json(self, extracted_data: Dict[str, any], output_path: str) -> None:
        """Export extracted data to JSON format"""
        # Convert ExtractedParameter objects to dictionaries
        json_data = {
            'text_based': [param.__dict__ for param in extracted_data['text_based']],
            'ocr_based': [param.__dict__ for param in extracted_data['ocr_based']],
            'summary': {k: v.__dict__ for k, v in extracted_data['summary'].items()}
        }
        
        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        logger.info(f"Data exported to {output_path}")
    
    def generate_report(self, extracted_data: Dict[str, any]) -> str:
        """Generate a human-readable report of extracted data"""
        report = "PDF Data Extraction Report\n"
        report += "=" * 50 + "\n\n"
        
        summary = extracted_data['summary']
        
        if not summary:
            report += "No parameters found in the PDF.\n"
            return report
        
        # Group by parameter type
        grouped = {}
        for key, param in summary.items():
            param_type = param.name.split('_')[0]
            if param_type not in grouped:
                grouped[param_type] = []
            grouped[param_type].append(param)
        
        for param_type, params in grouped.items():
            report += f"\n{param_type.upper()} PARAMETERS:\n"
            report += "-" * 30 + "\n"
            
            for param in params:
                report += f"Parameter: {param.name}\n"
                report += f"Value: {param.value} {param.unit or ''}\n"
                report += f"Page: {param.page_number}\n"
                report += f"Confidence: {param.confidence:.2f}\n"
                report += f"Context: {param.context[:100]}...\n"
                report += "\n"
        
        return report

# Example usage function
def extract_pdf_data(pdf_path: str, output_json: str = None) -> Dict[str, any]:
    """
    Main function to extract data from a PDF
    
    Args:
        pdf_path: Path to the PDF file
        output_json: Optional path to save JSON output
    
    Returns:
        Dictionary containing extracted parameters
    """
    extractor = PDFDataExtractor()
    
    try:
        # Extract data
        extracted_data = extractor.extract_from_pdf(pdf_path)
        
        # Generate and print report
        report = extractor.generate_report(extracted_data)
        print(report)
        
        # Save to JSON if requested
        if output_json:
            extractor.export_to_json(extracted_data, output_json)
        
        return extracted_data
    
    except Exception as e:
        logger.error(f"Failed to extract data from PDF: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    pdf_file = "construction_drawing.pdf"  # Replace with your PDF path
    
    try:
        data = extract_pdf_data(pdf_file, "extracted_data.json")
        
        print(f"\nSummary: Found {len(data['summary'])} unique parameters")
        for key, param in data['summary'].items():
            print(f"- {param.name}: {param.value} {param.unit or ''}")
    
    except FileNotFoundError:
        print("PDF file not found. Please provide a valid PDF path.")
    except Exception as e:
        print(f"Error: {str(e)}")
## 🌟 Get Involved!

This project is **brand new**—so your feedback, ideas, and code contributions have an outsized impact. Together, let’s make manual compliance checks a thing of the past and set a new bar for engineering efficiency and safety.

> **Ready to transform civil engineering with automation? [Get started now!]**
