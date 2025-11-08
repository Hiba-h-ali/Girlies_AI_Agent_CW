from domain import ai_agent 
from fastapi import APIRouter

router = APIRouter()

@router.post('/ai-agent-message')
def ai_agent_message(message: str,session_id: str = None):
    return ai_agent.AiAgent(message=message, session_id=session_id).generate_response()