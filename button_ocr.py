import cv2
import pytesseract
from pytesseract import Output
import json

img = cv2.imread('/root/AgentLink/vision/latest_grid.png')
# Standard reCAPTCHA popup is usually centered or fixed.
# My precision grid showed Row 12, Col 4 which is X=200, Y=600.
# Let's broaden the search slightly.
crop = img[580:680, 180:380]
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
# Scale up for better OCR
upscaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
# Threshold
thresh = cv2.threshold(upscaled, 150, 255, cv2.THRESH_BINARY)[1]

cv2.imwrite('/root/AgentLink/vision/button_debug_v2.png', thresh)

data = pytesseract.image_to_data(thresh, output_type=Output.DICT)
results = []
for i in range(len(data['text'])):
    if data['text'][i].strip():
        # Correct for upscaling and offset
        results.append({
            "text": data['text'][i],
            "x": (data['left'][i] / 2) + 180,
            "y": (data['top'][i] / 2) + 580,
            "w": data['width'][i] / 2,
            "h": data['height'][i] / 2
        })

print(json.dumps(results))
