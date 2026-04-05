const fs = require('fs');
const { execSync } = require('child_process');
const MISSION = '/root/AgentLink/mission.json';
const RESULT = '/root/AgentLink/result.json';

if (fs.existsSync(MISSION)) {
    try {
        const mission = JSON.parse(fs.readFileSync(MISSION, 'utf8'));
        fs.unlinkSync(MISSION);
        // We reuse our existing Overlord logic but in a cron-safe wrapper
        execSync('node /root/AgentLink/neural_runner.js'); 
    } catch (e) {}
}
