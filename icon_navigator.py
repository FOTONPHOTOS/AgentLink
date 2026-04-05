import cv2
import numpy as np
import os
import sys
import json

def find_best_match(screen_path, template_path, threshold=0.7):
    """Finds an icon using multi-scale template matching."""
    img = cv2.imread(screen_path, 0)
    template = cv2.imread(template_path, 0)
    if img is None or template is None: return None

    w, h = template.shape[::-1]
    found = None

    # Loop over the scales of the image
    for scale in np.linspace(0.5, 1.5, 20):
        resized = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)))
        r = img.shape[1] / float(resized.shape[1])

        if resized.shape[0] < h or resized.shape[1] < w:
            break

        res = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF_NORMED)
        (_, maxVal, _, maxLoc) = cv2.minMaxLoc(res)

        if found is None or maxVal > found[0]:
            found = (maxVal, maxLoc, r)

    if found is None: return None
    (maxVal, maxLoc, r) = found
    if maxVal >= threshold:
        startX, startY = (int(maxLoc[0] * r), int(maxLoc[1] * r))
        endX, endY = (int((maxLoc[0] + w) * r), int((maxLoc[1] + h) * r))
        return {
            "center": (startX + (endX - startX) // 2, startY + (endY - startY) // 2),
            "confidence": maxVal,
            "box": [startX, startY, endX, endY]
        }
    return None

def main():
    if len(sys.argv) > 1:
        screen = sys.argv[1]
    else:
        screen = '/root/AgentLink/live_frame.png'
    icon_dir = '/root/AgentLink/icons/'
    
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
        return

    results = {}
    for icon_name in os.listdir(icon_dir):
        if icon_name.endswith('.png'):
            match = find_best_match(screen, os.path.join(icon_dir, icon_name))
            if match:
                results[icon_name.split('.')[0]] = match

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
