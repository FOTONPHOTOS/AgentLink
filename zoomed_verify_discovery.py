import cv2
import numpy as np
import os
import sys
import json
import pytesseract
from pytesseract import Output

# 1. Configuration
IMAGE_PATH = "/root/AgentLink/vision/latest_grid.png"
OUTPUT_DIR = "/root/AgentLink/vision"
# Crop Area: Entire CAPTCHA Widget (approx based on precision grid)
CROP_X1, CROP_Y1, CROP_X2, CROP_Y2 = 0, 150, 450, 750
SCALE_FACTOR = 2

def run_zoomed_analysis():
    img = cv2.imread(IMAGE_PATH)
    if img is None: return
    
    # 2. Crop & Upscale
    crop = img[CROP_Y1:CROP_Y2, CROP_X1:CROP_X2]
    zoomed = cv2.resize(crop, None, fx=SCALE_FACTOR, fy=SCALE_FACTOR, interpolation=cv2.INTER_CUBIC)
    h, w = zoomed.shape[:2]
    
    # 3. Overlay Scaled Grid (50px in global space = 100px in zoomed space)
    grid_overlay = zoomed.copy()
    grid_size = 50 * SCALE_FACTOR
    for x in range(0, w, grid_size):
        cv2.line(grid_overlay, (x, 0), (x, h), (0, 0, 255), 1)
    for y in range(0, h, grid_size):
        cv2.line(grid_overlay, (0, y), (w, y), (0, 0, 255), 1)
        
    # Add Zone Numbering
    for y in range(0, h, grid_size):
        for x in range(0, w, grid_size):
            row = (y // grid_size) + (CROP_Y1 // 50)
            col = (x // grid_size) + (CROP_X1 // 50)
            cv2.putText(grid_overlay, f"{row},{col}", (x+5, y+25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            
    cv2.imwrite(os.path.join(OUTPUT_DIR, "zoomed_precision_map.png"), grid_overlay)

    # 4. Perform High-Res OCR on the Zoomed Image
    gray = cv2.cvtColor(zoomed, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
    data = pytesseract.image_to_data(thresh, output_type=Output.DICT)
    
    found_verify = None
    for i in range(len(data['text'])):
        text = data['text'][i].strip().lower()
        if "verify" in text or "ery" in text: # Catch partials
            # Zoomed Center
            zx = data['left'][i] + data['width'][i] // 2
            zy = data['top'][i] + data['height'][i] // 2
            
            # Map back to Global Coordinates
            global_x = (zx / SCALE_FACTOR) + CROP_X1
            global_y = (zy / SCALE_FACTOR) + CROP_Y1
            
            found_verify = {
                "text": text,
                "global_center": [int(global_x), int(global_y)],
                "confidence": data['conf'][i]
            }
            break

    if found_verify:
        print(json.dumps(found_verify, indent=2))
    else:
        print(json.dumps({"error": "Verify button text not found in zoom"}))

if __name__ == "__main__":
    run_zoomed_analysis()
