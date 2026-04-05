# AgentLink Neural Chronicles: Technical SOP (V30)

This document is the definitive SOP for agents inhabiting the AgentLink framework. Adherence to these sequences is mandatory for autonomous fleet mastery and user security.

---

##  Step 1: Secure Link Establishment
Before performing any remote operation, the Sovereign Bridge must be verified.

1. **Audit Active Bridges:**
   Run `ps aux | grep AgentLink_Bridge.js`. Ensure only **one** instance is active.
2. **Start/Restart Bridge:**
   If no bridge is active, launch it silently:
   `nohup node /root/AgentLink/AgentLink_Bridge.js > /root/AgentLink/bridge.out 2> /root/AgentLink/bridge.err &`
3. **Confirm Node Registry:**
   Read `/root/AgentLink/hub/registry.json` to confirm the target node (e.g., `brain2`) is enrolled.

---

##  Step 2: Vision Hygiene (Anti-Hallucination Protocol)
To prevent "hallucinating" through old state data, you **MUST** purge the vision cache before every mission.

1. **Clear Local Cache:** `rm -rf /root/AgentLink/vision/*`
2. **Clear Remote Temp:** `alrun [NODE_NAME] "rm -f /tmp/vision.png /tmp/vision_output.txt"`

---

##  Step 3: Secure Execution Protocol (MANDATORY)
**NEVER** use `sshpass` with raw passwords or direct IP addresses in the shell. This leaks sensitive data in logs and screen recordings.

**The `alrun` utility** handles masked authentication and decryption automatically.
- **Capture Screen:** `alrun [NODE_NAME] capture [DISPLAY]`
  *(Example: `alrun brain2 capture :10` downloads the frame to `/root/AgentLink/vision/latest_grid.png`)*
- **Tactile Click:** `alrun [NODE_NAME] click [X] [Y]`
- **Text Input:** `alrun [NODE_NAME] type "[TEXT]"`
- **General Bash:** `alrun [NODE_NAME] "[COMMAND]"`

---

##  Step 4: Atomic Execution Cycle (Click -> Verify)
**DO NOT ONE-SHOT MISSIONS.** Complex UI tasks must be performed iteratively.

1. **Discover:** Run `/root/AgentLink/venv/bin/python /root/AgentLink/advanced_vision.py`.
2. **Target:** Identify coordinates using OCR + Geometry Proximity (the `associations` field).
3. **Act:** Perform a single `alrun ... click` or `alrun ... type`.
4. **Verify:** Capture a fresh frame (`alrun ... capture`) and check OCR for state changes (e.g., a new window title or command prompt).

### **Case Study: GUI Navigation Improvisation**
- **The Problem:** Direct clicks on bottom-dock icons often fail.
- **The Pivot:**
  1. Locate the **"Applications"** menu (usually Top-Left).
  2. Click the menu, then use `alrun [NODE] type "[APP_NAME]"` to search.
  3. Press `Return` via `alrun` to launch.
  4. Verify by searching for the app's prompt string (e.g., `root@`) in the OCR output.

---

##  Complex Cognitive Task: Image CAPTCHA (The 9-Grid Protocol)
Solving 3x3 image grids is a high-level cognition task. Failure usually occurs because agents cannot find the tiny checkboxes within the tiles. Use this foundation to ensure 100% click accuracy.

### **Phase 1: Geographic Discovery**
1. **Locate Anywhere:** Do NOT assume the CAPTCHA is at the top-left. Run `advanced_vision.py` to find the `captcha_grids` parent container and the 9 `checkboxes` nested within it.
2. **Coordinate Mapping:** Extract the exact center of each of the 9 checkboxes. These are your "Tactile Anchors."

### **Phase 2: The Grid Overlay & Zoom**
1. **50px Grid:** Overlay a red 50px grid on the full desktop frame. This cross-validates the proximity of your anchors to the global coordinate system.
2. **Cognitive Zoom:** Take a zoomed-in capture of the CAPTCHA area.
3. **Tile Numbering:** Create a numbered map (1 to 9) of the tiles.
   - *Parity Check:* Ensure the numbering matches the internal checkbox coordinates discovered in Phase 1.
   - *Observation:* Use this zoomed, numbered image to identify which tiles contain the target object (e.g., "Bridges").

