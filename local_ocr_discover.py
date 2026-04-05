import pytesseract
from pytesseract import Output
import cv2
import json

def discover_ocr(image_path):
    img = cv2.imread(image_path)
    d = pytesseract.image_to_data(img, output_type=Output.DICT)
    results = []
    for i in range(len(d['text'])):
        if d['text'][i].strip():
            results.append({
                'text': d['text'][i],
                'x': d['left'][i],
                'y': d['top'][i],
                'w': d['width'][i],
                'h': d['height'][i]
            })
    return results

if __name__ == '__main__':
    res = discover_ocr('/root/AgentLink/vision/demo_page.png')
    print(json.dumps(res, indent=2))
