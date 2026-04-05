import cv2
import numpy as np
import os

def overlay_precision_grid(image_path, output_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read {image_path}")
        return
    
    h, w = img.shape[:2]
    overlay = img.copy()
    
    # 1. Draw thin grid (50px)
    grid_color = (0, 0, 255) # Red
    for x in range(0, w, 50):
        cv2.line(overlay, (x, 0), (x, h), grid_color, 1)
    for y in range(0, h, 50):
        cv2.line(overlay, (0, y), (w, y), grid_color, 1)
    
    # 2. Add tiny yellow numbering
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.3
    text_color = (0, 255, 255) # Yellow
    thickness = 1
    
    for y in range(0, h, 50):
        for x in range(0, w, 50):
            # Flat index or (row, col)
            row = y // 50
            col = x // 50
            label = f"{row},{col}"
            # Put text in top-left of cell
            cv2.putText(overlay, label, (x + 2, y + 10), font, font_scale, text_color, thickness)

    # Blend overlay with original (optional, but requested thin/readable)
    # Just using the lines directly is clearer if they are 1px
    cv2.imwrite(output_path, overlay)
    print(f"Precision grid saved to {output_path}")

if __name__ == "__main__":
    overlay_precision_grid("/root/AgentLink/vision/latest_grid.png", "/root/AgentLink/vision/precision_grid_map.png")
