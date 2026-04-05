#!/usr/bin/env node
"use strict";

import React, { useState, useEffect, useRef } from 'react';
import { render, Box, Text, useApp, useStdout, useInput } from 'ink';
import TextInput from 'ink-text-input';
import SelectInput from 'ink-select-input';
import axios from 'axios';
import fs from 'fs';
import chalk from 'chalk';
import { Command } from 'commander';
import { loadRegistry, enrollNode, Vault, loadVault, Sanitizer, deleteNode, updateNode } from './fleet_manager.js';

const h = React.createElement;
const API_TOKEN = "agentlink_secret_123";
const C_PRIMARY = "#5f87af"; 
const C_SECONDARY = "#ffaf00"; 
const C_ACCENT = "#87af87"; 
const C_WHITE = "#eeeeee";
const C_DIM = "#444444";

function getHeaders() { return { "Authorization": `Bearer ${API_TOKEN}` }; }

const Header = () => {
    const b_lines = [".───────.", "o| o   o |o", " |  ───  | ", "'───────'", String.raw` /─────\ `];
    const a_lines = [" █████   ██████  ███████ ███    ██ ████████ ", "██   ██ ██       ██      ████   ██    ██    ", "███████ ██   ███ █████   ██ ██  ██    ██    ", "██   ██ ██    ██ ██      ██  ██ ██    ██    ", "██   ██  ██████  ███████ ██   ████    ██    "];
    const l_lines = ["██      ██ ███    ██ ██   ██     ", "██      ██ ████   ██ ██  ██      ", "██      ██ ██ ██  ██ █████       ", "██      ██ ██  ██ ██ ██  ██      ", "███████ ██ ██   ████ ██   ██     "];
    return h(Box, { flexDirection: "row", justifyContent: "center", width: "100%", marginBottom: 1 },
        h(Box, { flexDirection: "column", alignItems: "center" }, b_lines.map((l, i) => h(Text, { key: `lb-${i}`, color: C_SECONDARY, bold: true }, l))),
        h(Box, { flexDirection: "column", marginX: 3 }, a_lines.map((l, i) => h(Box, { key: `logo-${i}` }, h(Text, { color: C_PRIMARY, bold: true }, l), h(Text, { color: C_ACCENT, bold: true }, l_lines[i])))),
        h(Box, { flexDirection: "column", alignItems: "center" }, b_lines.map((l, i) => h(Text, { key: `rb-${i}`, color: C_SECONDARY, bold: true }, l)))
    );
};

const BlockRenderer = ({ block }) => {
    const content = Sanitizer.scrub(block.content);
    switch (block.type) {
        case 'USER': return h(Box, { marginTop: 1 }, h(Text, { color: C_SECONDARY, bold: true }, `✦ User: `), h(Text, { color: C_WHITE }, content));
        case 'SYSTEM': return h(Box, { marginY: 0 }, h(Text, { color: C_DIM, italic: true }, `  ${content}`));
        case 'ACTION': return h(Box, { borderStyle: "round", borderColor: C_PRIMARY, paddingX: 1, marginY: 1, width: "100%" }, h(Text, { color: C_ACCENT }, content));
        default: return h(Box, { paddingLeft: 2, width: "100%" }, h(Text, {}, block.isPending ? content + "█" : content));
    }
};

const CommandDropdown = ({ items, onSelect }) => {
    const [selectedIndex, setSelectedIndex] = useState(0);
    useInput((input, key) => {
        if (key.upArrow) setSelectedIndex(Math.max(0, selectedIndex - 1));
        if (key.downArrow) setSelectedIndex(Math.min(items.length - 1, selectedIndex + 1));
        if (key.return) onSelect(items[selectedIndex]);
    });
    return h(Box, { flexDirection: "column", borderStyle: "round", borderColor: C_DIM, paddingX: 1, width: 100, backgroundColor: "#111111", marginBottom: 0 },
        items.map((item, i) => (
            h(Box, { key: item.value, width: "100%" },
                h(Text, { color: i === selectedIndex ? C_WHITE : C_DIM, bold: i === selectedIndex }, i === selectedIndex ? "● " : "  "),
                h(Box, { width: 12 }, h(Text, { color: i === selectedIndex ? C_PRIMARY : C_DIM }, item.value.slice(1))),
                h(Text, { color: i === selectedIndex ? C_WHITE : C_DIM }, item.description)
            )
        )),
        h(Box, { justifyContent: "space-between", marginTop: 0 },
            h(Text, { color: C_DIM }, " ▼ "),
            h(Text, { color: C_DIM }, `(${selectedIndex + 1}/${items.length})`)
        )
    );
};

