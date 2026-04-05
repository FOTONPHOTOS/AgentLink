from huggingface_hub import hf_hub_download
import os

repo_id = "bartowski/moondream2-GGUF"
dest = "/root/AgentLink/models"
os.makedirs(dest, exist_ok=True)

print("Downloading Lightning-Fast Model (Q4_0)...")
hf_hub_download(repo_id=repo_id, filename="moondream2-Q4_0.gguf", local_dir=dest)
print("Downloading Vision Projector...")
hf_hub_download(repo_id=repo_id, filename="moondream2-mmproj-f16.gguf", local_dir=dest)
print("SUCCESS")
