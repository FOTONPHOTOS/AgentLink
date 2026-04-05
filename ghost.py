
import os
import subprocess
import time
import signal
import mss
import numpy as np
from PIL import Image

class AgentLinkGhost:
    def __init__(self, display=":99", resolution="1920x1080x24"):
        self.display = display
        self.resolution = resolution
        self.xvfb_proc = None

    def start(self):
        """Starts the Virtual Framebuffer if not already running."""
        # Check if display is already in use
        if os.path.exists(f"/tmp/.X11-unix/X{self.display.replace(':', '')}"):
            print(f"👻 Ghost Display {self.display} already exists.")
            # Ensure window manager is running
            subprocess.Popen(["fluxbox", "-display", self.display], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True

        print(f"🚀 Starting Ghost Display {self.display} ({self.resolution})...")
        # -ac disables access control, +extension RANDR allows resolution changes
        cmd = f"Xvfb {self.display} -screen 0 {self.resolution} -ac +extension RANDR"
        self.xvfb_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Critical: Wait for Xvfb to socketize
        time.sleep(3)
        
        # Start Window Manager
        subprocess.Popen(["fluxbox", "-display", self.display], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        print(f"🎨 Window Manager (fluxbox) active on {self.display}")
        return True

    def run_app(self, cmd_str):
        """Runs an application inside the Ghost Display and waits for it to map."""
        print(f"📦 Launching App: {cmd_str}")
        env = os.environ.copy()
        env["DISPLAY"] = self.display
        proc = subprocess.Popen(f"nohup {cmd_str} > /dev/null 2>&1 &", shell=True, env=env)
        time.sleep(3) # Wait for window to map
        return proc.pid

    def capture(self, output_path="/root/AgentLink/vision/ghost_latest.png"):
        """High-speed capture with scrot fallback for reliability."""
        print(f"📸 Capturing {self.display} to {output_path}...")
        try:
            # Try scrot first for Xvfb compatibility
            cmd = f"DISPLAY={self.display} scrot -o {output_path}"
            subprocess.run(cmd, shell=True, check=True)
        except:
            # Fallback to mss if scrot fails
            with mss.mss(display=self.display) as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                img.save(output_path)
        
        return output_path

    def stop(self):
        """Kills the virtual display."""
        if self.xvfb_proc:
            self.xvfb_proc.terminate()
            print(f"🛑 Ghost Display {self.display} stopped.")

if __name__ == "__main__":
    import sys
    ghost = AgentLinkGhost()
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "start":
            ghost.start()
        elif action == "launch":
            ghost.run_app(" ".join(sys.argv[2:]))
        elif action == "capture":
            print(ghost.capture())
