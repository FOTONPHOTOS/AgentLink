# AgentLink V27: Sentinel Mesh (Operator Manual)

AgentLink is a distributed framework for **Persistent Agent Inhabitation**. It allows an agent (the "Body") to inhabit a remote node (the "Brain") and control its CLI environment with high-fidelity, real-time feedback.

## 🏗 Architecture
- **Bridge (Local Node):** Manages the SSH tunnels and JSON mission mailbox.
- **Spoke (Remote Node):** Runs the "Sentinel" watcher. Manages a persistent `screen` session.
- **Mailbox:** Atomic filesystem interface at `/root/AgentLink/mailbox/inbox/`.

## 🛰 Operational Flow (For Agents)

### 1. Initialize the Mesh
To inhabit a remote node, drop a `possess` mission into the inbox:
```bash
echo '{"type": "possess", "node": "brain2"}' > /root/AgentLink/mailbox/inbox/p.json
```
*Effect: Spawns `qwen -i` in a remote screen session and begins reactive streaming.*

### 2. Monitor Output (Ears)
Read the reactive stream log. This file updates in real-time as the remote agent types:
```bash
tail -f /root/AgentLink/session_stream.log
```

### 3. Inject Keyboard Input (Voice)
Send text directly to the remote agent's prompt:
```bash
echo '{"type": "input", "node": "brain2", "text": "Create a file named test.txt"}' > /root/AgentLink/mailbox/inbox/i.json
```
*Note: The bridge automatically handles Enter keys and carriage returns.*

### 4. Autonomous Security (The Sentinel Guard)
Remote Spoke V27+ includes **Automatic Auth Injection**. 
- If the remote agent triggers a "WriteFile" or "Bash" security prompt, the Sentinel will **automatically detect it and press "1" (Yes)**.
- **Operator Instruction:** Do not write logic to handle security popups. Assume they are handled.

## ⚙ Registry
- **Node: brain2** | IP: 173.249.50.30 | Agent: Qwen-Code-0.8.1

## 📜 Technical Chronicles
For deep-dive protocol specs and historical validation logs, refer to `AgentLink_Neural_Chronicles.md`.
