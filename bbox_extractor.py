import cv2
import pytesseract
from PIL import Image
import json
from dataclasses import dataclass
from typing import Tuple, Dict

@dataclass
class NormalizedBBox:
    """Represents a bounding box in normalized coordinates (0.0 to 1.0)"""
    x1: float  # 0.0 to 1.0
    y1: float  # 0.0 to 1.0
    x2: float  # 0.0 to 1.0
    y2: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict:
        return {'x1': self.x1, 'y1': self.y1, 'x2': self.x2, 'y2': self.y2}
    
    @classmethod
    def from_dict(cls, d: Dict):
        return cls(**d)
    
    def to_pixel_coords(self, img_width: int, img_height: int) -> Tuple[int, int, int, int]:
        """Convert normalized coords to pixel coords for a specific image size"""
        return (
            int(self.x1 * img_width),
            int(self.y1 * img_height),
            int(self.x2 * img_width),
            int(self.y2 * img_height)
        )
    
    @classmethod
    def from_pixel_coords(cls, x1: int, y1: int, x2: int, y2: int, 
                         img_width: int, img_height: int):
        """Convert pixel coords to normalized coords"""
        return cls(
            x1=x1 / img_width,
            y1=y1 / img_height,
            x2=x2 / img_width,
            y2=y2 / img_height
        )


class BBoxAnnotator:
    """Interactive annotation tool with normalized coordinates"""
    
    def __init__(self):
        self.bboxes: Dict[str, NormalizedBBox] = {}
        self.current_bbox = []
        self.img = None
        self.img_original = None
        self.img_width = None
        self.img_height = None
    
    def define_bboxes(self, image_path: str, output_file: str = 'bboxes.json'):
        """
        Interactive bbox annotation. Click twice to define a bbox.
        Format: top-left click, then bottom-right click.
        """
        self.img_original = cv2.imread(image_path)
        self.img = self.img_original.copy()
        self.img_height, self.img_width = self.img.shape[:2]
        
        cv2.namedWindow('Define Bboxes (click 2x per bbox)')
        cv2.setMouseCallback('Define Bboxes', self._mouse_callback)
        
        print(f"Image dimensions: {self.img_width}x{self.img_height}")
        print("Instructions:")
        print("  - Click 2 times to define a bounding box")
        print("  - Press 'u' to undo last bbox")
        print("  - Press 'q' to finish")
        
        cv2.imshow('Define Bboxes (click 2x per bbox)', self.img)
        
        while True:
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('u'):
                if self.bboxes:
                    last_field = list(self.bboxes.keys())[-1]
                    del self.bboxes[last_field]
                    print(f"Removed: {last_field}")
                    self.img = self.img_original.copy()
                    self._redraw_bboxes()
                    cv2.imshow('Define Bboxes (click 2x per bbox)', self.img)
        
        cv2.destroyAllWindows()
        self._save_bboxes(output_file)
    
    def _mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_bbox.append((x, y))
            
            if len(self.current_bbox) == 1:
                # Draw circle at first point
                cv2.circle(self.img, (x, y), 5, (0, 255, 0), -1)
                cv2.imshow('Define Bboxes (click 2x per bbox)', self.img)
            
            elif len(self.current_bbox) == 2:
                x1, y1 = self.current_bbox[0]
                x2, y2 = self.current_bbox[1]
                
                # Ensure x1 < x2 and y1 < y2
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                
                # Draw rectangle
                cv2.rectangle(self.img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.imshow('Define Bboxes (click 2x per bbox)', self.img)
                
                # Get field name
                field_name = input("Enter field name for this bbox: ").strip()
                
                if field_name:
                    # Store as normalized coordinates
                    self.bboxes[field_name] = NormalizedBBox.from_pixel_coords(
                        x1, y1, x2, y2, self.img_width, self.img_height
                    )
                    print(f"✓ Saved '{field_name}': {self.bboxes[field_name].to_dict()}")
                
                self.current_bbox.clear()
    
    def _redraw_bboxes(self):
        """Redraw all saved bboxes on the image"""
        for field_name, bbox in self.bboxes.items():
            x1, y1, x2, y2 = bbox.to_pixel_coords(self.img_width, self.img_height)
            cv2.rectangle(self.img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(self.img, field_name, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    def _save_bboxes(self, output_file: str):
        """Save normalized bboxes to JSON"""
        data = {
            'image_width': self.img_width,
            'image_height': self.img_height,
            'bboxes': {k: v.to_dict() for k, v in self.bboxes.items()}
        }
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Saved {len(self.bboxes)} bboxes to {output_file}")


class TextExtractor:
    """Extract text from normalized bboxes on images of any size"""
    
    def __init__(self, bboxes_file: str = 'bboxes.json'):
        with open(bboxes_file) as f:
            data = json.load(f)
        
        self.bboxes = {k: NormalizedBBox.from_dict(v) 
                      for k, v in data['bboxes'].items()}
        self.template_width = data['image_width']
        self.template_height = data['image_height']
        print(f"Loaded {len(self.bboxes)} field definitions")
        print(f"Template size: {self.template_width}x{self.template_height}")
    
    def extract_text(self, image_path: str, engine: str = 'tesseract') -> Dict[str, str]:
        """
        Extract text from all bboxes in image of any size.
        
        Args:
            image_path: Path to scanned image
            engine: 'tesseract' or 'paddleocr'
        """
        img = cv2.imread(image_path)
        img_height, img_width = img.shape[:2]
        
        results = {}
        
        for field_name, bbox in self.bboxes.items():
            # Convert normalized coords to pixel coords for this image
            x1, y1, x2, y2 = bbox.to_pixel_coords(img_width, img_height)
            
            # Crop the region
            cropped = img[y1:y2, x1:x2]
            
            # Extract text
            if engine == 'tesseract':
                text = pytesseract.image_to_string(cropped)
            elif engine == 'paddleocr':
                text = self._extract_with_paddleocr(cropped)
            else:
                raise ValueError(f"Unknown engine: {engine}")
            
            results[field_name] = text.strip()
        
        return results
    
    def _extract_with_paddleocr(self, cropped_img) -> str:
        """Extract text using PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='en')
            ocr_result = ocr.ocr(cropped_img)
            
            if ocr_result and ocr_result[0]:
                text = ' '.join([line[1][0] for line in ocr_result[0]])
            else:
                text = ''
            return text
        except ImportError:
            print("PaddleOCR not installed. Using tesseract instead.")
            return pytesseract.image_to_string(cropped_img)
    
    def extract_text_batch(self, image_paths: list, engine: str = 'tesseract') -> Dict[str, Dict[str, str]]:
        """Extract text from multiple images"""
        all_results = {}
        for i, path in enumerate(image_paths, 1):
            print(f"Processing {i}/{len(image_paths)}: {path}")
            all_results[path] = self.extract_text(path, engine)
        return all_results


# ============= USAGE EXAMPLES =============

if __name__ == '__main__':
    # PHASE 1: Define bounding boxes (run once on template image)
    annotator = BBoxAnnotator()
    annotator.define_bboxes('template_invoice.jpg', 'invoice_bboxes.json')
    
    # PHASE 2: Extract text from any image size
    extractor = TextExtractor('invoice_bboxes.json')
    
    # Single image
    results = extractor.extract_text('new_invoice_large.jpg')
    print("\n=== Extracted Text ===")
    for field, text in results.items():
        print(f"{field}: {text[:50]}...")
    
    # Batch processing
    # results = extractor.extract_text_batch([
    #     'invoice_1.jpg',
    #     'invoice_2.jpg',
    #     'invoice_3_small.jpg',
    # ])
