from integeration import Dialogflow
from pydantic import BaseModel

dialogflow_instance = Dialogflow()

class AiAgentResponse(BaseModel):
    response: str
    session_id: str

class AiAgent(BaseModel):
    message: str = ""
    session_id: str|None = None
    audio_bytes: bytes|None = None
    audio_file_path: str|None = None

    def generate_response(self):
        response, session_id = dialogflow_instance.detect_intent(
            query=self.message if self.message else None,
            session_id=self.session_id, 
            audio_bytes=self.audio_bytes, 
            audio_file_path=self.audio_file_path
        )
        return AiAgentResponse(response=response, session_id=session_id)