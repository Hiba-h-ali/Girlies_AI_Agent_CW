from domain import ai_agent 
from fastapi import APIRouter

router = APIRouter()

@router.post('/message')
def ai_agent_message(message: str,session_id: str = None, audio_bytes: bytes = None, audio_file_path: str = None):
    return ai_agent.AiAgent(message=message, session_id=session_id, audio_bytes=audio_bytes, audio_file_path=audio_file_path).generate_response()