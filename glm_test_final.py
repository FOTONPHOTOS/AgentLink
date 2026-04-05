
import torch
import os
import time
from glm_engine import GLMOCREngine

# Limit CPU
torch.set_num_threads(2)

def test():
    print("🚀 GLM-OCR Standalone Test Start")
    engine = GLMOCREngine()
    
    # 1. Load Model
    if not engine.load():
        print("❌ Load Failed")
        return

    # 2. Process Latest Grid
    image_path = "/root/AgentLink/vision/latest_grid.png"
    if not os.path.exists(image_path):
        print(f"⚠ Image not found: {image_path}")
        return

    print(" Starting Inference...")
    start = time.time()
    result = engine.process_image(image_path)
    print(f" Inference Complete in {time.time() - start:.2f}s")
    print("--- RESULT ---")
    print(result)
    print("--------------")

if __name__ == "__main__":
    test()
