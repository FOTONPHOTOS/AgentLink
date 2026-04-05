import logging
import asyncio
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from contextlib import asynccontextmanager
from agents.gemini_cli import GeminiAgent
from agents.qwen_cli import QwenAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AgentLink')

# Registry
AGENT_MODELS = {
    'gemini': GeminiAgent(),
    'qwen': QwenAgent()
}

active_model = 'gemini'

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('🚀 AgentLink Spoke starting. Waiting for manual initialization.')
    yield
    logger.info('Shutting down Spoke.')

app = FastAPI(lifespan=lifespan)
security = HTTPBearer()
API_TOKEN = "agentlink_secret_123"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return credentials.credentials

@app.get('/status', dependencies=[Depends(verify_token)])
def get_status():
    agent = AGENT_MODELS[active_model]
    return {
        'active_model': active_model, 
        'available': list(AGENT_MODELS.keys()),
        'started': agent.started
    }

@app.post('/start', dependencies=[Depends(verify_token)])
def start_agent():
    agent = AGENT_MODELS[active_model]
    if not agent.started:
        agent.start()
        return {'status': f'{active_model} started'}
    return {'status': f'{active_model} already running'}

@app.post('/switch', dependencies=[Depends(verify_token)])
async def switch_model(request: Request):
    global active_model
    data = await request.json()
    new_model = data.get('model')
    if new_model in AGENT_MODELS:
        active_model = new_model
        return {'status': f'switched to {new_model}'}
    return {'error': 'Invalid model'}, 400

@app.post('/prompt', dependencies=[Depends(verify_token)])
async def send_prompt(request: Request):
    data = await request.json()
    msg = data.get('text', '')
    AGENT_MODELS[active_model].send_text(msg)
    return {'status': 'sent', 'model': active_model}

@app.post('/key', dependencies=[Depends(verify_token)])
async def send_key(request: Request):
    data = await request.json()
    key = data.get('key', '')
    AGENT_MODELS[active_model].send_key(key)
    return {'status': 'key_sent'}

@app.get('/logs', dependencies=[Depends(verify_token)])
def get_logs_endpoint():
    return PlainTextResponse(AGENT_MODELS[active_model].get_logs())

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8092)
