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
    print("🚀 VLM Isolation Test: Starting...")
    print(f"📊 Initial RAM Usage: {get_mem():.2f} GB")
    
    model_id = "moondream/moondream-2b-2025-04-14-4bit"
    image_path = "/root/AgentLink/vision/latest_grid.png"
    
    if not os.path.exists(image_path):
        print(f"⚠ Image not found at {image_path}, using a blank placeholder for speed.")
        image = Image.new('RGB', (1024, 1024), color='white')
    else:
        image = Image.open(image_path).convert("RGB")

    print(f"🔍 Check CUDA: {'AVAILABLE' if torch.cuda.is_available() else 'NOT FOUND (Using CPU)'}")
    
    # 1. Loading Model
    print(f" Loading {model_id}...")
    start_load = time.time()
    try:
        # Patch check: Ensure we handle the tied weights error if it persists
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        ).to("cpu").eval()
        
        load_time = time.time() - start_load
        print(f" Model Loaded in {load_time:.2f}s")
        print(f"📊 RAM after load: {get_mem():.2f} GB")
        
        # 2. Inference
        print("⚡ Starting Inference...")
        start_inf = time.time()
        with torch.no_grad():
            image_embeds = model.encode_image(image)
            answer = model.answer_question(image_embeds, "Read the visible text on the terminal screen.", tokenizer)
        
        inf_time = time.time() - start_inf
        print(f" Inference Complete in {inf_time:.2f}s")
        print(f"📝 Result: {answer}")
        print(f"📊 Final RAM: {get_mem():.2f} GB")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Limit to 2 threads for safety
    torch.set_num_threads(2)
    test()
