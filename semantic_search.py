import torch
import open_clip
from PIL import Image
import os
import numpy as np

class SemanticAtlas:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🧬 SemanticAtlas: Using device {self.device}")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms('ViT-B-32-quickgelu', pretrained='laion400m_e32')
        self.model = self.model.to(self.device)
        self.tokenizer = open_clip.get_tokenizer('ViT-B-32-quickgelu')
        self.index = {} # Filename -> Embedding

    def encode_image(self, image_path):
        """Generates an embedding for a single image crop."""
        try:
            image = self.preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)
            with torch.no_grad():
                image_features = self.model.encode_image(image)
                image_features /= image_features.norm(dim=-1, keepdim=True)
            return image_features.cpu().numpy()
        except Exception as e:
            print(f"Embedding error for {image_path}: {e}")
            return None

    def index_atlas(self, atlas_dir):
        """Indexes all images in the atlas directory."""
        print(f"📦 Indexing Atlas: {atlas_dir}")
        for filename in os.listdir(atlas_dir):
            if filename.endswith(".png") and filename not in self.index:
                path = os.path.join(atlas_dir, filename)
                emb = self.encode_image(path)
                if emb is not None:
                    self.index[filename] = emb
        print(f" Indexed {len(self.index)} unique elements.")

    def search(self, query_text, top_k=3):
        """Searches the atlas for the most similar element to the query text."""
        if not self.index: return []
        
        # Encode text query
        text = self.tokenizer([query_text]).to(self.device)
        with torch.no_grad():
            text_features = self.model.encode_text(text)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        
        query_emb = text_features.cpu().numpy()
        
        results = []
        for filename, emb in self.index.items():
            # Cosine similarity
            score = np.dot(query_emb, emb.T)[0][0]
            results.append({"atlas_id": filename, "score": float(score)})
            
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

# Singleton instance
ATLAS_ENGINE = None

def get_atlas_engine():
    global ATLAS_ENGINE
    if ATLAS_ENGINE is None:
        ATLAS_ENGINE = SemanticAtlas()
    return ATLAS_ENGINE
