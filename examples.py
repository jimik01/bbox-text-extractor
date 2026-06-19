"""Example usage of BBoxAnnotator and TextExtractor"""

from bbox_extractor import BBoxAnnotator, TextExtractor, NormalizedBBox
import json

# ============= EXAMPLE 1: Create bounding boxes =============

def example_annotate():
    """
    Run interactive annotation on a template image.
    Define field locations once, reuse on any image size.
    """
    annotator = BBoxAnnotator()
    
    # This launches an interactive window
    # Click to define each field, press 'q' when done
    annotator.define_bboxes(
        'templates/invoice.jpg',
        'configs/invoice_bboxes.json'
    )
    
    # Output: invoice_bboxes.json with normalized coordinates


# ============= EXAMPLE 2: Extract from single image =============

def example_extract_single():
    """
    Extract text from a single document using stored bboxes.
    Works regardless of image size.
    """
    extractor = TextExtractor('configs/invoice_bboxes.json')
    
    # Works on original size
    results = extractor.extract_text('scans/invoice_1200x800.jpg')
    print("Original size (1200x800):")
    print(results)
    print()
    
    # Works on enlarged scan
    results = extractor.extract_text('scans/invoice_2400x1600.jpg')
    print("Enlarged scan (2400x1600):")
    print(results)
    print()
    
    # Works on reduced scan
    results = extractor.extract_text('scans/invoice_600x400.jpg')
    print("Reduced scan (600x400):")
    print(results)


# ============= EXAMPLE 3: Batch processing =============

def example_batch_extract():
    """
    Process multiple documents at once.
    Useful for automated data entry workflows.
    """
    extractor = TextExtractor('configs/invoice_bboxes.json')
    
    invoice_files = [
        'scans/invoice_001.jpg',
        'scans/invoice_002.jpg',
        'scans/invoice_003.jpg',
    ]
    
    # Extract from all files
    batch_results = extractor.extract_text_batch(invoice_files)
    
    # Save results to CSV or database
    for file_path, extracted_data in batch_results.items():
        print(f"\n{file_path}:")
        print(json.dumps(extracted_data, indent=2))


# ============= EXAMPLE 4: Using PaddleOCR for better accuracy =============

def example_extract_with_paddleocr():
    """
    Use PaddleOCR instead of Tesseract for better accuracy.
    Slower but more accurate on complex documents.
    """
    extractor = TextExtractor('configs/invoice_bboxes.json')
    
    results = extractor.extract_text(
        'scans/invoice_complex.jpg',
        engine='paddleocr'  # Use PaddleOCR
    )
    
    print("Extracted with PaddleOCR:")
    print(json.dumps(results, indent=2))


# ============= EXAMPLE 5: Working with normalized coordinates directly =============

def example_normalized_coords():
    """
    Advanced: manually create and convert normalized coordinates.
    """
    # Create a normalized bbox (represents top-left 30% of image)
    bbox = NormalizedBBox(x1=0.0, y1=0.0, x2=0.3, y2=0.3)
    
    # Convert to pixel coordinates for different image sizes
    print("\n=== Normalized Coordinate Conversion ===")
    print(f"Normalized bbox: {bbox}")
    print()
    
    # 800x600 image
    x1, y1, x2, y2 = bbox.to_pixel_coords(800, 600)
    print(f"800x600 image:   pixels = ({x1}, {y1}, {x2}, {y2})")
    
    # 1600x1200 image (2x larger)
    x1, y1, x2, y2 = bbox.to_pixel_coords(1600, 1200)
    print(f"1600x1200 image: pixels = ({x1}, {y1}, {x2}, {y2})")
    
    # 400x300 image (2x smaller)
    x1, y1, x2, y2 = bbox.to_pixel_coords(400, 300)
    print(f"400x300 image:   pixels = ({x1}, {y1}, {x2}, {y2})")


# ============= EXAMPLE 6: Custom post-processing =============

def example_custom_processing():
    """
    Extract text and apply custom post-processing.
    Useful for cleaning up OCR results.
    """
    extractor = TextExtractor('configs/invoice_bboxes.json')
    results = extractor.extract_text('scans/invoice.jpg')
    
    # Clean and validate extracted data
    cleaned = {}
    for field, text in results.items():
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Field-specific cleaning
        if field == 'amount':
            # Keep only digits and decimal
            text = ''.join(c for c in text if c.isdigit() or c == '.')
        elif field == 'date':
            # Remove non-date characters
            text = ''.join(c for c in text if c.isdigit() or c in '/-')
        
        cleaned[field] = text
    
    print("\nCleaned results:")
    print(json.dumps(cleaned, indent=2))


if __name__ == '__main__':
    # Uncomment to run examples
    # example_annotate()
    # example_extract_single()
    # example_batch_extract()
    # example_extract_with_paddleocr()
    example_normalized_coords()
    # example_custom_processing()
