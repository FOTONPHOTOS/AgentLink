import cv2
import numpy as np
import sys

def find_icon(screen_path, template_path, threshold=0.8):
    # Load images
    screen = cv2.imread(screen_path)
    template = cv2.imread(template_path)
    
    if screen is None or template is None:
        return None

    # Perform Template Matching
    res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        # Get center of the match
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return (center_x, center_y, max_val)
    return None

if __name__ == "__main__":
    # For this demo, we'll surgically crop the Home icon first
    full_screen = cv2.imread('/root/AgentLink/live_frame.png')
    # Home icon is roughly at [10, 210] based on visual audit
    home_template = full_screen[200:260, 15:75] 
    cv2.imwrite('/root/AgentLink/home_icon.png', home_template)
    
    # Now find it
    match = find_icon('/root/AgentLink/live_frame.png', '/root/AgentLink/home_icon.png')
    if match:
        print(f" ICON DISCOVERED: Home Icon found at X={match[0]}, Y={match[1]} (Confidence: {match[2]:.2f})")
    else:
        print("❌ ICON NOT FOUND")
