import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import matplotlib.pyplot as plt

class PDFDrawingPreprocessor:
    def __init__(self, input_folder="files", output_folder="processed_images"):
        self.input_folder = input_folder
        self.output_folder = output_folder
        
        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
    
    def pdf_to_high_quality_images(self, pdf_path, dpi=300):
        """
        Convert PDF to high-quality images
        """
        try:
            # Convert PDF to images with high DPI
            images = convert_from_path(pdf_path, dpi=dpi)
            return images
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            return None
    
    def detect_drawing_boundaries(self, image):
        """
        Detect the main drawing area by finding the largest rectangular region
        """
        # Convert PIL to OpenCV format
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest rectangular contour (likely the drawing border)
        largest_area = 0
        best_rect = None
        
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's roughly rectangular (4 corners)
            if len(approx) >= 4:
                area = cv2.contourArea(contour)
                if area > largest_area:
                    largest_area = area
                    x, y, w, h = cv2.boundingRect(contour)
                    best_rect = (x, y, w, h)
        
        # If no good rectangle found, use conservative crop
        if best_rect is None:
            h, w = gray.shape
            margin_x = int(w * 0.05)  # 5% margin from sides
            margin_y = int(h * 0.05)  # 5% margin from top/bottom
            best_rect = (margin_x, margin_y, w - 2*margin_x, h - 2*margin_y)
        
        return best_rect
    
    def crop_drawing_area(self, image):
        """
        Crop the image to keep only the drawing area
        """
        # Detect boundaries
        x, y, w, h = self.detect_drawing_boundaries(image)
        
        # Crop the image
        cropped = image.crop((x, y, x + w, y + h))
        
        return cropped, (x, y, w, h)
    
    def detect_grid_lines(self, image):
        """
        Detect gray grid lines to help with division
        """
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
        
        return horizontal_lines, vertical_lines
    
    def divide_into_grid(self, image, rows=3, cols=3):
        """
        Divide the cropped image into a 3x3 grid
        """
        width, height = image.size
        
        # Calculate grid dimensions
        grid_width = width // cols
        grid_height = height // rows
        
        grid_images = []
        
        for row in range(rows):
            for col in range(cols):
                # Calculate crop coordinates
                left = col * grid_width
                top = row * grid_height
                right = left + grid_width
                bottom = top + grid_height
                
                # For the last column/row, extend to the edge to avoid missing pixels
                if col == cols - 1:
                    right = width
                if row == rows - 1:
                    bottom = height
                
                # Crop the grid cell
                grid_cell = image.crop((left, top, right, bottom))
                grid_images.append(grid_cell)
        
        return grid_images
    
    def process_single_pdf(self, pdf_filename):
        """
        Process a single PDF file
        """
        pdf_path = os.path.join(self.input_folder, pdf_filename)
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return
        
        print(f"Processing {pdf_filename}...")
        
        # Convert PDF to high-quality images
        images = self.pdf_to_high_quality_images(pdf_path)
        
        if images is None:
            return
        
        # Process each page
        for page_num, image in enumerate(images):
            print(f"Processing page {page_num + 1}...")
            
            # Crop to drawing area
            cropped_image, crop_info = self.crop_drawing_area(image)
            
            # Save the cropped full image
            base_name = os.path.splitext(pdf_filename)[0]
            cropped_path = os.path.join(self.output_folder, f"{base_name}_page_{page_num+1}_cropped.png")
            cropped_image.save(cropped_path, "PNG", quality=95)
            print(f"Saved cropped image: {cropped_path}")
            
            # Divide into 3x3 grid
            grid_images = self.divide_into_grid(cropped_image)
            
            # Save grid images
            for i, grid_img in enumerate(grid_images):
                row = i // 3
                col = i % 3
                grid_path = os.path.join(self.output_folder, 
                                       f"{base_name}_page_{page_num+1}_grid_{row+1}_{col+1}.png")
                grid_img.save(grid_path, "PNG", quality=95)
                print(f"Saved grid image: {grid_path}")
            
            print(f"Page {page_num + 1} processed successfully!")
    
    def process_all_pdfs(self):
        """
        Process all PDF files in the input folder
        """
        if not os.path.exists(self.input_folder):
            print(f"Input folder '{self.input_folder}' not found!")
            return
        
        pdf_files = [f for f in os.listdir(self.input_folder) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"No PDF files found in '{self.input_folder}' folder!")
            return
        
        print(f"Found {len(pdf_files)} PDF files to process...")
        
        for pdf_file in pdf_files:
            try:
                self.process_single_pdf(pdf_file)
                print(f"✓ Successfully processed {pdf_file}")
            except Exception as e:
                print(f"✗ Error processing {pdf_file}: {e}")
    
    def visualize_processing_steps(self, pdf_filename, page_num=0):
        """
        Visualize the processing steps for debugging
        """
        pdf_path = os.path.join(self.input_folder, pdf_filename)
        images = self.pdf_to_high_quality_images(pdf_path)
        
        if images is None or page_num >= len(images):
            print("Cannot load image for visualization")
            return
        
        original_image = images[page_num]
        cropped_image, crop_info = self.crop_drawing_area(original_image)
        grid_images = self.divide_into_grid(cropped_image)
        
        # Create visualization
        fig, axes = plt.subplots(2, 5, figsize=(20, 8))
        
        # Original image
        axes[0, 0].imshow(original_image)
        axes[0, 0].set_title('Original PDF Page')
        axes[0, 0].axis('off')
        
        # Cropped image
        axes[0, 1].imshow(cropped_image)
        axes[0, 1].set_title('Cropped Drawing Area')
        axes[0, 1].axis('off')
        
        # Show crop boundaries on original
        img_with_crop = original_image.copy()
        # This is just for visualization - you'd need to draw the rectangle
        axes[0, 2].imshow(img_with_crop)
        axes[0, 2].set_title('Crop Boundaries')
        axes[0, 2].axis('off')
        
        # Hide unused subplot
        axes[0, 3].axis('off')
        axes[0, 4].axis('off')
        
        # Show first 5 grid images
        for i in range(min(5, len(grid_images))):
            axes[1, i].imshow(grid_images[i])
            row = i // 3
            col = i % 3
            axes[1, i].set_title(f'Grid {row+1},{col+1}')
            axes[1, i].axis('off')
        
        plt.tight_layout()
        plt.show()

# Example usage
if __name__ == "__main__":
    # Initialize the preprocessor
    preprocessor = PDFDrawingPreprocessor(
        input_folder="files",           # Folder containing PDF files
        output_folder="processed_images" # Output folder for processed images
    )
    
    # Process all PDFs in the folder
    preprocessor.process_all_pdfs()
    
    # Optional: Visualize processing steps for debugging
    # Uncomment the lines below to see the processing steps
    # pdf_files = [f for f in os.listdir("files") if f.lower().endswith('.pdf')]
    # if pdf_files:
    #     preprocessor.visualize_processing_steps(pdf_files[0])