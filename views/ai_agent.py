from domain import ai_agent 
from fastapi import APIRouter, File, UploadFile, Form, Query, Body
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

class TextMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post('/message')
async def ai_agent_message(
    text_request: Optional[TextMessageRequest] = Body(None),
    session_id: Optional[str] = Query(None),
    message: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None)
):
    """
    Handle AI agent messages - supports both text and voice messages.
    
    For text messages (JSON body):
    {
        "message": "Hello",
        "session_id": "optional-session-id"
    }
    
    For voice messages (multipart/form-data):
    - Upload 'audio_file' 
    - Optionally include 'message' in form data
    - session_id can be query parameter or in JSON body
    
    session_id: optional query parameter to maintain conversation context
    """
    audio_bytes = None
    audio_file_path = None
    final_message = ""
    final_session_id = session_id
    
    # Handle JSON body request (text message)
    if text_request:
        final_message = text_request.message
        if text_request.session_id:
            final_session_id = text_request.session_id
    
    # Handle form data (for file uploads or form-based text)
    elif message:
        final_message = message
    
    # Handle audio file upload
    if audio_file:
        audio_bytes = await audio_file.read()
        # If message is not provided, use empty string (audio-only)
        if not final_message:
            final_message = ""
    
    # Validate that either message or audio is provided
    if not final_message and not audio_bytes:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Either 'message' (text) or 'audio_file' (voice) must be provided")
    
    return ai_agent.AiAgent(
        message=final_message,
        session_id=final_session_id,
        audio_bytes=audio_bytes,
        audio_file_path=audio_file_path
    ).generate_response()