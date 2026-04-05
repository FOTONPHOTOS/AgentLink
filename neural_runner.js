import fs from 'fs';
import crypto from 'crypto';
import { execSync } from 'child_process';

const MISSION_PATH = '/root/AgentLink/mission.json';
const RESULT_PATH = '/root/AgentLink/result.json';
const MASTER_SECRET = 'agentlink_secret_123_neural_key_master';

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

console.log(' NEURAL RUNNER: High-Speed Sovereign Driver Active.');

// SINGLE-MISSION OPTION: Allows external agents to run once and exit
if (process.argv.includes('--once')) {
    process.on('exit', () => console.log(' Mission Complete. Driver Exiting.'));
}

setInterval(() => {
    if (fs.existsSync(MISSION_PATH)) {
        try {
            const mission = JSON.parse(fs.readFileSync(MISSION_PATH, 'utf8'));
            fs.unlinkSync(MISSION_PATH); 
            
            const creds = getCreds(mission.node);
            if (!creds) throw new Error(`Node ${mission.node} not found.`);

            let cmd = `export DISPLAY=${mission.display || ':10'} && export XAUTHORITY=/root/.Xauthority && `;
            if (mission.type === 'bash') cmd += mission.command;
            else if (mission.type === 'vision') cmd += `scrot /tmp/v.png && tesseract /tmp/v.png /tmp/v -l eng && cat /tmp/v.txt`;
            else if (mission.type === 'macro') cmd += mission.commands.join(' && sleep 1 && ');

            const output = execSync(`sshpass -p "${creds.pass}" ssh -o StrictHostKeyChecking=no ${creds.user}@${creds.ip} '${cmd}'`).toString();
            
            fs.writeFileSync(RESULT_PATH, JSON.stringify({ status: 'success', output: output.trim(), timestamp: Date.now() }));
            
            if (process.argv.includes('--once')) process.exit(0);
            
        } catch (e) {
            fs.writeFileSync(RESULT_PATH, JSON.stringify({ status: 'error', error: e.message }));
            if (process.argv.includes('--once')) process.exit(1);
        }
    }
}, 500);