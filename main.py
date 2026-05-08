from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="brain_mock")

class ChatRequest(BaseModel):
    """Payload de entrada do endpoint de chat mock."""

    message: str

@app.get("/health")
def health():
    """Retorna o estado básico de saúde do serviço."""

    return {"status": "ok", "service": "brain_mock"}

@app.post("/chat")
def chat(req: ChatRequest):
    """Retorna uma resposta mock baseada na mensagem recebida."""

    return {"response": f"[MOCK] {req.message}"}
