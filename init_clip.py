import open_clip
import torch
import os

MODEL_DIR = '/root/AgentLink/models'
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

print("🚀 Loading lightweight CLIP model (ViT-B-32-quickgelu)...")
# ViT-B-32 is a good balance between speed and accuracy for semantic search
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32-quickgelu', pretrained='laion400m_e32')
tokenizer = open_clip.get_tokenizer('ViT-B-32-quickgelu')

# Save placeholder to confirm success
with open(os.path.join(MODEL_DIR, 'clip_ready.txt'), 'w') as f:
    f.write('ready')

print(" CLIP model initialized and cached.")