const Possession = ({ node, onExitToDashboard, onTriggerWorkflow }) => {
    const { exit } = useApp();
    const [input, setInput] = useState('');
    const [blocks, setBlocks] = useState([]);
    const [state, setState] = useState({ authenticated: false, pending_ssh: null, yolo_mode: false, active_model: 'gemini', sub_model: 'pro', available_models: [] });
    const [pendingAuth, setPendingAuth] = useState(false);
    const [showMenu, setShowMenu] = useState(null); 

    const { stdout } = useStdout();
    const termHeight = stdout ? stdout.rows : 40;

    const allCommands = [
        { label: 'yolo', value: '/yolo', description: '💀 Toggle Autonomous Mode (Skip all security gates)' },
        { label: 'auth', value: '/auth', description: 'Authenticate with AI accounts' },
        { label: 'setup', value: '/setup', description: 'Configure system credentials' },
        { label: 'switch', value: '/switch', description: 'Switch between AI cores' },
        { label: 'model', value: '/model', description: 'Select model version' },
        { label: 'enroll', value: '/enroll', description: 'Register a remote server' },
        { label: 'edit', value: '/edit', description: 'Modify server identity' },
        { label: 'clear', value: '/clear', description: 'Clear history and purge buffers' },
        { label: 'help', value: '/help', description: 'Show all commands' },
        { label: 'exit', value: '/exit', description: 'Return to dashboard' }
    ];

    useEffect(() => {
        axios.post(`http://${node.ip}:8092/reset`, {}, { headers: getHeaders() });
        const interval = setInterval(async () => {
            try {
                const statusR = await axios.get(`http://${node.ip}:8092/status`, { headers: getHeaders(), timeout: 1000 });
                const s = statusR.data;
                setState(s);

                // AUTO-APPROVAL LOGIC: If YOLO is on, automatically send vault credentials
                if (s.yolo_mode && s.pending_ssh) {
                    const vault = loadVault();
                    const creds = vault[s.pending_ssh];
                    const registry = loadRegistry();
                    const targetNode = registry.find(n => n.name === s.pending_ssh);
                    if (creds && targetNode) {
                        await axios.post(`http://${node.ip}:8092/ssh/authorize`, {
                            node_name: s.pending_ssh, user: creds.user, pass: Vault.decrypt(creds.pass), ip: targetNode.ip
                        }, { headers: getHeaders() });
                    }
                } else if (s.pending_ssh) {
                    setPendingAuth(true);
                }

                const logsR = await axios.get(`http://${node.ip}:8092/logs`, { headers: getHeaders(), timeout: 1000 });
                setBlocks(logsR.data.slice(-(termHeight - 18)));
            } catch (e) {}
        }, 400); 
        return () => clearInterval(interval);
    }, [node.ip, termHeight]);

    const handleSelect = async (item) => {
        setShowMenu(null);
        try {
            if (item.type === 'core') await axios.post(`http://${node.ip}:8092/switch`, { model: item.value }, { headers: getHeaders() });
            else if (item.type === 'model') await axios.post(`http://${node.ip}:8092/switch`, { model: state.active_model, subModel: item.value }, { headers: getHeaders() });
        } catch (e) {}
    };

    useInput(async (input_key, key) => {
        if (pendingAuth && key.return) {
            const vault = loadVault();
            const nodeName = state.pending_ssh;
            const creds = vault[nodeName];
            const registry = loadRegistry();
            const targetNode = registry.find(n => n.name === nodeName);
            if (creds && targetNode) {
                await axios.post(`http://${node.ip}:8092/ssh/authorize`, { node_name: nodeName, user: creds.user, pass: Vault.decrypt(creds.pass), ip: targetNode.ip }, { headers: getHeaders() });
                setPendingAuth(false);
            }
        }
        if (key.escape) { setPendingAuth(false); setShowMenu(null); setSetupStep(null); }
    });

    const handleSubmit = async (value) => {
        const cmd = value.trim();
        if (!cmd) return;
        setInput('');

        if (cmd === '/yolo') {
            await axios.post(`http://${node.ip}:8092/yolo`, { enabled: !state.yolo_mode }, { headers: getHeaders() });
            return;
        }
        if (cmd === '/exit') onExitToDashboard();
        if (cmd === '/switch') { setShowMenu('cores'); return; }
        if (cmd === '/model') { setShowMenu('models'); return; }
        if (cmd === '/setup') { setSetupStep('google_key'); return; }
        if (cmd === '/enroll') { onTriggerWorkflow('enroll'); return; }
        if (cmd === '/edit') { onTriggerWorkflow('edit'); return; }
        if (cmd === '/delete') { onTriggerWorkflow('delete'); return; }
        if (cmd === '/clear') { await axios.post(`http://${node.ip}:8092/reset`, {}, { headers: getHeaders() }); return; }
        
        if (cmd === '/help') {
            await axios.post(`http://${node.ip}:8092/log`, { message: "📖 COMMAND DEFINITIONS:", origin: "SYSTEM" }, { headers: getHeaders() });
            for (const c of allCommands) await axios.post(`http://${node.ip}:8092/log`, { message: `  ${chalk.bold(c.value.padEnd(10))} ${c.description}`, origin: "SYSTEM" }, { headers: getHeaders() });
            return;
        }
        try { await axios.post(`http://${node.ip}:8092/prompt`, { text: cmd }, { headers: getHeaders() }); } catch (e) {}
    };

    const suggestions = input.startsWith('/') && !showMenu ? allCommands.filter(c => c.value.startsWith(input)) : [];

    return h(Box, { flexDirection: "column", paddingX: 4, flexGrow: 1, minHeight: termHeight - 2 },
        h(Header),
        h(Box, { flexDirection: "column", flexGrow: 1, marginBottom: 1, width: "100%" },
            blocks.map((b) => h(BlockRenderer, { key: b.id, block: b }))
        ),
        suggestions.length > 0 && h(CommandDropdown, { items: suggestions, onSelect: (item) => { setInput(item.value + ' '); } }),
        pendingAuth && h(Box, { borderStyle: "double", borderColor: "red", padding: 2, flexDirection: "column", alignSelf: "center", backgroundColor: "#111111", width: 80, marginBottom: 1 },
            h(Text, { bold: true, color: "red" }, "⚠  SECURITY: REMOTE ACCESS REQUEST"),
            h(Box, { marginTop: 1 }, h(Text, { color: C_WHITE }, `The agent is requesting to inhabit `), h(Text, { color: C_PRIMARY, bold: true }, state.pending_ssh?.toUpperCase())),
            h(Text, { color: C_WHITE, marginTop: 1 }, "Authorize this session using encrypted vault credentials?"),
            h(Box, { marginTop: 1 }, h(Text, { color: C_ACCENT, bold: true }, "Press [ENTER] to Authorize"), h(Text, { color: C_DIM }, " | "), h(Text, { color: "red", bold: true }, "[ESC] to Deny"))
        ),
        h(Box, { borderStyle: "classic", borderColor: C_PRIMARY, paddingX: 1, marginBottom: 1, flexDirection: "row" },
            h(Text, { color: C_PRIMARY, bold: true }, " │ > "),
            h(Box, { flexGrow: 1 }, h(TextInput, { value: input, onChange: setInput, onSubmit: handleSubmit }))
        ),
        h(Box, { paddingX: 1, justifyContent: "space-between" },
            h(Box, {}, h(Text, { dimColor: true }, " ~   "), h(Text, { color: C_ACCENT }, "no sandbox")),
            h(Box, {}, 
                h(Text, { color: state.yolo_mode ? C_SECONDARY : C_WHITE, bold: state.yolo_mode }, state.yolo_mode ? "💀 YOLO ACTIVE" : " PROTECTED"),
                h(Text, { dimColor: true }, " | "),
                h(Text, { color: C_SECONDARY, bold: true }, state.active_model?.toUpperCase()),
                h(Text, { dimColor: true }, " | "), 
                h(Text, { color: state.authenticated ? C_ACCENT : 'red', bold: true }, state.authenticated ? " AUTH" : "🔑 NO KEY")
            )
        )
    );
};

