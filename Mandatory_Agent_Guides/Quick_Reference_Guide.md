# AgentLink Quick Reference Guide

## Essential Commands

### Starting Services
- Start Bridge: `nohup node /root/AgentLink/AgentLink_Bridge.js > /root/AgentLink/bridge.out 2> /root/AgentLink/bridge.err &`
- Start Vision Server: `nohup /root/AgentLink/venv/bin/python /root/AgentLink/vision_server.py > /root/AgentLink/vision_server.out 2> /root/AgentLink/vision_server.err &`

### Checking Service Status
- Bridge: `ps aux | grep AgentLink_Bridge.js`
- Vision Server: `curl "http://localhost:8095/status"`
- All processes: `ps aux | grep -E "(AgentLink|vision_server)"`

### Vision Operations
- Clear cache: `rm -rf /root/AgentLink/vision/*`
- Capture screen: `/root/AgentLink/venv/bin/python /root/AgentLink/alrun.py brain2 capture :10`
- Scan with vision server: `curl "http://localhost:8095/scan?node=brain2&display=:10"`
- Generate overlay: `curl "http://localhost:8095/overlay?node=brain2&display=:10"`

## Critical Path Information
- Virtual Environment Python: `/root/AgentLink/venv/bin/python`
- Vision Server Output: `/root/AgentLink/vision/som_brain2.png`
- Registry: `/root/AgentLink/hub/registry.json`
- Vault: `/root/AgentLink/hub/vault.json`

## Troubleshooting
- If vision server won't start: Use virtual environment Python (`/root/AgentLink/venv/bin/python`)
- If modules missing: Install in virtual env (`/root/AgentLink/venv/bin/pip install [package]`)
- Check error logs: `/root/AgentLink/vision_server.err`