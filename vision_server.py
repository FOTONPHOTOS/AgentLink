import asyncio
import json
import os
import subprocess
import time
from aiohttp import web
import torch

from glm_engine import GLMOCREngine

# Configuration
PORT = 8095
HOST = '127.0.0.1'
LOCAL_VISION_DIR = '/root/AgentLink/vision'

class VisionServer:
    def __init__(self):
        if not os.path.exists(LOCAL_VISION_DIR):
            os.makedirs(LOCAL_VISION_DIR)
        self.glm = GLMOCREngine()

    async def handle_deep_scan(self, request):
        node = request.query.get('node', 'local-node')
        display = request.query.get('display', ':10')
        prompt = request.query.get('prompt', 'Describe the text and UI elements in this image in detail.')
        
        image_path = os.path.join(LOCAL_VISION_DIR, f"deep_{node}.png")
        
        # 1. Capture
        if node == "local-node":
            print(f"📸 Capturing LOCAL display {display}...")
            cmd = f"export DISPLAY={display} && scrot -o {image_path}"
            subprocess.run(cmd, shell=True)
        else:
            print(f"🔗 Capturing REMOTE display {display} on {node} via alrun...")
            # alrun [node] capture [display]
            # alrun downloads to /root/AgentLink/vision/latest_grid.png
            # We move it to the specific node path for the Vision Server to process
            cmd = f"alrun {node} capture {display}"
            subprocess.run(cmd, shell=True)
            local_grid = os.path.join(LOCAL_VISION_DIR, "latest_grid.png")
            if os.path.exists(local_grid):
                os.rename(local_grid, image_path)

        if not os.path.exists(image_path):
            return web.json_response({"error": "Capture failed"}, status=500)

        # 2. Inference
        print(f" Deep Scan Start: prompt='{prompt}'")
        start_time = time.time()
        # Use asyncio.to_thread because llama-cpp is blocking
        semantic_data = await asyncio.to_thread(self.glm.process_image, image_path, prompt)
        duration = time.time() - start_time
        
        print(f" Deep Scan Complete in {duration:.2f}s")
        return web.json_response({
            "status": "success",
            "duration_s": duration,
            "semantic_content": semantic_data
        })

    async def handle_status(self, request):
        model_status = "Ready" if self.glm.model else "Loading"
        return web.json_response({
            "status": "Vision Server Online", 
            "model": "Moondream2",
            "model_state": model_status
        })

async def main():
    server = VisionServer()
    app = web.Application()
    app.router.add_get('/deep_scan', server.handle_deep_scan)
    app.router.add_get('/status', server.handle_status)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    print(f"🚀 Vision Server active on http://{HOST}:{PORT}")
    await site.start()

    print(" Loading GGUF Model in background...")
    await asyncio.to_thread(server.glm.load)
    print(" GGUF Model Ready")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
