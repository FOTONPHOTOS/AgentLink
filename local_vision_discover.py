import cv2
import numpy as np
import json

def discover_local(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Locate the "I'm not a robot" widget area
    # Looking for the reCAPTCHA logo or the specific white box geometry
    # The checkbox is a white square with a gray border
    # Based on the image, it is in the lower left area
    
    # Let's use template matching for the checkbox specifically
    # Cropping a generic checkbox from the image for matching
    # Checkbox visual: X=37, Y=595 (approx)
    
    # We will search for a 28x28 white square with a dark border
    # Using Canny + Contours
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    found_checkbox = None
    found_submit = None
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Checkbox is roughly 28x28 to 32x32
        if 25 < w < 35 and 25 < h < 35 and x < 100 and y > 500:
            found_checkbox = (x + w//2, y + h//2)
        # Submit button is roughly 50x20
        if 45 < w < 65 and 15 < h < 30 and x < 100 and y > 600:
            found_submit = (x + w//2, y + h//2)
            
    return {"checkbox": found_checkbox, "submit": found_submit}

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '/root/AgentLink/vision/remote_raw_shot.png'
    res = discover_local(path)
    print(json.dumps(res))
