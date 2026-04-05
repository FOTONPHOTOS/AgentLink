import express from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import { exec } from 'child_process';
import fs from 'fs';
import crypto from 'crypto';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { Client } from 'ssh2';

const CONFIG_PATH = "/root/AgentLink/spoke/neural_config.json";
const REGISTRY_PATH = "/root/AgentLink/hub/registry.json";
const VAULT_PATH = "/root/AgentLink/hub/vault.json";
const MASTER_SECRET = "agentlink_secret_123_neural_key_master";

// --- IMMEDIATE SEEDING ---
if (fs.existsSync(CONFIG_PATH)) {
    const config = JSON.parse(fs.readFileSync(CONFIG_PATH));
    if (config.google_key) process.env.GOOGLE_API_KEY = config.google_key;
}

const app = express();
const port = 8092;
const API_TOKEN = "agentlink_secret_123";

app.use(cors());
app.use(bodyParser.json());

const authenticate = (req, res, next) => {
    if (req.headers.authorization === `Bearer ${API_TOKEN}`) next();
    else res.status(403).json({ error: "Unauthorized" });
};

// --- SOVEREIGN VAULT LOGIC ---
class SovereignVault {
    static decrypt(encText) {
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
    }
    static getCredentials(nodeName) {
        if (!fs.existsSync(VAULT_PATH)) return null;
        const vault = JSON.parse(fs.readFileSync(VAULT_PATH, 'utf8'));
        const reg = JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
        const node = reg.find(n => n.name.toLowerCase() === nodeName.toLowerCase());
        const creds = vault[nodeName];
        if (!node || !creds) return null;
        return { ip: node.ip, user: creds.user, pass: this.decrypt(creds.pass) };
    }
}

let yoloMode = true; 
let messageBuffer = [];
let msgCounter = 0;
let chatHistory = []; 
let currentSubModel = 'gemini-2.0-pro-exp-05-02';

const neuralTools = {
    execute_remote: async (type, args) => {
        const creds = SovereignVault.getCredentials(args.node_name);
        if (!creds) return { error: `Credentials for ${args.node_name} not found.` };
        return new Promise((resolve) => {
            const conn = new Client();
            conn.on('ready', () => {
                let cmd = "";
                if (type === 'read') cmd = `cat '${args.path}'`;
                else if (type === 'bash') cmd = args.command;
                else if (type === 'macro') cmd = `export DISPLAY=:10 && export XAUTHORITY=/root/.Xauthority && ${args.commands.join(' && sleep 1 && ')}`;
                conn.exec(cmd, (err, stream) => {
                    if (err) return resolve({ error: err.message });
                    let output = "";
                    stream.on('close', (code) => { conn.end(); resolve({ output, exitCode: code }); })
                          .on('data', (data) => { output += data; })
                          .stderr.on('data', (data) => { output += data; });
                });
            }).on('error', (err) => resolve({ error: err.message }))
              .connect({ host: creds.ip, port: 22, username: creds.user, password: creds.pass });
        });
    }
};

const toolDeclarations = [
    { name: "agentlink_fleet_map", description: "Map all servers.", parameters: { type: "object", properties: {} } },
    { name: "agentlink_remote_bash", description: "Run command on remote node.", parameters: { type: "object", properties: { node_name: { type: "string" }, command: { type: "string" } }, required: ["node_name", "command"] } },
    { name: "agentlink_remote_macro", description: "Inject GUI sequence on remote server.", parameters: { type: "object", properties: { node_name: { type: "string" }, commands: { type: "array", items: { type: "string" } } }, required: ["node_name", "commands"] } }
];

function pushBlock(type, content, isPending = false) {
    const id = isPending ? 'pending-static' : ++msgCounter;
    const block = { id, type, content, timestamp: Date.now(), isPending };
    if (!isPending) { messageBuffer.push(block); if (messageBuffer.length > 500) messageBuffer.shift(); }
    return block;
}

async function runSovereignAgent(prompt) {
    const apiKey = process.env.GOOGLE_API_KEY;
    if (!apiKey) { pushBlock('SYSTEM', '⚠ NEURAL CORE OFFLINE: RUN /setup IN HUB'); return; }
    try {
        const genAI = new GoogleGenerativeAI(apiKey);
        const model = genAI.getGenerativeModel({ model: currentSubModel, tools: [{ functionDeclarations: toolDeclarations }] });
        const chat = model.startChat({ history: chatHistory });
        pushBlock('USER', prompt);
        let result = await chat.sendMessageStream(prompt);
        let fullText = "";
        for await (const chunk of result.stream) { fullText += chunk.text(); app.locals.pendingText = fullText; }
        const response = await result.response;
        const calls = response.functionCalls();
        if (calls && calls.length > 0) {
            for (const call of calls) {
                pushBlock('ACTION', ` SOVEREIGN: ${call.name}`);
                let res;
                if (call.name === 'agentlink_fleet_map') { res = { fleet: JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8')) }; }
                else { res = await neuralTools.execute_remote(call.name.split('_').pop(), call.args); }
                const nextResult = await chat.sendMessage([{ functionResponse: { name: call.name, response: res } }]);
                pushBlock('AGENT', nextResult.response.text());
            }
        } else { pushBlock('AGENT', fullText); }
        chatHistory = await chat.getHistory();
    } catch (e) { pushBlock('SYSTEM', `Neural Error: ${e.message}`); }
    finally { app.locals.pendingText = ""; }
}

app.post('/prompt', authenticate, async (req, res) => { runSovereignAgent(req.body.text); res.json({ status: "processing" }); });
app.get('/logs', authenticate, (req, res) => {
    const current = app.locals.pendingText ? [{ id: 'pending-static', type: 'AGENT', content: app.locals.pendingText, isPending: true }] : [];
    res.json([...messageBuffer, ...current]);
});
app.get('/status', authenticate, (req, res) => { res.json({ active_model: "gemini", sub_model: currentSubModel, yolo_mode: yoloMode, authenticated: !!process.env.GOOGLE_API_KEY }); });

app.listen(port, '0.0.0.0', () => { console.log(`AgentLink Sovereign Spoke (V13.2) listening on port ${port}`); });
