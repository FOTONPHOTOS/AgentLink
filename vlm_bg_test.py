import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
import os
import time
import psutil

def get_mem():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024 / 1024 # GB

def test():
    with open("/root/AgentLink/vlm_test_log.txt", "w") as f:
        f.write("VLM Background Test Start\n")
        f.write(f"Initial RAM: {get_mem():.2f} GB\n")
        f.flush()
        
        model_id = "moondream/moondream-2b-2025-04-14-4bit"
        image_path = "/root/AgentLink/vision/latest_grid.png"
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16
            ).to("cpu").eval()
            
            f.write(f"Model Loaded. RAM: {get_mem():.2f} GB\n")
            f.flush()
            
            if os.path.exists(image_path):
                image = Image.open(image_path).convert("RGB")
            else:
                image = Image.new('RGB', (1024, 1024), color='white')

            f.write("Starting Inference...\n")
            f.flush()
            
            start_inf = time.time()
            with torch.no_grad():
                image_embeds = model.encode_image(image)
                answer = model.answer_question(image_embeds, "Read the visible text on the terminal screen.", tokenizer)
            
            inf_time = time.time() - start_inf
            f.write(f"Inference Complete in {inf_time:.2f}s\n")
            f.write(f"Result: {answer}\n")
            f.write(f"Final RAM: {get_mem():.2f} GB\n")
            f.flush()
            
        except Exception as e:
            f.write(f"FAILED: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())

if __name__ == "__main__":
    torch.set_num_threads(2)
    test()