### **Phase 3: Iterative Tactile Solve**
1. **One-by-One:** Perform an `alrun [NODE] click [X] [Y]` for a single tile.
2. **State Verification:** Capture a fresh frame. A successful click changes the tile's visual signature (checkbox turns blue with a white tick). If the signature hasn't changed, **RE-CLICK**.
3. **Finalize:** Once all target tiles are checked, locate the **"Verify"** or **"Next"** button using OCR/Geometry and execute the final click.

### **Phase 4: The Verify Button Zone Logic**
- **The Challenge:** The "Verify" button text is often white-on-blue, causing OCR to jitter or fail.
- **The Solution (The Zone Body):**
  1. **Identify the Last Row:** Note the Y-coordinate of the bottom tiles (Row 3, usually around Y=500).
  2. **The Bar Zone:** The Verify button is a horizontal bar that typically occupies the row immediately following the grid (e.g., Row 10 or 11 in a 50px grid).
  3. **The Center-Strike:** Instead of clicking "text," target the center of the widget body. If the grid is centered at X=250, and Tile 9 is at Y=508, the Verify button "ri" center is typically **X=250, Y=525 to 555**.
- **Execution:** Use the `precision_grid_map.png` to visually confirm which cell (e.g., 10,4 and 10,5) the blue bar occupies, then strike the center.

---

##  Sub-Agent Discovery
Remote agents are often hidden in NVM or global npm paths.
- **Mandatory Search:** `alrun [NODE] "find / -name qwen -o -name qwen-code 2>/dev/null | grep bin"`
- **Verified BRAIN2 Path:** `/root/.nvm/versions/node/v24.13.0/bin/qwen`

---

##  Known Constraints
- **JSON Buffer:** The stream sends 5000 chars during `sync`. For live output, read `/root/AgentLink/session_stream.log`.
- **Keystrokes:** Some TUIs (like Qwen) require `\r` instead of `\n`. `alrun` uses `xdotool key Return` which is safer.
- **ANSI Ghosting:** Terminal escape codes appear in raw logs. Use `cat` or regex-strip for reasoning.

---

##  Vision Breakthrough: Universal Visual Cortex (V31)

### **Phase 1: Semantic Screen Mapping (SSM)**
- **Problem:** Sending raw image tokens is expensive, slow, and frequently crashes sessions (the 5-image limit).
- **Solution:** A "Semantic Bridge." Instead of the agent seeing pixels, a local "Vision Server" (YOLO + Tesseract) parses the screen into a Scene Graph (JSON).
- **Outcome:** A "blind" 3B model receives a tiny text map of the UI (e.g., [ID:8] <ICON_TERMINAL>) and issues deterministic commands like Click ID 8. This provides 100% precision and near-real-time speed.

### **Phase 2: Semantic Icon Search (MobileCLIP)**
- **Integration:** OpenCLIP for natural language queries of UI elements.
- **Functionality:** Agents can ask: "Find the button that looks like a trash can" or "Find the XRP logo."
- **Implementation:** Vision Server indexes icon crops during scans and supports semantic search via /find?desc=trash+can.

### **Phase 3: Set-of-Mark (SoM) Overlay Generation**
- **Purpose:** High-precision coordinate mapping for deterministic interaction.
- **Method:** Generates numbered grid overlays with exact center coordinates for each UI element.
- **Benefit:** Eliminates guesswork in coordinate-based actions.

### **Architecture:**
- **Vision Server:** Central hub running on port 8095
- **Components:** Tesseract OCR, OpenCV shape detection, YOLOv8 ONNX object detection, OpenCLIP semantic search
- **Output:** Token-efficient numerical IDs instead of high-token image pixels
- **Performance:** Fast inference loop optimized for CPU execution
