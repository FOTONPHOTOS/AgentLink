import cv2
import numpy as np
import sys
import os

def process_grid(image_path, output_dir, tile_coords):
    img = cv2.imread(image_path)
    if img is None: return
    
    h, w = img.shape[:2]
    
    # 1. Full Desktop with 50px Grid
    full_grid = img.copy()
    for x in range(0, w, 50):
        cv2.line(full_grid, (x, 0), (x, h), (0, 0, 255), 1)
    for y in range(0, h, 50):
        cv2.line(full_grid, (0, y), (w, y), (0, 0, 255), 1)
    cv2.imwrite(os.path.join(output_dir, "full_desktop_grid.png"), full_grid)
    
    # 2. Zoomed Image (Crop to CAPTCHA area)
    # Area based on tile mapping: X[50-350], Y[250-550]
    zoom_crop = img[250:650, 50:350]
    cv2.imwrite(os.path.join(output_dir, "zoom_raw.png"), zoom_crop)
    
    # 3. Zoomed with Numbered Tiles
    zoom_numbered = zoom_crop.copy()
    # Normalize coordinates to crop area
    for i, (tx, ty) in enumerate(tile_coords):
        nx = tx - 50
        ny = ty - 250
        cv2.putText(zoom_numbered, str(i+1), (nx, ny), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.rectangle(zoom_numbered, (nx-10, ny-10), (nx+10, ny+10), (255, 255, 0), 2)
        
    cv2.imwrite(os.path.join(output_dir, "zoom_numbered.png"), zoom_numbered)
    print(f"Grid analysis complete. Files in {output_dir}")

if __name__ == "__main__":
    tiles = [
        [95, 322], [188, 321], [282, 321],
        [95, 414], [189, 414], [282, 414],
        [95, 508], [188, 508], [282, 508]
    ]
    process_grid("/root/AgentLink/vision/latest_grid.png", "/root/AgentLink/vision", tiles)
