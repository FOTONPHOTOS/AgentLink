#!/usr/bin/env node
"use strict";

import fs from 'fs';
import crypto from 'crypto';
import chalk from 'chalk';

const VAULT_PATH = "/root/AgentLink/hub/vault.json";
const REGISTRY_PATH = "/root/AgentLink/hub/registry.json";
const MASTER_SECRET = "agentlink_secret_123_neural_key_master";

/**
 * NEURAL VAULT: AES-256-GCM Encryption
 */
export class Vault {
    static encrypt(text) {
        const iv = crypto.randomBytes(16);
        const salt = crypto.randomBytes(16);
        const key = crypto.scryptSync(MASTER_SECRET, salt, 32);
        const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
        let encrypted = cipher.update(text, 'utf8', 'hex');
        encrypted += cipher.final('hex');
        const tag = cipher.getAuthTag().toString('hex');
        return `${iv.toString('hex')}:${salt.toString('hex')}:${tag}:${encrypted}`;
    }

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
}

/**
 * NEURAL SANITIZER: Redacts sensitive patterns from logs/errors
 */
export class Sanitizer {
    static scrub(text) {
        if (!text || typeof text !== 'string') return text;
        
        // Redact sshpass -p "password"
        let scrubbed = text.replace(/sshpass -p\s+["'].*?["']/gi, 'sshpass -p "********"');
        
        // Redact any long strings that look like API Keys or Auth tokens
        scrubbed = scrubbed.replace(/(AIza[0-9A-Za-z-_]{35})/g, 'GOOGLE_API_KEY_REDACTED');
        
        // Redact potential passwords in CLI commands
        scrubbed = scrubbed.replace(/password[:=]\s*\S+/gi, 'password=REDACTED');
        
        return scrubbed;
    }
}

export function loadRegistry() {
    if (!fs.existsSync(REGISTRY_PATH)) {
        fs.writeFileSync(REGISTRY_PATH, JSON.stringify([{ name: "local-node", ip: "127.0.0.1" }], null, 2));
    }
    return JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
}

export function saveRegistry(nodes) {
    fs.writeFileSync(REGISTRY_PATH, JSON.stringify(nodes, null, 2));
}

export function loadVault() {
    if (!fs.existsSync(VAULT_PATH)) return {};
    return JSON.parse(fs.readFileSync(VAULT_PATH, 'utf8'));
}

export function saveToVault(nodeName, credentials) {
    const vault = loadVault();
    vault[nodeName] = {
        user: credentials.user,
        pass: Vault.encrypt(credentials.pass)
    };
    fs.writeFileSync(VAULT_PATH, JSON.stringify(vault, null, 2));
}

export async function enrollNode(ip, name, user, pass) {
    const nodes = loadRegistry();
    if (nodes.find(n => n.name.toLowerCase() === name.toLowerCase())) return { error: "Name exists" };
    nodes.push({ name, ip, status: "ENROLLED", active_model: "---" });
    saveRegistry(nodes);
    saveToVault(name, { user, pass });
    return { status: "success" };
}

export function deleteNode(name) {
    let nodes = loadRegistry();
    nodes = nodes.filter(n => n.name.toLowerCase() !== name.toLowerCase());
    saveRegistry(nodes);
    const vault = loadVault();
    if (vault[name]) {
        delete vault[name];
        fs.writeFileSync(VAULT_PATH, JSON.stringify(vault, null, 2));
    }
    return { status: "success" };
}

/**
 * SURGICAL UPDATE: Handles individual field modifications
 */
export function updateNode(oldName, field, newValue) {
    const nodes = loadRegistry();
    const node = nodes.find(n => n.name.toLowerCase() === oldName.toLowerCase());
    if (!node) return { error: "Node not found" };

    const vault = loadVault();
    const creds = vault[oldName] || { user: 'root', pass: '' };

    if (field === 'name') {
        if (nodes.find(n => n.name.toLowerCase() === newValue.toLowerCase())) return { error: "New name already exists" };
        node.name = newValue;
        vault[newValue] = vault[oldName];
        delete vault[oldName];
    } else if (field === 'ip') {
        node.ip = newValue;
    } else if (field === 'user') {
        creds.user = newValue;
        vault[oldName] = { user: creds.user, pass: creds.pass }; // pass is already encrypted in vault
    } else if (field === 'pass') {
        vault[oldName] = { user: creds.user, pass: Vault.encrypt(newValue) };
    }

    saveRegistry(nodes);
    fs.writeFileSync(VAULT_PATH, JSON.stringify(vault, null, 2));
    return { status: "success" };
}