import cv2
import numpy as np
import sys
import json
import os
import pytesseract
from pytesseract import Output
import onnxruntime as ort

# Ensure tesseract is available
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# YOLO Configuration
YOLO_MODEL_PATH = '/root/AgentLink/models/yolov8n.onnx'
ort_session = None

def get_yolo_session():
    global ort_session
    if ort_session is None and os.path.exists(YOLO_MODEL_PATH):
        try:
            ort_session = ort.InferenceSession(YOLO_MODEL_PATH, providers=['CPUExecutionProvider'])
        except Exception as e:
            print(f"YOLO ERROR: Failed to load ONNX session: {e}")
    return ort_session

def detect_objects_yolo(image_path, confidence_threshold=0.25):
    """
    Detects objects using the YOLO ONNX model.
    """
    session = get_yolo_session()
    if session is None: return []
    
    img = cv2.imread(image_path)
    if img is None: return []
    
    h, w = img.shape[:2]
    
    # 1. Preprocess
    input_img = cv2.resize(img, (640, 640))
    input_img = input_img.transpose(2, 0, 1) # HWC to CHW
    input_img = input_img.astype(np.float32) / 255.0
    input_img = np.expand_dims(input_img, axis=0) # Add batch dimension
    
    # 2. Inference
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: input_img})
    
    # 3. Post-process (Standard YOLOv8 ONNX output is [1, 84, 8400])
    # Elements: [x, y, w, h, class0_conf, class1_conf, ...]
    predictions = np.squeeze(outputs[0]).T # [8400, 84]
    
    results = []
    for pred in predictions:
        scores = pred[4:]
        class_id = np.argmax(scores)
        confidence = scores[class_id]
        
        if confidence > confidence_threshold:
            # Scale coordinates back to original image size
            xc, yc, ow, oh = pred[:4]
            x1 = int((xc - ow/2) * w / 640)
            y1 = int((yc - oh/2) * h / 640)
            x2 = int((xc + ow/2) * w / 640)
            y2 = int((yc + oh/2) * h / 640)
            
            results.append({
                "category": "object",
                "class_id": int(class_id),
                "box": [max(0, x1), max(0, y1), min(w, x2), min(h, y2)],
                "center": [int(x1 + (x2-x1)//2), int(y1 + (y2-y1)//2)],
                "confidence": float(confidence)
            })
            
    # Simple Non-Maximum Suppression (NMS) could be added here
    return results

def detect_text(image_path):
    """
    Detects text using Tesseract OCR and returns a list of text elements with bounding boxes.
    """
    img = cv2.imread(image_path)
    if img is None: return []
    
    # Preprocessing for better OCR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Simple thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    custom_config = r'--oem 3 --psm 6' # PSM 6 assumes a block of text
    data = pytesseract.image_to_data(thresh, config=custom_config, output_type=Output.DICT)
    
    text_elements = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        if int(data['conf'][i]) > 40: # Confidence threshold
            text = data['text'][i].strip()
            if len(text) > 1: # Ignore single chars/noise
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                text_elements.append({
                    "text": text,
                    "box": [x, y, x+w, y+h],
                    "center": [x + w//2, y + h//2],
                    "confidence": int(data['conf'][i]) / 100.0
                })
    return text_elements

def detect_shapes(image_path):
    """
    Detects various UI shapes: Scrollbars, Checkboxes, Radio Buttons, 
    Search Bars, Triangles, and Captcha Grids.
    """
    img = cv2.imread(image_path)
    if img is None: return {}
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    results = {
        "scrollbars": [],
        "checkboxes": [],
        "radio_buttons": [],
        "search_bars": [],
        "buttons": [],
        "triangles": [],
        "captcha_grids": []
    }
    
    min_area = 50
    
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < min_area: continue
        
        perimeter = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / h
        
        # --- 1. Triangles (3 vertices) ---
        if len(approx) == 3:
            results["triangles"].append({
                "box": [x, y, x+w, y+h],
                "center": [x + w//2, y + h//2],
                "confidence": 0.85
            })
            continue

        # --- 2. Rectangular Shapes (4 vertices) ---
        if len(approx) == 4:
            # Scrollbars: Very thin/wide
            if aspect_ratio < 0.2 or aspect_ratio > 5.0:
                 results["scrollbars"].append({
                    "type": "vertical" if aspect_ratio < 1 else "horizontal",
                    "box": [x, y, x+w, y+h],
                    "center": [x + w//2, y + h//2],
                    "confidence": 0.85
                })
            
            # Checkboxes: Aspect ratio ~ 1.0, small size
            elif 0.8 < aspect_ratio < 1.2 and area < 2000:
                 results["checkboxes"].append({
                    "type": "standard",
                    "box": [x, y, x+w, y+h],
                    "center": [x + w//2, y + h//2],
                    "confidence": 0.90
                })

            # Search Bars / Text Inputs: Wide, moderate height
            elif aspect_ratio > 3.0 and h > 20 and area > 1000:
                 results["search_bars"].append({
                    "box": [x, y, x+w, y+h],
                    "center": [x + w//2, y + h//2],
                    "confidence": 0.80
                })
            
            # General Buttons: Rectangular, moderate size
            elif 1.2 < aspect_ratio < 5.0 and 2000 < area < 20000:
                 results["buttons"].append({
                    "box": [x, y, x+w, y+h],
                    "center": [x + w//2, y + h//2],
                    "confidence": 0.75
                })

        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if 0.7 < circularity < 1.2 and 0.8 < aspect_ratio < 1.2:
                 results["radio_buttons"].append({
                    "box": [x, y, x+w, y+h],
                    "center": [x + w//2, y + h//2],
                    "confidence": 0.85
                })
                
        if hierarchy is not None:
            current_idx = i
            child_idx = hierarchy[0][current_idx][2]
            children_count = 0
            while child_idx != -1:
                children_count += 1
                child_idx = hierarchy[0][child_idx][0]
            
            if 8 <= children_count <= 10: 
                 results["captcha_grids"].append({
                    "box": [x, y, x+w, y+h],
                    "center": [x + w//2, y + h//2],
                    "confidence": 0.95
                })

    return results

def find_best_match(screen_path, template_path, threshold=0.7):
    img = cv2.imread(screen_path, 0)
    template = cv2.imread(template_path, 0)
    if img is None or template is None: return None

    w, h = template.shape[::-1]
    found = None

    for scale in np.linspace(0.5, 1.5, 20):
        resized = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)))
        r = img.shape[1] / float(resized.shape[1])
        if resized.shape[0] < h or resized.shape[1] < w: break

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

def associate_elements(text_list, shapes):
    """
    Associates text labels with nearby UI elements (shapes) based on proximity.
    Now includes detection for text OVERLAYING a shape (e.g., buttons).
    """
    associations = []
    
    # Flatten all shapes into a single list with 'category' tag
    all_shapes = []
    for cat, items in shapes.items():
        for item in items:
            item['category'] = cat
            all_shapes.append(item)
            
    # For each text label, find nearest shape
    for txt in text_list:
        tx_min, ty_min, tx_max, ty_max = txt['box']
        tx_center, ty_center = txt['center']
        
        best_shape = None
        min_dist = 150 # Max pixels to consider "nearby"
        relation = "none"
        
        for shape in all_shapes:
            sx_min, sy_min, sx_max, sy_max = shape['box']
            sx_center, sy_center = shape['center']
            
            # 1. Check for containment (Text INSIDE Shape) -> High certainty for Buttons
            # Allow a small margin for OCR box jitter
            if tx_min >= sx_min - 5 and tx_max <= sx_max + 5 and \
               ty_min >= sy_min - 5 and ty_max <= sy_max + 5:
                relation = "inside"
                dist = 0 # Prioritize containment
            else:
                # 2. Standard Proximity
                dist = np.sqrt((tx_center - sx_center)**2 + (ty_center - sy_center)**2)
                
                if dist < min_dist:
                    dx = sx_center - tx_center
                    dy = sy_center - ty_center
                    
                    if dx > 0 and abs(dy) < 30:
                        relation = "right_of"
                    elif dx < 0 and abs(dy) < 30:
                        relation = "left_of"
                    elif dy > 0 and abs(dx) < 50:
                        relation = "below"
                    else:
                        relation = "near"
                else:
                    continue # Too far

            # Selection Logic: Prioritize 'inside' or closer distance
            if best_shape is None or relation == "inside" or dist < best_shape['dist']:
                 best_shape = {
                     "shape": shape,
                     "dist": dist,
                     "relation": relation
                 }
                 if relation == "inside": break # Found the button container

        if best_shape:
            associations.append({
                "label": txt['text'],
                "associated_element": best_shape['shape'],
                "relation": best_shape['relation'],
                "distance": float(best_shape['dist'])
            })
            
    return associations

def draw_som_overlay(image_path, output_path, elements):
    """
    Draws a Smart Set-of-Mark overlay on the image.
    Uses semi-transparent badges with IDs for each semantic element.
    """
    print(f"DRAW_SOM: Loading {image_path}")
    img = cv2.imread(image_path)
    if img is None: 
        print(f"DRAW_SOM ERROR: Could not load image {image_path}")
        return None
    
    h, w = img.shape[:2]
    overlay = img.copy()
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    thickness = 1
    
    # Filter elements that have required keys
    valid_elements = [e for e in elements if 'center' in e and 'box' in e]
    print(f"DRAW_SOM: Processing {len(valid_elements)} valid elements out of {len(elements)}")
    
    # Sort elements to ensure deterministic numbering (Top-Left to Bottom-Right)
    valid_elements.sort(key=lambda e: (e['center'][1] // 20, e['center'][0]))
    
    marks = {}
    
    for i, el in enumerate(valid_elements):
        mark_id = i + 1
        try:
            x1, y1, x2, y2 = el['box']
            cx, cy = el['center']
            
            # 1. Choose color based on category (if available)
            color = (0, 255, 0) # Green for text
            if 'category' in el:
                cat = el['category']
                if cat == 'buttons': color = (255, 0, 0) # Blue
                elif cat == 'checkboxes': color = (0, 255, 255) # Yellow
                elif cat == 'icons': color = (0, 165, 255) # Orange
            
            # 2. Draw subtle bounding box
            cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), color, 1)
            
            # 3. Draw Badge (The Mark)
            label = str(mark_id)
            (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)
            
            pad = 2
            bx1, by1 = int(x1 - tw - pad), int(y1 - th - pad)
            bx2, by2 = int(x1 + pad), int(y1 + pad)
            
            if bx1 < 0: bx1 = int(x1 + pad); bx2 = int(x1 + tw + pad*2)
            if by1 < 0: by1 = int(y1 + pad); by2 = int(y1 + th + pad*2)
            
            cv2.rectangle(overlay, (bx1, by1), (bx2, by2), color, -1)
            cv2.putText(overlay, label, (bx1 + pad, by2 - pad), font, font_scale, (255, 255, 255), thickness)
            
            marks[mark_id] = {
                "id": mark_id,
                "center": [int(cx), int(cy)],
                "box": [int(x1), int(y1), int(x2), int(y2)],
                "content": el.get('text', el.get('category', 'unknown'))
            }
        except Exception as e:
            print(f"DRAW_SOM element error: {e}")

    # Apply 40% transparency to the marks
    alpha = 0.6
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    
    cv2.imwrite(output_path, img)
    print(f"DRAW_SOM: Saved to {output_path}")
    return marks

if __name__ == "__main__":
    if len(sys.argv) > 1:
        screen = sys.argv[1]
    else:
        screen = '/root/AgentLink/vision/latest_grid.png'
        
    final_output = {}
    
    # 1. Detect Text (OCR)
    text_elements = detect_text(screen)
    final_output["text_elements"] = text_elements
    
    # 2. Detect Shapes
    shape_results = detect_shapes(screen)
    for category, items in shape_results.items():
        if items:
            final_output[category] = items
            
    # 3. Detect Icons
    icon_dir = '/root/AgentLink/icons/'
    if os.path.exists(icon_dir):
        for icon_name in os.listdir(icon_dir):
            if icon_name.endswith('.png'):
                label = icon_name.split('.')[0]
                if label == 'chrome': label = 'browser_native'
                match = find_best_match(screen, os.path.join(icon_dir, icon_name))
                if match:
                    final_output[label] = match

    # 4. Proximity Association (The Fusion)
    associations = associate_elements(text_elements, shape_results)
    final_output["associations"] = associations

    print(json.dumps(final_output, indent=2))