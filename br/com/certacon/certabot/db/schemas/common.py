
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["Usuário ou senha inválidos", "Acesso negado para sua função"])
