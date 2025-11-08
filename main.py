from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn

app = FastAPI(title='Ai Agent CW', version='1.0.0')


class Model(BaseModel):
    message: str

@app.get('/')
def root():
    return {'message': 'Hello there'}

@app.post('/generate-text')
def reply(request: Request, model: Model):
    return {'message': model.message}
    

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)