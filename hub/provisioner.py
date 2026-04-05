import os
import subprocess
import json
import sys

class Provisioner:
    def __init__(self, registry_path):
        self.registry_path = registry_path

    def run_remote(self, ip, command, user="root"):
        print(f"[*] Executing on {ip}: {command}")
        full_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", f"{user}@{ip}", command]
        result = subprocess.run(full_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[!] Error: {result.stderr}")
        return result.stdout

    def deploy_spoke(self, ip, user="root"):
        print(f"[*] Deploying Spoke to {ip}...")
        
        # 1. Create directory
        self.run_remote(ip, "mkdir -p /root/AgentLink/spoke/agents")
        
        # 2. Copy files (using tar for efficiency)
        local_spoke_path = "/root/AgentLink/spoke"
        cmd = f"tar -czf - -C {local_spoke_path} . | ssh {user}@{ip} 'tar -xzf - -C /root/AgentLink/spoke'"
        subprocess.run(cmd, shell=True)

        # 3. Install dependencies
        setup_script = """
        apt-get update && apt-get install -y python3-pip
        pip3 install fastapi uvicorn
        # Check for NVM
        if [ ! -d "$HOME/.nvm" ]; then
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
            nvm install 24.13.0
            npm install -g @google/generative-ai @gemini/cli qwen-cli # Assuming these are the packages
        fi
        """
        self.run_remote(ip, setup_script)

        # 4. Create Systemd Service
        service_content = f"""[Unit]
Description=AgentLink Spoke Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/AgentLink/spoke
ExecStart=/usr/bin/python3 AgentLink.py
Restart=always

[Install]
WantedBy=multi-user.target
"""
        self.run_remote(ip, f"echo '{service_content}' > /etc/systemd/system/agentlink.service")
        self.run_remote(ip, "systemctl daemon-reload && systemctl enable agentlink && systemctl start agentlink")
        
        print(f"[+] Spoke deployed and started on {ip}")
        self.add_to_registry(ip)

    def add_to_registry(self, ip, name=None):
        if not name:
            name = f"node-{ip.replace('.', '-')}"
        
        with open(self.registry_path, 'r') as f:
            registry = json.load(f)
        
        if any(node['ip'] == ip for node in registry):
            print(f"[!] {ip} already in registry.")
            return

        registry.append({"name": name, "ip": ip, "status": "online"})
        
        with open(self.registry_path, 'w') as f:
            json.dump(registry, f, indent=4)
        print(f"[+] Added {name} ({ip}) to registry.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 provisioner.py <ip>")
        sys.exit(1)
    
    p = Provisioner("/root/AgentLink/hub/registry.json")
    p.deploy_spoke(sys.argv[1])
