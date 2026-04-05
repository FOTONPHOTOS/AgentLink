import os
import time
import easyocr
import cv2
import numpy as np
from PIL import Image
import torch

# 🚀 Enforce CPU Efficiency
torch.set_num_threads(2)

ICON_DIR = '/root/AgentLink/icons/'

class GLMOCREngine:
    def __init__(self):
        self.reader = None
        self.model = None

    def load(self):
        print(" Loading Sovereign Vision Cortex (V34)...")
        try:
            self.reader = easyocr.Reader(['en'], gpu=False)
            self.model = True
            return True
        except Exception as e:
            print(f"❌ Failed to load EasyOCR: {e}")
            return False

    def get_icon_match(self, blob_img):
        """Matches a blob against the local icon library using Histogram Comparison."""
        if not os.path.exists(ICON_DIR): return "UNKNOWN"
        
        best_match = "UNKNOWN"
        best_score = 0
        
        # Convert blob to HSV for robust color matching
        h1 = cv2.calcHist([cv2.cvtColor(blob_img, cv2.COLOR_BGR2HSV)], [0, 1], None, [180, 256], [0, 180, 0, 256])
        cv2.normalize(h1, h1, 0, 1, cv2.NORM_MINMAX)

        for icon_name in os.listdir(ICON_DIR):
            if not icon_name.endswith('.png'): continue
            
            ref_path = os.path.join(ICON_DIR, icon_name)
            ref_img = cv2.imread(ref_path)
            if ref_img is None: continue
            
            # Match histograms
            h2 = cv2.calcHist([cv2.cvtColor(ref_img, cv2.COLOR_BGR2HSV)], [0, 1], None, [180, 256], [0, 180, 0, 256])
            cv2.normalize(h2, h2, 0, 1, cv2.NORM_MINMAX)
            
            score = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
            if score > best_score and score > 0.7: # 70% similarity threshold
                best_score = score
                best_match = icon_name.split('.')[0].upper()
        
        return best_match

    def detect_ui_blobs(self, image_path):
        img = cv2.imread(image_path)
        if img is None: return []
        
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
        
        blobs = []
        for i in range(1, num_labels):
            x, y, bw, bh, area = stats[i]
            cx, cy = centroids[i]
            
            # Filter for Icon-sized objects
            if 20 < bw < 80 and 20 < bh < 80 and 400 < area < 5000:
                # Crop the blob for fingerprinting
                blob_crop = img[y:y+bh, x:x+bw]
                identity = self.get_icon_match(blob_crop)
                
                blobs.append({
                    "box": [x, y, x + bw, y + bh],
                    "center": [int(cx), int(cy)],
                    "identity": identity
                })
        return blobs

    def process_image(self, image_path, prompt=""):
        if not self.reader: self.load()

        try:
            # 1. OCR Scan
            results = self.reader.readtext(image_path, detail=1)
            
            # 2. UI Blob Scan (Sovereign Fingerprinting)
            blobs = self.detect_ui_blobs(image_path)
            
            structured_output = ["[SEMANTIC SCREEN MAP]"]
            text_elements = []
            
            for i, res in enumerate(results):
                box, text, conf = res
                x_coords = [p[0] for p in box]
                y_coords = [p[1] for p in box]
                cx, cy = int(sum(x_coords) / 4), int(sum(y_coords) / 4)
                x1, y1, x2, y2 = int(min(x_coords)), int(min(y_coords)), int(max(x_coords)), int(max(y_coords))
                
                text_elements.append({
                    "id": i + 1, "text": text, "center": (cx, cy), "box": (x1, y1, x2, y2), "conf": conf
                })

            # 3. Fuse Data
            final_id = len(text_elements) + 1
            for blob in blobs:
                bx, by = blob["center"]
                
                # Check for Tooltip Proximity (Text within 50px of blob)
                label_from_ocr = ""
                for te in text_elements:
                    tx, ty = te["center"]
                    dist = np.sqrt((bx - tx)**2 + (by - ty)**2)
                    if dist < 60:
                        label_from_ocr = f" (TOOLTIP: \"{te['text']}\")"
                        break
                
                category = "DOCK_ICON" if by > 800 else "UI_ELEMENT"
                identity = blob["identity"]
                
                line = f"[{final_id}] <{category}:{identity}{label_from_ocr} at {bx},{by}> [Box: {blob['box'][0]},{blob['box'][1]},{blob['box'][2]},{blob['box'][3]}]"
                structured_output.append(line)
                final_id += 1

            for te in text_elements:
                line = f"[{te['id']}] \"{te['text']}\" ({te['center'][0]},{te['center'][1]}) [Box: {te['box'][0]},{te['box'][1]},{te['box'][2]},{te['box'][3]}] Conf: {te['conf']:.2f}"
                structured_output.append(line)
                
            return "\n".join(structured_output)
        except Exception as e:
            return f"Error: {e}"

if __name__ == "__main__":
    engine = GLMOCREngine()
    engine.load()
