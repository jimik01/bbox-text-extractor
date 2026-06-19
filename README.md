# BBox Text Extractor

Interactive bounding box annotation and text extraction tool with **normalized coordinates** for scale-invariant document processing.

## Features

✅ **Normalized Coordinates (0.0-1.0)** - Works on any image size  
✅ **Interactive Annotation UI** - Mouse-driven with OpenCV  
✅ **Scale-Invariant** - Same bboxes work on enlarged or reduced images  
✅ **Dual OCR Engines** - Tesseract or PaddleOCR support  
✅ **Batch Processing** - Process multiple documents efficiently  
✅ **JSON Export** - Store field definitions for reuse  

## Installation

```bash
pip install opencv-python pytesseract pillow paddleocr
```

### For Tesseract OCR:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer: https://github.com/UB-Mannheim/tesseract/wiki

## Quick Start

### Phase 1: Define Bounding Boxes

Annotate field locations on a template image:

```python
from bbox_extractor import BBoxAnnotator

annotator = BBoxAnnotator()
annotator.define_bboxes('template_invoice.jpg', 'invoice_bboxes.json')
```

**Controls:**
- **Click twice** to define a bounding box (top-left, then bottom-right)
- **Type field name** when prompted
- **Press 'u'** to undo last bbox
- **Press 'q'** to finish

### Phase 2: Extract Text from Any Image Size

Reuse the same bboxes on images of different sizes:

```python
from bbox_extractor import TextExtractor

extractor = TextExtractor('invoice_bboxes.json')

# Single image (works on any size)
results = extractor.extract_text('invoice_2400x1600.jpg')
print(results)
# Output: {'invoice_number': '12345', 'date': '2024-01-15', ...}

# Batch processing
results = extractor.extract_text_batch([
    'invoice_1.jpg',
    'invoice_2_small.jpg',  # Different size
    'invoice_3_large.jpg',  # Different size
])
```

## How It Works

### Normalized Coordinates

Bounding boxes are stored as normalized coordinates (0.0 to 1.0) relative to the image dimensions:

```json
{
  "image_width": 1200,
  "image_height": 800,
  "bboxes": {
    "invoice_number": {
      "x1": 0.1,
      "y1": 0.05,
      "x2": 0.4,
      "y2": 0.15
    }
  }
}
```

When processing a 2400x1600 image:
- `x1: 0.1` → `240 pixels`
- `x2: 0.4` → `960 pixels`
- (automatically scaled)

## API Reference

### NormalizedBBox

```python
class NormalizedBBox:
    x1: float  # 0.0 to 1.0
    y1: float  # 0.0 to 1.0
    x2: float  # 0.0 to 1.0
    y2: float  # 0.0 to 1.0
    
    # Convert to pixel coordinates for specific image
    to_pixel_coords(img_width: int, img_height: int) -> Tuple[int, int, int, int]
    
    # Convert from pixel coordinates
    from_pixel_coords(x1, y1, x2, y2, img_width, img_height) -> NormalizedBBox
```

### BBoxAnnotator

```python
class BBoxAnnotator:
    def define_bboxes(image_path: str, output_file: str = 'bboxes.json')
        """Interactive annotation tool"""
```

### TextExtractor

```python
class TextExtractor:
    def __init__(bboxes_file: str = 'bboxes.json')
    
    def extract_text(image_path: str, engine: str = 'tesseract') -> Dict[str, str]
        """Extract text from single image"""
    
    def extract_text_batch(image_paths: list, engine: str = 'tesseract') -> Dict
        """Extract text from multiple images"""
```

## Example Output

```python
{
    'invoice_number': 'INV-2024-001234',
    'date': '01/15/2024',
    'customer_name': 'John Doe',
    'amount': '$1,250.00'
}
```

## Use Cases

- 📄 **Document OCR** - Extract fields from invoices, forms, receipts
- 🏦 **Banking** - Process checks, statements, contracts
- 📋 **Data Entry** - Automate form processing
- 📸 **Document Scanning** - Handle variable image sizes from different scanners

## Performance

- **Annotation:** ~2-3 fields per minute (interactive)
- **Extraction:** ~0.5-1s per image (Tesseract), ~2-3s (PaddleOCR)
- **Memory:** ~50MB for typical document processing

## Troubleshooting

**Tesseract not found:**
```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Poor OCR results:**
- Use `engine='paddleocr'` for better accuracy
- Preprocess image with `cv2.adaptiveThreshold()` for low-contrast scans
- Increase image resolution before OCR

## License

MIT
