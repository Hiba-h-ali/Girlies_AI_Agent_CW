from domain import ai_agent 
from fastapi import APIRouter, File, UploadFile, Form, Query, Body
from typing import Optional
from pydantic import BaseModel
import base64

router = APIRouter()

class TextMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class AudioMessageRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    session_id: Optional[str] = None
    message: Optional[str] = None  # Optional text message along with audio

@router.post('/message')
async def ai_agent_message(
    text_request: Optional[TextMessageRequest] = Body(None),
    audio_request: Optional[AudioMessageRequest] = Body(None),
    session_id: Optional[str] = Query(None),
    message: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None)
):
    """
    Handle AI agent messages - supports text, voice file uploads, and recorded audio.
    
    For text messages (JSON body):
    {
        "message": "Hello",
        "session_id": "optional-session-id"
    }
    
    For recorded audio (JSON body - base64 encoded):
    {
        "audio_data": "base64-encoded-audio-string",
        "session_id": "optional-session-id",
        "message": "optional-text-message"
    }
    
    For voice file uploads (multipart/form-data):
    - Upload 'audio_file' 
    - Optionally include 'message' in form data
    - session_id can be query parameter
    
    session_id: optional query parameter to maintain conversation context
    """
    audio_bytes = None
    audio_file_path = None
    final_message = ""
    final_session_id = session_id
    
    # Handle audio request with base64 encoded audio (for recorded audio)
    if audio_request:
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_request.audio_data)
            if audio_request.message:
                final_message = audio_request.message
            else:
                final_message = ""  # Audio-only request
            if audio_request.session_id:
                final_session_id = audio_request.session_id
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {str(e)}")
    
    # Handle JSON body request (text message only)
    elif text_request:
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
        raise HTTPException(
            status_code=400, 
            detail="Either 'message' (text), 'audio_data' (base64 audio), or 'audio_file' (file upload) must be provided"
        )
    
    return ai_agent.AiAgent(
        message=final_message,
        session_id=final_session_id,
        audio_bytes=audio_bytes,
        audio_file_path=audio_file_path
    ).generate_response()