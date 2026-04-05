import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from quanto import quantize, freeze, qint4
import time

model_id = "zai-org/GLM-OCR"
print("Loading model...")
model = AutoModelForImageTextToText.from_pretrained(
    model_id, 
    trust_remote_code=True, 
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True
)
print("Quantizing...")
quantize(model, weights=qint4)
print("Freezing...")
freeze(model)
print("SUCCESS")
