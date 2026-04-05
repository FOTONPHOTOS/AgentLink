import torch
import os
import time
import json
import sys

# Move to the correct directory to ensure relative paths work
os.chdir("/root/AgentLink")
sys.path.append("/root/AgentLink")

from glm_engine import GLMOCREngine

# Limit CPU
torch.set_num_threads(2)

def run_bg_test():
    with open("glm_progress.log", "w") as f:
        f.write(f"START: {time.time()}\n")
        f.flush()
        
        try:
            engine = GLMOCREngine()
            f.write("LOADING MODEL...\n")
            f.flush()
            if not engine.load():
                f.write("LOAD FAILED\n")
                return

            image_path = "/root/AgentLink/vision/latest_grid.png"
            f.write(f"ANALYZING: {image_path}\n")
            f.flush()
            
            start = time.time()
            result = engine.process_image(image_path)
            duration = time.time() - start
            
            with open("glm_result.txt", "w") as rf:
                rf.write(f"DURATION: {duration:.2f}s\n")
                rf.write("--- RESULT ---\n")
                rf.write(str(result))
                rf.write("\n--------------\n")
            
            f.write(f"COMPLETE: {time.time()}\n")
            f.flush()
        except Exception as e:
            f.write(f"CRASH: {str(e)}\n")
            f.flush()

if __name__ == "__main__":
    run_bg_test()