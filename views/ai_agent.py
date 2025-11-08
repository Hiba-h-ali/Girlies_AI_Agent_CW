from domain import ai_agent 
from fastapi import APIRouter, File, UploadFile, Form, Query, Body, Request
from typing import Optional
from pydantic import BaseModel
import base64
import json

router = APIRouter()

class MessageRequest(BaseModel):
    message: Optional[str] = None
    audio_data: Optional[str] = None  # Base64 encoded audio
    session_id: Optional[str] = None

@router.post('/message')
async def ai_agent_message(
    request: Request,
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
    from fastapi import HTTPException
    
    audio_bytes = None
    audio_file_path = None
    final_message = ""
    final_session_id = session_id
    
    # Check content type to determine how to parse the request
    content_type = request.headers.get("content-type", "")
    
    # Handle JSON body (for text or base64 audio)
    if "application/json" in content_type:
        try:
            body = await request.json()
            json_request = MessageRequest(**body)
            
            # Handle base64 audio data
            if json_request.audio_data:
                try:
                    audio_bytes = base64.b64decode(json_request.audio_data)
                    final_message = json_request.message or ""
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {str(e)}")
            # Handle text message
            elif json_request.message:
                final_message = json_request.message
            
            # Use session_id from JSON body if provided
            if json_request.session_id:
                final_session_id = json_request.session_id
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")
    
    # Handle form data (for file uploads or form-based text)
    elif "multipart/form-data" in content_type or message:
        if message:
            final_message = message
    
    # Handle audio file upload
    if audio_file:
        audio_bytes = await audio_file.read()
        # If message is not provided, use empty string (audio-only)
        if not final_message:
            final_message = ""
    
    # Validate that either message or audio is provided
    if not final_message and not audio_bytes:
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