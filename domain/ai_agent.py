from integeration import Dialogflow
from pydantic import BaseModel

dialogflow_instance = Dialogflow()

class AiAgentResponse(BaseModel):
    response: str
    session_id: str

class AiAgent(BaseModel):
    message: str
    session_id: str|None = None

    def generate_response(self):
        response, session_id = dialogflow_instance.detect_intent(self.message, self.session_id)
        return AiAgentResponse(response=response, session_id=session_id)