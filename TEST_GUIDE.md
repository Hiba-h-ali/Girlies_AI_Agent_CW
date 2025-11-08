# AI Agent Endpoint Test Guide

## Prerequisites
1. Start the server: `python3 main.py`
2. Server should be running on `http://127.0.0.1:8000`

## Test Cases

### Test 1: Text Message (JSON)
```bash
curl -X POST "http://127.0.0.1:8000/ai-agent/message?session_id=test-001" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "session_id": "test-001"
  }'
```

### Test 2: Text Message (session_id in query only)
```bash
curl -X POST "http://127.0.0.1:8000/ai-agent/message?session_id=test-002" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the weather?"
  }'
```

### Test 3: Recorded Audio (Base64)
```bash
# First, encode an audio file to base64
AUDIO_B64=$(base64 -i audio.wav | tr -d '\n')

curl -X POST "http://127.0.0.1:8000/ai-agent/message?session_id=test-003" \
  -H "Content-Type: application/json" \
  -d "{
    \"audio_data\": \"$AUDIO_B64\",
    \"session_id\": \"test-003\"
  }"
```

### Test 4: Audio with Text Message
```bash
AUDIO_B64=$(base64 -i audio.wav | tr -d '\n')

curl -X POST "http://127.0.0.1:8000/ai-agent/message?session_id=test-004" \
  -H "Content-Type: application/json" \
  -d "{
    \"audio_data\": \"$AUDIO_B64\",
    \"message\": \"This is a voice message\",
    \"session_id\": \"test-004\"
  }"
```

### Test 5: File Upload (multipart/form-data)
```bash
curl -X POST "http://127.0.0.1:8000/ai-agent/message?session_id=test-005" \
  -F "audio_file=@audio.wav" \
  -F "message=Uploaded audio file"
```

### Test 6: File Upload (audio only)
```bash
curl -X POST "http://127.0.0.1:8000/ai-agent/message?session_id=test-006" \
  -F "audio_file=@audio.wav"
```

### Test 7: Empty Request (should fail with 400)
```bash
curl -X POST "http://127.0.0.1:8000/ai-agent/message" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Test 8: Invalid Base64 (should fail with 400)
```bash
curl -X POST "http://127.0.0.1:8000/ai-agent/message?session_id=test-008" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "invalid-base64!!!"
  }'
```

## Running Automated Tests

Run the automated test suite:
```bash
python3 test_endpoint.py
```

This will test all cases automatically and provide a summary.

## Expected Responses

### Success Response (200 OK)
```json
{
  "response": "AI agent response text",
  "session_id": "session-id-here"
}
```

### Error Response (400 Bad Request)
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Notes

- Audio files should be in WAV format, LINEAR16 encoding, 16kHz sample rate
- Session ID can be provided in query parameter or JSON body
- For base64 audio, remove the `data:audio/wav;base64,` prefix if present
- All audio inputs are processed by Dialogflow CX

