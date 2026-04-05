#!/root/AgentLink/venv/bin/python
import os
import json
import sys
import subprocess
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt

# --- Configuration ---
REGISTRY_PATH = "/root/AgentLink/hub/registry.json"
VAULT_PATH = "/root/AgentLink/hub/vault.json"
MASTER_SECRET = "agentlink_secret_123_neural_key_master"
LOCAL_VISION_DIR = "/root/AgentLink/vision"

def decrypt(enc_text):
    if not enc_text or ":" not in enc_text:
        return ""
    try:
        parts = enc_text.split(':')
        iv = bytes.fromhex(parts[0])
        salt = bytes.fromhex(parts[1])
        tag = bytes.fromhex(parts[2])
        encrypted = bytes.fromhex(parts[3])
        
        # Node.js scrypt defaults (from crypto.scryptSync documentation)
        # N=16384, r=8, p=1
        key = scrypt(MASTER_SECRET, salt, 32, N=16384, r=8, p=1)
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted = cipher.decrypt_and_verify(encrypted, tag)
        return decrypted.decode('utf-8')
    except Exception as e:
        # print(f"Decryption Error: {e}")
        return ""

def get_creds(node_name):
    if not os.path.exists(VAULT_PATH) or not os.path.exists(REGISTRY_PATH):
        return None
    with open(REGISTRY_PATH, 'r') as f:
        registry = json.load(f)
    with open(VAULT_PATH, 'r') as f:
        vault = json.load(f)
    
    node = next((n for n in registry if n['name'].lower() == node_name.lower()), None)
    if not node or node_name not in vault:
        return None
    
    return {
        "ip": node['ip'],
        "user": vault[node_name]['user'],
        "pass": decrypt(vault[node_name]['pass'])
    }

def run_ssh(creds, command):
    # Masking for terminal safety
    # The actual execution uses the real password, but the command logged by the OS is shorter
    ssh_cmd = [
        "sshpass", "-p", creds['pass'],
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"{creds['user']}@{creds['ip']}",
        command
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    return result

def main():
    if len(sys.argv) < 3:
        print("Usage: alrun <node_name> <command|capture|click>")
        sys.exit(1)

    node_name = sys.argv[1]
    action = sys.argv[2]
    
    creds = get_creds(node_name)
    if not creds:
        print(f"Error: Node '{node_name}' not found in registry/vault.")
        sys.exit(1)
    
    # DEBUG (Remove later)
    # print(f"DEBUG: Decrypted Pass: {creds['pass']}")

    elif action == "capture":
        display = sys.argv[3] if len(sys.argv) > 3 else ":10"
        remote_path = "/tmp/vision.png"
        if not os.path.exists(LOCAL_VISION_DIR): os.makedirs(LOCAL_VISION_DIR, exist_ok=True)
        local_path = os.path.join(LOCAL_VISION_DIR, "latest_grid.png")
        
        # 1. Take Screenshot
        run_ssh(creds, f"export DISPLAY={display} && scrot -o {remote_path}")
        # 2. Download
        scp_cmd = ["sshpass", "-p", creds['pass'], "scp", "-o", "StrictHostKeyChecking=no", f"{creds['user']}@{creds['ip']}:{remote_path}", local_path]
        subprocess.run(scp_cmd)
        if os.path.exists(local_path):
            print(f"Captured screen from {node_name} to {local_path}")
        else:
            print(f"Error: Failed to download screenshot from {node_name}")

    elif action == "upload":
        if len(sys.argv) < 5:
            print("Usage: alrun <node> upload <local_path> <remote_path>")
            sys.exit(1)
        local_path = sys.argv[3]
        remote_path = sys.argv[4]
        
        if not os.path.exists(local_path):
            print(f"Error: Local file '{local_path}' not found.")
            sys.exit(1)

        scp_cmd = ["sshpass", "-p", creds['pass'], "scp", "-o", "StrictHostKeyChecking=no", local_path, f"{creds['user']}@{creds['ip']}:{remote_path}"]
        res = subprocess.run(scp_cmd, capture_output=True, text=True)
        
        if res.returncode == 0:
            print(f"Uploaded {local_path} to {node_name}:{remote_path}")
        else:
            print(f"Upload failed: {res.stderr}")

    elif action == "click":
        if len(sys.argv) < 5:
            print("Usage: alrun <node> click <x> <y>")
            sys.exit(1)
        x, y = sys.argv[3], sys.argv[4]
        display = ":10"
        run_ssh(creds, f"export DISPLAY={display} && xdotool mousemove {x} {y} click 1")
        print(f"Clicked {x}, {y} on {node_name}")

    elif action == "type":
        if len(sys.argv) < 4:
            print("Usage: alrun <node> type '<text>'")
            sys.exit(1)
        text = sys.argv[3]
        display = ":10"
        run_ssh(creds, f"export DISPLAY={display} && xdotool type \"{text}\" && xdotool key Return")
        print(f"Typed text on {node_name}")

    else:
        # Default bash execution
        res = run_ssh(creds, action)
        if res.stdout: print(res.stdout.strip())
        if res.stderr: print(res.stderr.strip(), file=sys.stderr)

if __name__ == "__main__":
    main()
