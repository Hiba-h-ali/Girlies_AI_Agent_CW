import os
import json
from google.auth import default
from google.oauth2 import service_account
from google.cloud.dialogflowcx import SessionsClient
from google.cloud.dialogflowcx_v3.types.session import DetectIntentRequest, DetectIntentResponse, QueryInput, TextInput, AudioInput, QueryParameters
from google.cloud.dialogflowcx_v3.types.audio_config import InputAudioConfig, AudioEncoding
import uuid

LOCATION = "us-central1"
PROJECT_ID = "girlies-ai-agent"
AGENT_ID = "4a8116a1-9f58-4b71-8cf0-f2faee516a2d"
LANGUAGE_CODE = "ar"
API_ENDPOINT = f"{LOCATION}-dialogflow.googleapis.com:443"

class Dialogflow:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Dialogflow, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Dialogflow._initialized:
            credentials = None
            # Option 1: Check for credentials file path from environment variable
            creds_file_path = os.environ.get("GCP_CREDENTIALS_FILE")
            if creds_file_path and os.path.exists(creds_file_path):
                credentials = service_account.Credentials.from_service_account_file(creds_file_path)
            # Option 2: Check for credentials JSON string
            elif os.environ.get("GCP_CREDENTIALS"):
                creds_json_string = os.environ.get("GCP_CREDENTIALS")
                creds_json = json.loads(creds_json_string)
                credentials = service_account.Credentials.from_service_account_info(creds_json)
            # Option 3: Check for default credentials file in project directory
            else:
                # Look for common credential file names in the project root
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                default_creds_files = [
                    os.path.join(project_root, "girlies-ai-agent-84d2cbf6976f.json"),
                    os.path.join(project_root, "credentials.json"),
                    os.path.join(project_root, "gcp-credentials.json"),
                ]
                for creds_file in default_creds_files:
                    if os.path.exists(creds_file):
                        credentials = service_account.Credentials.from_service_account_file(creds_file)
                        break
                # Option 4: Use default credentials (for local development with gcloud auth)
                if credentials is None:
                    try:
                        credentials, _ = default()
                    except Exception:
                        raise Exception(
                            "No GCP credentials found. Please set GCP_CREDENTIALS_FILE environment variable, "
                            "or place credentials.json in the project root, or run 'gcloud auth application-default login'"
                        )
            self.client = SessionsClient(credentials=credentials, client_options={"api_endpoint": API_ENDPOINT})
            Dialogflow._initialized = True

# يلي بتاخد الرسالة وبترد عليها 
    def detect_intent(self, query, session_id=None, audio_bytes=None, audio_file_path=None, audio_encoding=AudioEncoding.AUDIO_ENCODING_LINEAR_16, sample_rate_hertz=16000):
        """
        Detect intent from text or voice message.
        
        Args:
            query: Text query (str) - required for text input
            session_id: Optional session ID (str)
            audio_bytes: Audio data as bytes - required for audio input
            audio_file_path: Path to audio file - alternative to audio_bytes
            audio_encoding: Audio encoding format (default: LINEAR_16)
            sample_rate_hertz: Sample rate in Hz (default: 16000)
        
        Returns:
            tuple: (response_text, session_id)
        """
        session_id = session_id or str(uuid.uuid4())
        session_path = self.build_session_path(session_id)
        
        # Determine if input is audio or text
        if audio_bytes is not None or audio_file_path is not None:
            # Handle audio input
            if audio_file_path:
                with open(audio_file_path, 'rb') as f:
                    audio_bytes = f.read()
            query_input = self.build_audio_query_input(audio_bytes, audio_encoding, sample_rate_hertz)
        elif query:
            # Handle text input
            query_input = self.build_query_input(query)
        else:
            raise ValueError("Either 'query' (text) or 'audio_bytes'/'audio_file_path' must be provided")
        
        request = self.build_detect_intent_request(query_input, session_path)
        response = self.client.detect_intent(request=request)
        return self.extract_response_text(response), session_id

    def build_session_path(self, session_id):
        return f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}/sessions/{session_id}"
    
    def build_query_input(self, query):
        """Build query input for text messages."""
        text_input = TextInput(text=query)
        return QueryInput(text=text_input, language_code=LANGUAGE_CODE)
    
    def build_audio_query_input(self, audio_bytes, audio_encoding=AudioEncoding.AUDIO_ENCODING_LINEAR_16, sample_rate_hertz=16000):
        """Build query input for voice/audio messages."""
        audio_config = InputAudioConfig(
            audio_encoding=audio_encoding,
            sample_rate_hertz=sample_rate_hertz
        )
        audio_input = AudioInput(config=audio_config, audio=audio_bytes)
        return QueryInput(audio=audio_input, language_code=LANGUAGE_CODE)
    
    def build_detect_intent_request(self, query_input, session_path):
        return DetectIntentRequest(session=session_path, query_input=query_input)

    def extract_response_text(self, response):
        if not response.query_result.response_messages:
            return ""
        
        else:
            return response.query_result.response_messages[0].text.text[0]
    
    