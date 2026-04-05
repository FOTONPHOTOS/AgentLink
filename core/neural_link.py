import subprocess
import requests
import time
import json
import os

VISION_API = "http://127.0.0.1:8095/deep_scan"

class NeuralLink:
    def __init__(self, node="brain2"):
        self.node = node
        self.last_scan = None

    def see(self):
        """Performs a deep scan and returns the structured semantic map."""
        try:
            # 1. Trigger Remote Capture via alrun
            subprocess.run(["alrun", self.node, "capture", ":10"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 2. Trigger Local Analysis (EasyOCR V32)
            # Note: alrun downloads to /root/AgentLink/vision/latest_grid.png
            # The Vision Server reads that file if node=local-node, or we can just ask it to scan 'brain2' 
            # if we trust the bridge. But to be safe and use the file we JUST downloaded:
            
            # Actually, the most robust V32 way is: 
            # alrun capture -> local file -> ask vision server to scan local file 
            # BUT vision server logic defaults to 'scrot' if we hit the endpoint.
            # So we will use the endpoint which we know now works via the Bridge Protocol.
            
            resp = requests.get(f"{VISION_API}?node={self.node}&display=:10", timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                self.last_scan = data.get("semantic_content", "")
                return self.last_scan
            return "Error: Vision API Failed"
        except Exception as e:
            return f"Error: {e}"

    def act(self, action, params=None, verify=True):
        """
        Executes an action and optionally verifies it changed the screen.
        action: 'click', 'type', 'exec'
        """
        pre_state = self.last_scan if verify else ""
        
        cmd = ["alrun", self.node]
        if action == "click":
            cmd.extend(["click", str(params[0]), str(params[1])])
        elif action == "type":
            cmd.extend(["type", params])
        elif action == "exec":
            cmd.append(params)
            
        subprocess.run(cmd, check=True)
        
        if verify:
            time.sleep(2) # Reaction time
            post_state = self.see()
            if pre_state == post_state:
                return {"success": False, "reason": "No visual change detected"}
            return {"success": True, "state": post_state}
        
        return {"success": True}

    def find_text(self, text_query):
        """Parses the semantic map to find coordinates of text."""
        if not self.last_scan: self.see()
        
        lines = self.last_scan.split('\n')
        for line in lines:
            if text_query.lower() in line.lower() and "[Box:" in line:
                # Extract Center (x,y)
                # Format: [ID] "Text" (x,y) [Box...
                try:
                    parts = line.split('(')[1].split(')')[0]
                    x, y = map(int, parts.split(','))
                    return (x, y)
                except:
                    continue
        return None
