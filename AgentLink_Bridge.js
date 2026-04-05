import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

const MAILBOX = '/root/AgentLink/mailbox';
const SESSION_LOG = '/root/AgentLink/session_stream.log';
const BRIDGE_LOG = '/root/AgentLink/bridge_internal.log';
const VAULT_PATH = '/root/AgentLink/hub/vault.json';

const log = (msg) => {
    const entry = `[${new Date().toLocaleTimeString()}] ${msg}\n`;
    process.stdout.write(entry);
    fs.appendFileSync(BRIDGE_LOG, entry);
};

log('AGENTLINK BRIDGE V29: INTERACTION PROTOCOL.');

// Load credentials from encrypted vault
const loadVaultCredentials = () => {
    try {
        const vault = JSON.parse(fs.readFileSync(VAULT_PATH, 'utf8'));
        return vault;
    } catch (e) {
        log('ERROR: Could not load vault.json. Ensure credentials are configured.');
        return {};
    }
};

let spoke = null;

const connectSpoke = () => {
    const vault = loadVaultCredentials();
    const nodeName = process.env.AGENTLINK_NODE || 'brain2';
    const nodeConfig = vault[nodeName];
    
    if (!nodeConfig || !nodeConfig.ip || !nodeConfig.pass) {
        log(`ERROR: No configuration found for node '${nodeName}' in vault.json`);
        log('Please configure hub/vault.json with your node credentials.');
        setTimeout(connectSpoke, 10000);
        return;
    }

    log(`Opening Sentinel Link to ${nodeConfig.ip}...`);
    spoke = spawn('sshpass', [
        '-p', nodeConfig.pass,
        'ssh', '-o', 'StrictHostKeyChecking=no',
        `${nodeConfig.user}@${nodeConfig.ip}`,
        'node /root/AgentLink_Spoke.js'
    ]);

    spoke.stdout.on('data', (data) => {
        const raw = data.toString();
        const lines = raw.split('\n');
        lines.forEach(line => {
            if (!line.trim()) return;
            try {
                const msg = JSON.parse(line);
                if (msg.type === 'stream') {
                    fs.appendFileSync(SESSION_LOG, msg.data);
                } else if (msg.type === 'vision_data') {
                    log(`VISION RECEIVED: ${msg.data}`);
                    const parts = msg.data.split('|');
                    if (parts[0] === 'SIGHT_SUCCESS') {
                        const remotePath = parts[2];
                        const localPath = `/root/AgentLink/vision/latest_grid.png`;
                        if (!fs.existsSync('/root/AgentLink/vision')) fs.mkdirSync('/root/AgentLink/vision', { recursive: true });
                        spawn('sshpass', ['-p', nodeConfig.pass, 'scp', `${nodeConfig.user}@${nodeConfig.ip}:${remotePath}`, localPath]);
                        log(`DOWNLOADED GRID TO: ${localPath}`);
                    }
                } else if (msg.type === 'pong') {
                    log(`PONG RECEIVED`);
                } else if (msg.type === 'status') {
                    log(`STATUS: ${msg.data}`);
                }
            } catch(e) {
                log(`MSG: ${line}`);
            }
        });
    });

    spoke.stderr.on('data', (data) => log(`SSH ERR: ${data.toString()}`));
    spoke.on('exit', () => setTimeout(connectSpoke, 3000));
};

connectSpoke();

setInterval(() => {
    try {
        const inbox = path.join(MAILBOX, 'inbox');
        if (!fs.existsSync(inbox)) fs.mkdirSync(inbox, { recursive: true });
        const files = fs.readdirSync(inbox);
        files.forEach(file => {
            if (!file.endsWith('.json')) return;
            const p = path.join(inbox, file);
            const mission = JSON.parse(fs.readFileSync(p, 'utf8'));
            fs.unlinkSync(p);
            log(`MISSION: ${mission.type}`);
            if (spoke && spoke.stdin.writable) {
                spoke.stdin.write(JSON.stringify(mission) + '\n');
            }
        });
    } catch (e) {}
}, 200);
