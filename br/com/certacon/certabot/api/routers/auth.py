# br/com/certacon/certabot/api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from br.com.certacon.certabot.api.deps import get_db
from br.com.certacon.certabot.db import crud
from br.com.certacon.certabot.db.schemas.auth import TokenOut
from br.com.certacon.certabot.api.core.security import create_access_token
from br.com.certacon.certabot.db.schemas.common import ErrorResponse

class UserData(BaseModel):
    username: str
    password: str


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/token",
    response_model=TokenOut,
    summary="Gera um token de acesso (JWT)",
    description=(
        "Faça login com **username** e **password** (formulário x-www-form-urlencoded). "
        "Na resposta, copie `access_token` e clique no botão **Authorize** no topo do Swagger para informar `Bearer SEU_TOKEN`."
    ),
    responses={
        200: {
            "description": "Login OK",
            "content": {
                "application/json": {
                    "example": {"access_token": "eyJhbGciOiJI...","token_type":"bearer","role":"admin"}
                }
            }
        },
        400: {"model": ErrorResponse, "description": "Credenciais inválidas"},
    },
)
def login(
    request: Request,
    form_data: UserData,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not crud.verify_user_password(user, form_data.password):
        if user:
            crud.create_login_log(db, user_id=user.id, ip=request.client.host if request.client else None,
                                  user_agent=request.headers.get("User-Agent",""), success=False)
        raise HTTPException(status_code=400, detail="Usuário ou senha inválidos")

    crud.create_login_log(db, user_id=user.id, ip=request.client.host if request.client else None,
                          user_agent=request.headers.get("User-Agent",""), success=True)

    token = create_access_token(sub=user.username, role=user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role}
