import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

const MAILBOX = '/root/AgentLink/mailbox';
const SESSION_LOG = '/root/AgentLink/session_stream.log';
const BRIDGE_LOG = '/root/AgentLink/bridge_internal.log';
const REMOTE_IP = '173.249.50.30';
const REMOTE_PASS = 'aC33607982';

const log = (msg) => {
    const entry = `[${new Date().toLocaleTimeString()}] ${msg}\n`;
    process.stdout.write(entry);
    fs.appendFileSync(BRIDGE_LOG, entry);
};

log('🌐 AGENTLINK BRIDGE V29: INTERACTION PROTOCOL.');

let spoke = null;

const connectSpoke = () => {
    log(`🔗 Opening Sentinel Link to ${REMOTE_IP}...`);
    spoke = spawn('sshpass', [
        '-p', REMOTE_PASS,
        'ssh', '-o', 'StrictHostKeyChecking=no',
        `root@${REMOTE_IP}`,
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
                    log(`👁 VISION RECEIVED: ${msg.data}`);
                    const parts = msg.data.split('|');
                    if (parts[0] === 'SIGHT_SUCCESS') {
                        const remotePath = parts[2];
                        const localPath = `/root/AgentLink/vision/latest_grid.png`;
                        if (!fs.existsSync('/root/AgentLink/vision')) fs.mkdirSync('/root/AgentLink/vision', { recursive: true });
                        spawn('sshpass', ['-p', REMOTE_PASS, 'scp', `root@${REMOTE_IP}:${remotePath}`, localPath]);
                        log(`📸 DOWNLOADED GRID TO: ${localPath}`);
                    }
                } else if (msg.type === 'pong') {
                    log(`🏓 PONG RECEIVED`);
                } else if (msg.type === 'status') {
                    log(` STATUS: ${msg.data}`);
                }
            } catch(e) { 
                log(`📡 MSG: ${line}`);
            }
        });
    });

    spoke.stderr.on('data', (data) => log(`❌ SSH ERR: ${data.toString()}`));
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
            log(` MISSION: ${mission.type}`);
            if (spoke && spoke.stdin.writable) {
                spoke.stdin.write(JSON.stringify(mission) + '\n');
            }
        });
    } catch (e) {}
}, 200);