# AgentLink: Distributed AI Agent Orchestration Framework

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AgentLink is a distributed orchestration framework that enables AI agents to remotely control, observe, and interact with multiple servers with full visual and tactile autonomy. It transforms text-only AI models into multi-modal autonomous operators capable of managing entire fleets of remote systems without API dependencies or vision API costs.

---

## Overview

AgentLink provides a sovereign bridge for "possessing" remote environments with complete autonomy. AI agents can:

- **See** - Capture remote screens and extract semantic information via EasyOCR
- **Click** - Interact with UI elements at precise coordinates
- **Type** - Input text into applications, terminals, and forms
- **Execute** - Run commands on remote systems
- **Verify** - Confirm state changes after each action

The framework enables small parameter models (3B-7B) without vision capabilities to perform complex visual tasks locally and for free, eliminating the need for expensive vision API calls ($0.01-0.05 per image).

---

## 🎥 Live Demo

Gemini (text-only LLM) controlling a remote Linux server via **AgentLink** — solving a ReCAPTCHA, launching Chrome, searching Google, and browsing CNN news.

All actions are performed using **local vision only** (EasyOCR + blob detection) with zero paid vision APIs.

[![AgentLink Demo: Gemini Solves CAPTCHA & Browses Internet](https://img.youtube.com/vi/oqaWF77UKIY/0.jpg)](https://youtu.be/oqaWF77UKIY)

**Watch how AgentLink gives text-only models full visual + tactile control over a remote machine.**



## Architecture

```
+------------------+          +------------------+          +------------------+
|   Human (Hub)    |          |  AI Agent (Local)|          |  Remote Node     |
|                  |          |                  |          |  (Spoke)         |
|  agentlink CLI   |          |  Sovereign Bridge|<-------->|  AgentLink.js    |
|  Registry/Vault  |          |  mission.json    |          |  System Access   |
+------------------+          +------------------+          +------------------+
                                       |
                                       v
                              +------------------+
                              |  Vision Server   |
                              |  (EasyOCR:8095)  |
                              |  Screen Capture  |
                              |  Semantic Scan   |
                              +------------------+
```

### Core Components

| Component | Description |
|-----------|-------------|
| **Hub** | Node.js interface for human fleet management. Registry and encrypted vault. |
| **Sovereign Bridge** | Background daemon (`AgentLink_Bridge.js`) for AI mission dispatch via file protocol. |
| **Spoke** | Infrastructure daemon on each remote node providing low-level system access. |
| **Vision Server** | EasyOCR-based screen scanning service (port 8095) with semantic JSON output. |
| **alrun** | CLI utility for remote capture, click, type, and execute operations. |

---

## Key Capabilities

### Visual Autonomy
- Screen capture with EasyOCR semantic scanning (~20-30 seconds per scan)
- Connected Components Analysis (Blob Detection) for icon/button awareness
- Tooltip Fusion - automatic blob-to-text association
- 9-Grid CAPTCHA solving protocol with zoom and iterative verification

### Tactile Autonomy
- Prec coordinate clicking with pixel-level accuracy
- Text input via xdotool
- Command execution on remote nodes
- State verification after each action

### Mission Protocol
- JSON-based mission dispatch (`mission.json` to `result.json`)
- SQLite-backed mission tracking with progress logging
- Active context anchors for agent awareness

### Security
- AES-256-GCM encrypted credential vault
- Masked authentication - no passwords in logs or commands
- Neural sanitizer - automatic token redaction from logs

---

## Use Cases

### Cost-Effective Vision for Text-Only AI
Small parameter models (Smol 3B, Phi-3, etc.) lack vision capabilities. AgentLink's EasyOCR vision server provides screen understanding for free via local CPU inference. Enables $0 vision for budget AI agents.

### Legacy System Automation
Many enterprise systems (old ERPs, mainframes, proprietary software) have no API access. AgentLink interacts with these systems visually - sees the UI, clicks buttons, types inputs, verifies results.

### Remote IT Support
AI agents can remotely capture screens, diagnose issues via OCR, click through menus, run commands, and verify fixes. 24/7 autonomous IT support without human intervention.

### Automated Software Deployment
Deploy software across multiple servers with visual verification at each step. Navigate configuration UIs, verify successful deployment, and rollback on errors.

### Web Application Testing
Resilient testing that adapts to UI changes. Catches visual bugs that code-based tests miss. Sees the actual rendered UI, identifies elements semantically, clicks through workflows.

### Automated Data Entry
Repetitive data entry across multiple web portals or legacy systems. Reads source data, navigates to target forms, fills fields, submits, and verifies success.

### Cross-Platform Workflow Automation
Manages a fleet of heterogeneous nodes (Windows, Linux, web apps), executing steps on each and verifying transitions. End-to-end automation across any combination of systems.

### Compliance & Security Auditing
Captures screens, reads configurations via OCR, verifies security settings, and generates audit reports. Continuous automated compliance monitoring.

### CAPTCHA & Challenge Solving
9-grid protocol with zoom, checkbox detection, and iterative verification solves visual challenges autonomously. Unblocks automated workflows.

### Remote AI Agent Orchestration
Discovers remote AI agents, launches them, sends instructions, and monitors outputs. Distributed AI agent swarms working collaboratively across multiple machines.

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- EasyOCR (for vision server)
- xdotool (for tactile operations)

### Installation

```bash
# Clone repository
git clone https://github.com/FOTONPHOTOS/agentlink.git
cd agentlink

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Node dependencies
npm install
```

### Starting Services

```bash
# Start Sovereign Bridge
nohup node /root/AgentLink/AgentLink_Bridge.js > /root/AgentLink/bridge.out 2> /root/AgentLink/bridge.err &

# Start Vision Server
nohup /root/AgentLink/venv/bin/python /root/AgentLink/vision_server.py > /root/AgentLink/vision.out 2>&1 &

# Verify services
ps aux | grep -E "(AgentLink_Bridge|vision_server)"
curl http://localhost:8095/status
```

### Basic Usage

```bash
# Capture remote screen
alrun brain2 capture :10

# Scan with vision server
curl -s "http://127.0.0.1:8095/deep_scan?node=brain2&display=:10"

# Click on remote screen
alrun brain2 click 250 300

# Type text on remote screen
alrun brain2 type "hello world"

# Execute command on remote node
alrun brain2 "ls -la /root"
```

---

## Agent Protocol

For AI agents using AgentLink, the mandatory operational guide is located at:

**`Mandatory_Agent_Guides/AgentLink_Neural_Chronicles_Updated.md`**

All agents MUST read this document before operating. It contains:
- Identity verification protocols
- Secure link establishment
- Vision hygiene procedures
- Atomic execution cycles
- CAPTCHA solving protocols
- Sub-agent discovery methods
- Known constraints and safety warnings

---

## Project Structure

```
agentlink/
├── AgentLink_Bridge.js          # Sovereign Bridge daemon
├── AgentLink_Daemon.js          # System daemon
├── alrun.py                     # Remote execution utility
├── vision_server.py             # EasyOCR vision server (port 8095)
├── advanced_vision.py           # Advanced vision with blob detection
├── core/
│   ├── mission_control.py       # SQLite mission tracking
│   ├── neural_link.py           # Remote node connection
│   ├── browser_driver.py        # Remote browser automation
│   └── sovereign.py             # High-level plan executor
├── hub/
│   ├── agentlink.js             # Hub TUI interface
│   ├── agentlink.py             # Hub Python interface
│   ├── fleet_manager.js         # Fleet management
│   ├── registry.json            # Node registry
│   └── vault.json               # Encrypted credentials
├── spoke/
│   ├── AgentLink.js             # Spoke daemon
│   ├── AgentLink.py             # Spoke Python interface
│   └── neural_config.json       # Neural configuration
├── Mandatory_Agent_Guides/
│   ├── AgentLink_Neural_Chronicles_Updated.md  # Agent SOP (MANDATORY)
│   └── Quick_Reference_Guide.md # Quick command reference
├── models/                      # Vision models (EasyOCR, etc.)
├── vision/                      # Vision cache (auto-cleared)
└── requirements.txt             # Python dependencies
```

---

## Configuration

### Node Registry (`hub/registry.json`)

```json
{
  "brain2": {
    "ip": "192.168.1.100",
    "display": ":10",
    "status": "active"
  }
}
```

### Vision Server Endpoints

| Endpoint | Description |
|----------|-------------|
| `/status` | Server health check |
| `/deep_scan?node=[NODE]&display=[DISPLAY]` | Full semantic scan with OCR |
| `/scan?node=[NODE]&display=[DISPLAY]` | Quick scan |
| `/overlay?node=[NODE]&display=[DISPLAY]` | Generate visual overlay |

---

## Security

- **NEVER** include server passwords in any file or command
- **ALWAYS** use `alrun` for remote tasks
- **Vision Hygiene** is mandatory: clear vision cache before each mission
- Credentials are AES-256-GCM encrypted in `hub/vault.json`
- Sensitive tokens are automatically redacted from all logs

---

## Performance

| Metric | Value |
|--------|-------|
| Vision scan time | ~20-30 seconds (CPU) |
| Bridge latency | <100ms |
| CPU usage (idle) | <1% |
| Memory usage | ~200MB |

---

## Contributing

Contributions are welcome. Please read our contributing guidelines and submit pull requests.

---

## License

This project is open source and available under the MIT License.

---

## Disclaimer

AgentLink is a powerful automation tool. Users are responsible for ensuring compliance with applicable laws and terms of service when automating interactions with third-party systems.

---

*Last Updated: March 2026*
