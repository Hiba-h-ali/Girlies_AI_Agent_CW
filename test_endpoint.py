"""
Test script for /ai-agent/message endpoint
Tests all cases: text messages, recorded audio, and file uploads
"""
import requests
import base64
import json
import os

BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = f"{BASE_URL}/ai-agent/message"

def test_text_message():
    """Test 1: Text message with JSON body"""
    print("\n" + "="*50)
    print("TEST 1: Text Message (JSON)")
    print("="*50)
    
    session_id = "test-session-text-001"
    payload = {
        "message": "Hello, how are you?",
        "session_id": session_id
    }
    
    response = requests.post(
        f"{ENDPOINT}?session_id={session_id}",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_text_message_query_param():
    """Test 2: Text message with session_id in query parameter only"""
    print("\n" + "="*50)
    print("TEST 2: Text Message (session_id in query only)")
    print("="*50)
    
    session_id = "test-session-text-002"
    payload = {
        "message": "What's the weather like?"
    }
    
    response = requests.post(
        f"{ENDPOINT}?session_id={session_id}",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_audio_base64():
    """Test 3: Recorded audio as base64 (mock data)"""
    print("\n" + "="*50)
    print("TEST 3: Recorded Audio (Base64)")
    print("="*50)
    
    # Create a mock audio file (small WAV file header)
    # This is a minimal valid WAV file header
    wav_header = b'RIFF' + (36).to_bytes(4, 'little') + b'WAVE' + b'fmt ' + (16).to_bytes(4, 'little') + \
                 (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') + (16000).to_bytes(4, 'little') + \
                 (32000).to_bytes(4, 'little') + (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + \
                 b'data' + (0).to_bytes(4, 'little')
    
    base64_audio = base64.b64encode(wav_header).decode('utf-8')
    
    session_id = "test-session-audio-001"
    payload = {
        "audio_data": base64_audio,
        "session_id": session_id
    }
    
    response = requests.post(
        f"{ENDPOINT}?session_id={session_id}",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def test_audio_with_text():
    """Test 4: Audio with optional text message"""
    print("\n" + "="*50)
    print("TEST 4: Audio with Text Message")
    print("="*50)
    
    # Mock audio data
    wav_header = b'RIFF' + (36).to_bytes(4, 'little') + b'WAVE' + b'fmt ' + (16).to_bytes(4, 'little') + \
                 (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') + (16000).to_bytes(4, 'little') + \
                 (32000).to_bytes(4, 'little') + (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + \
                 b'data' + (0).to_bytes(4, 'little')
    
    base64_audio = base64.b64encode(wav_header).decode('utf-8')
    
    session_id = "test-session-audio-002"
    payload = {
        "audio_data": base64_audio,
        "message": "This is a voice message",
        "session_id": session_id
    }
    
    response = requests.post(
        f"{ENDPOINT}?session_id={session_id}",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def test_file_upload():
    """Test 5: Audio file upload (if test file exists)"""
    print("\n" + "="*50)
    print("TEST 5: Audio File Upload")
    print("="*50)
    
    # Create a test audio file
    test_audio_file = "test_audio.wav"
    wav_header = b'RIFF' + (36).to_bytes(4, 'little') + b'WAVE' + b'fmt ' + (16).to_bytes(4, 'little') + \
                 (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') + (16000).to_bytes(4, 'little') + \
                 (32000).to_bytes(4, 'little') + (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + \
                 b'data' + (0).to_bytes(4, 'little')
    
    with open(test_audio_file, 'wb') as f:
        f.write(wav_header)
    
    session_id = "test-session-file-001"
    
    try:
        with open(test_audio_file, 'rb') as f:
            files = {'audio_file': (test_audio_file, f, 'audio/wav')}
            data = {'message': 'Uploaded audio file'}
            
            response = requests.post(
                f"{ENDPOINT}?session_id={session_id}",
                files=files,
                data=data
            )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    finally:
        # Clean up test file
        if os.path.exists(test_audio_file):
            os.remove(test_audio_file)

def test_file_upload_only():
    """Test 6: Audio file upload without text"""
    print("\n" + "="*50)
    print("TEST 6: Audio File Upload (audio only)")
    print("="*50)
    
    test_audio_file = "test_audio_only.wav"
    wav_header = b'RIFF' + (36).to_bytes(4, 'little') + b'WAVE' + b'fmt ' + (16).to_bytes(4, 'little') + \
                 (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') + (16000).to_bytes(4, 'little') + \
                 (32000).to_bytes(4, 'little') + (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + \
                 b'data' + (0).to_bytes(4, 'little')
    
    with open(test_audio_file, 'wb') as f:
        f.write(wav_header)
    
    session_id = "test-session-file-002"
    
    try:
        with open(test_audio_file, 'rb') as f:
            files = {'audio_file': (test_audio_file, f, 'audio/wav')}
            
            response = requests.post(
                f"{ENDPOINT}?session_id={session_id}",
                files=files
            )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    finally:
        if os.path.exists(test_audio_file):
            os.remove(test_audio_file)

def test_empty_request():
    """Test 7: Empty request (should fail with 400)"""
    print("\n" + "="*50)
    print("TEST 7: Empty Request (should fail)")
    print("="*50)
    
    response = requests.post(
        ENDPOINT,
        json={},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    return response.status_code == 400  # Should fail

def test_invalid_base64():
    """Test 8: Invalid base64 audio (should fail)"""
    print("\n" + "="*50)
    print("TEST 8: Invalid Base64 Audio (should fail)")
    print("="*50)
    
    payload = {
        "audio_data": "invalid-base64!!!",
        "session_id": "test-session-invalid"
    }
    
    response = requests.post(
        ENDPOINT,
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    return response.status_code == 400  # Should fail

def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("AI AGENT ENDPOINT TEST SUITE")
    print("="*50)
    print(f"Testing endpoint: {ENDPOINT}")
    print("\nMake sure the server is running on http://127.0.0.1:8000")
    print("Start server with: python3 main.py")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Server is running (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running!")
        print("Please start the server first: python3 main.py")
        return
    
    print("\nStarting tests...\n")
    
    results = []
    
    try:
        results.append(("Text Message (JSON)", test_text_message()))
        results.append(("Text Message (Query Param)", test_text_message_query_param()))
        results.append(("Audio Base64", test_audio_base64()))
        results.append(("Audio with Text", test_audio_with_text()))
        results.append(("File Upload", test_file_upload()))
        results.append(("File Upload Only", test_file_upload_only()))
        results.append(("Empty Request (should fail)", test_empty_request()))
        results.append(("Invalid Base64 (should fail)", test_invalid_base64()))
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server!")
        print("Please make sure the server is running on http://127.0.0.1:8000")
        return
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {total} | Passed: {passed} | Failed: {total - passed}")

if __name__ == "__main__":
    main()