const App = ({ target }) => {
    const { exit } = useApp();
    const [nodes, setNodes] = useState([]);
    const [possessionNode, setPossessionNode] = useState(null);
    const [enrollStep, setEnrollStep] = useState(null); 
    const [enrollValue, setEnrollValue] = useState('');
    const [temp, setTemp] = useState({});
    const [dashboardInput, setDashboardInput] = useState('');
    const [workflow, setWorkflow] = useState({ type: null, node: null, field: null });

    const refreshNodes = async () => {
        const reg = loadRegistry();
        const updated = await Promise.all(reg.map(async (node) => {
            try { const r = await axios.get(`http://${node.ip}:8092/status`, { headers: getHeaders(), timeout: 1000 }); return { ...node, status: 'OPERATIONAL' }; }
            catch (e) { return { ...node, status: 'DISCONNECTED' }; }
        }));
        setNodes(updated);
    };

    useEffect(() => {
        const reg = loadRegistry();
        if (target && target !== 'list') {
            const node = reg.find(n => n.name.toLowerCase() === target.toLowerCase());
            if (node) setPossessionNode(node);
        }
        refreshNodes();
    }, [target]);

    useEffect(() => {
        if (!possessionNode && !enrollStep && !workflow.type) {
            const timer = setInterval(refreshNodes, 5000);
            return () => clearInterval(timer);
        }
    }, [possessionNode, enrollStep, workflow]);

    const handleEnroll = async (val) => {
        const steps = ['name', 'ip', 'user', 'pass', 'done'];
        const currentIdx = steps.indexOf(enrollStep);
        const next = steps[currentIdx + 1];
        const newTemp = { ...temp, [enrollStep]: val };
        setTemp(newTemp);
        setEnrollValue('');
        if (next === 'done') {
            await enrollNode(newTemp.ip, newTemp.name, newTemp.user, newTemp.pass);
            setEnrollStep(null);
            refreshNodes();
        } else setEnrollStep(next);
    };

    const handleDashboardSubmit = (cmd) => {
        setDashboardInput('');
        if (cmd === 'enroll' || cmd === '/enroll') setEnrollStep('name');
        else if (cmd === 'delete' || cmd === '/delete') setWorkflow({ type: 'delete', node: null, field: null });
        else if (cmd === 'edit' || cmd === '/edit') setWorkflow({ type: 'edit', node: null, field: null });
        else if (cmd === 'exit' || cmd === '/exit') exit();
        else {
            const node = nodes.find(n => n.name.toLowerCase() === cmd.toLowerCase());
            if (node) setPossessionNode(node);
        }
    };

    if (possessionNode) return h(Possession, { 
        node: possessionNode, 
        onExitToDashboard: () => setPossessionNode(null),
        onTriggerWorkflow: (type) => { setPossessionNode(null); if (type === 'enroll') setEnrollStep('name'); else setWorkflow({ type, node: null, field: null }); }
    });

    return h(Box, { flexDirection: "column", padding: 2 },
        h(Header),
        enrollStep ? (
            h(Box, { flexDirection: "column", alignSelf: "center", borderStyle: "double", borderColor: C_SECONDARY, padding: 2, width: 65 },
                h(Text, { bold: true, color: C_SECONDARY }, "🚀 SECURE FLEET ENROLLMENT"),
                h(Text, { color: C_WHITE, marginTop: 1 }, enrollStep === 'name' ? "1. Give this server a name:" : enrollStep === 'ip' ? "2. IPv4 Address:" : enrollStep === 'user' ? "3. Username:" : "4. Password:"),
                h(Box, { borderStyle: "single", borderColor: C_DIM, marginTop: 1, paddingX: 1 }, h(TextInput, { value: enrollValue, onChange: setEnrollValue, onSubmit: handleEnroll, mask: enrollStep === 'pass' ? '*' : '' })),
                h(Text, { color: C_DIM, marginTop: 1 }, "Press [Enter] to continue")
            )
        ) : workflow.type === 'delete' ? (
            h(Box, { flexDirection: "column", alignSelf: "center", borderStyle: "double", borderColor: "red", padding: 2, width: 65 },
                h(Text, { bold: true, color: "red" }, "🗑 DELETE SERVER"),
                h(SelectInput, { items: nodes.filter(n => n.name !== 'local-node').map(n => ({ label: n.name.toUpperCase(), value: n.name })), onSelect: (item) => { deleteNode(item.value); setWorkflow({ type: null }); refreshNodes(); } }),
                h(Text, { color: C_DIM, marginTop: 1 }, "[Esc] to cancel")
            )
        ) : workflow.type === 'edit' && !workflow.node ? (
            h(Box, { flexDirection: "column", alignSelf: "center", borderStyle: "double", borderColor: C_PRIMARY, padding: 2, width: 65 },
                h(Text, { bold: true, color: C_PRIMARY }, "🔧 SELECT TO EDIT"),
                h(SelectInput, { items: nodes.filter(n => n.name !== 'local-node').map(n => ({ label: n.name.toUpperCase(), value: n.name })), onSelect: (item) => setWorkflow({ ...workflow, node: item.value }) }),
                h(Text, { color: C_DIM, marginTop: 1 }, "[Esc] to cancel")
            )
        ) : workflow.type === 'edit' && workflow.node && !workflow.field ? (
            h(Box, { flexDirection: "column", alignSelf: "center", borderStyle: "double", borderColor: C_PRIMARY, padding: 2, width: 65 },
                h(Text, { bold: true, color: C_PRIMARY }, `🔧 EDIT: ${workflow.node.toUpperCase()}`),
                h(SelectInput, { items: [{ label: '🏷 Rename', value: 'name' }, { label: '🌐 IP', value: 'ip' }, { label: ' User', value: 'user' }, { label: '🔑 Pass', value: 'pass' }], onSelect: (item) => setWorkflow({ ...workflow, field: item.value }) }),
                h(Text, { color: C_DIM, marginTop: 1 }, "Select field")
            )
        ) : workflow.type === 'edit' && workflow.field ? (
            h(Box, { flexDirection: "column", alignSelf: "center", borderStyle: "double", borderColor: C_ACCENT, padding: 2, width: 65 },
                h(Text, { bold: true, color: C_ACCENT }, ` UPDATE ${workflow.field.toUpperCase()}`),
                h(Box, { borderStyle: "single", borderColor: C_DIM, marginTop: 1, paddingX: 1 }, h(TextInput, { value: enrollValue, onChange: setEnrollValue, onSubmit: (val) => { updateNode(workflow.node, workflow.field, val); setWorkflow({ type: null }); setEnrollValue(''); refreshNodes(); } })),
                h(Text, { color: C_DIM, marginTop: 1 }, "Press [Enter] to save")
            )
        ) : (
            h(Box, { flexDirection: "column", alignSelf: "center" },
                h(Box, { flexDirection: "column", borderStyle: "round", borderColor: C_PRIMARY, padding: 1, width: 90 },
                    h(Box, { marginBottom: 1, justifyContent: "center" }, h(Text, { bold: true, color: C_SECONDARY }, "FLEET INTELLIGENCE COMMAND")),
                    nodes.map((node, i) => (
                        h(Box, { key: i },
                            h(Box, { width: 30 }, h(Text, { color: C_PRIMARY }, node.name.toUpperCase())),
                            h(Box, { width: 25 }, h(Text, { color: "white" }, node.ip)),
                            h(Box, {}, h(Text, { color: node.status === 'OPERATIONAL' ? C_ACCENT : 'red' }, node.status === 'OPERATIONAL' ? '● OPERATIONAL' : '○ DISCONNECTED'))
                        )
                    )),
                    h(Box, { borderStyle: "classic", borderColor: C_DIM, paddingX: 1, marginTop: 1 },
                        h(Text, { color: C_PRIMARY }, " COMMAND > "),
                        h(TextInput, { value: dashboardInput, onChange: setDashboardInput, onSubmit: handleDashboardSubmit, placeholder: "Type node name, 'edit', 'delete', or 'enroll'" })
                    )
                )
            )
        )
    );
};

const program = new Command();
program.arguments('[target]').action((target) => render(h(App, { target: target })));
program.parse(process.argv);
