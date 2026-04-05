import fs from 'fs';
import crypto from 'crypto';
import { execSync } from 'child_process';

const MISSION_PATH = '/root/AgentLink/mission.json';
const RESULT_PATH = '/root/AgentLink/result.json';
const MASTER_SECRET = 'agentlink_secret_123_neural_key_master';

/**
 * NEURAL SANITIZER: Redacts secrets from logs
 */
class Sanitizer {
    static scrub(text) {
        if (!text || typeof text !== 'string') return text;
        return text
            .replace(/sshpass -p\s+["'].*?["']/gi, 'sshpass -p "********"')
            .replace(/(AIza[0-9A-Za-z-_]{35})/g, 'GOOGLE_API_KEY_REDACTED')
            .replace(/password[:=]\s*\S+/gi, 'password=REDACTED');
    }
}

const decrypt = (encText) => {
    if (!encText || !encText.includes(':')) return "";
    const [ivHex, saltHex, tagHex, encrypted] = encText.split(':');
    const iv = Buffer.from(ivHex, 'hex');
    const salt = Buffer.from(saltHex, 'hex');
    const tag = Buffer.from(tagHex, 'hex');
    const key = crypto.scryptSync(MASTER_SECRET, salt, 32);
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
    decipher.setAuthTag(tag);
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
};

const getCreds = (nodeName) => {
    const vault = JSON.parse(fs.readFileSync('/root/AgentLink/hub/vault.json', 'utf8'));
    const reg = JSON.parse(fs.readFileSync('/root/AgentLink/hub/registry.json', 'utf8'));
    const node = reg.find(n => n.name.toLowerCase() === nodeName.toLowerCase());
    if (!node || !vault[nodeName]) return null;
    return { ip: node.ip, user: vault[nodeName].user, pass: decrypt(vault[nodeName].pass) };
};

const printLogo = () => {
    const logo = String.raw`
  .───────.   █████   ██████  ███████ ███    ██ ████████ ██      ██ ███    ██ ██   ██       .───────.
  o| o   o |o  ██   ██ ██       ██      ████   ██    ██    ██      ██ ████   ██ ██  ██        o| o   o |o
   |  ───  |   ███████ ██   ███ █████   ██ ██  ██    ██    ██      ██ ██ ██  ██ █████          |  ───  | 
  '───────'  ██   ██ ██    ██ ██      ██  ██ ██    ██    ██      ██ ██  ██ ██ ██  ██        '───────'
   /─────\   ██   ██  ██████  ███████ ██   ████    ██    ███████ ██ ██   ████ ██   ██        /─────\
    `;
    console.log(logo);
};

printLogo();
console.log('\n AGENTLINK DAEMON: High-Speed Autonomous Bridge Active.');
console.log('📍 Listening at: /root/AgentLink/mission.json');
console.log('--------------------------------------------------');

setInterval(() => {
    if (fs.existsSync(MISSION_PATH)) {
        try {
            const mission = JSON.parse(fs.readFileSync(MISSION_PATH, 'utf8'));
            fs.unlinkSync(MISSION_PATH); 
            
            const creds = getCreds(mission.node);
            console.log(`🚀 [${new Date().toLocaleTimeString()}] EXECUTING: ${mission.type} on ${mission.node.toUpperCase()}`);
            
            let cmd = `export DISPLAY=${mission.display || ':10'} && export XAUTHORITY=/root/.Xauthority && `; 
            if (mission.type === 'bash') cmd += mission.command;
            else if (mission.type === 'vision') cmd += `scrot /tmp/vision.png && tesseract /tmp/vision.png /tmp/vision_output -l eng && cat /tmp/vision_output.txt
`;
            else if (mission.type === 'macro') cmd += mission.commands.join(' && sleep 1 && ');

            const output = execSync(`sshpass -p "${creds.pass}" ssh -o StrictHostKeyChecking=no ${creds.user}@${creds.ip} '${cmd}'`).toString();
            
            fs.writeFileSync(RESULT_PATH, JSON.stringify({ status: 'success', output: output.trim(), timestamp: Date.now() }));
            console.log(' MISSION COMPLETE');
            
        } catch (e) {
            const safeError = Sanitizer.scrub(e.message);
            console.error('❌ ERROR:', safeError);
            fs.writeFileSync(RESULT_PATH, JSON.stringify({ status: 'error', error: safeError }));
        }
    }
}, 100);