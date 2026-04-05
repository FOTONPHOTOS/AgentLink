import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

model_id = "moondream/moondream-2b-2025-04-14-4bit"
dest = "/root/AgentLink/models/moondream_4bit"
os.makedirs(dest, exist_ok=True)

print(f"Downloading {model_id}...")
# This will download and cache the model.
# We use bfloat16 for CPU efficiency as bitsandbytes 4-bit is mostly CUDA.
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    torch_dtype=torch.bfloat16
)
print("SUCCESS")
