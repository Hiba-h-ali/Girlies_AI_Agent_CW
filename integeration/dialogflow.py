import os
import json
from google.auth import default
from google.oauth2 import service_account
from google.cloud.dialogflow_v3 import SessionsClient, DetectIntentRequest, DetectIntentResponse, QueryInput, TextInput,QueryParametes
import uuid

LOCATION = "us-central1"
PROJECT_ID = "girlies-ai-agent"
AGENT_ID = "4a8116a1-9f58-4b71-8cf0-f2faee516a2d"
LANGUAGE_CODE = "ar"
API_ENDPOINT = f"{LOCATION}dialogflow.googleapis.com:443"

class Dialogflow:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Dialogflow, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Dialogflow._initialized:
            creds_json_string = os.environ.get("GCP_CREDENTIALS")
            if creds_json_string:
                creds_json = json.loads(creds_json_string)
                credentials = service_account.Credentials.from_service_account_info(creds_json)
            else:
                credentials,_ = default()
            self.client = SessionsClient(credentials=credentials, client_options={"api_endpoint": API_ENDPOINT})
            Dialogflow._initialized = True
        return Dialogflow._instance

# يلي بتاخد الرسالة وبترد عليها 
    def detect_intent(self, query, session_id=None):
        session_id = session_id or str(uuid.uuid4())
        session_path = self.build_session_path(session_id)
        query_input = self.build_query_input(query)
        request = self.build_detect_intent_request(query_input, session_path)
        response = self.client.detect_intent(request=request)
        return self.extract_response_text(response), session_id

    def build_session_path(self, session_id):
        return f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}/sessions/{session_id}"
    
    def build_query_input(self, query):
        text_input = TextInput(text=query)
        return QueryInput(text=text_input, language_code=LANGUAGE_CODE)
    
    def build_detect_intent_request(self, query_input, session_path):
        return DetectIntentRequest(session=session_path, query_input=query_input)

    def extract_response_text(self, response):
        if not response.query_result.response_messages:
            return ""
        
        else:
            return response.query_result.response_messages[0].text.text[0]