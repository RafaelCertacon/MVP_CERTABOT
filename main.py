import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from br.com.certacon.certabot.api.core.config import settings
from br.com.certacon.certabot.db.session import engine, SessionLocal
from br.com.certacon.certabot.db.base import Base
from br.com.certacon.certabot.db import crud
from br.com.certacon.certabot.db.models import User
from br.com.certacon.certabot.api.routers import auth as auth_router
from br.com.certacon.certabot.api.routers.post.NFE.nfe_route import router as nfe_router
from br.com.certacon.certabot.api.routers.post.NFCE.nfce_route import router as nfce_router
from br.com.certacon.certabot.api.routers.post.CTE.cte_route import router as cfe_router
from br.com.certacon.certabot.api.routers.post.CFE.cfe_route import router as cte_router
from br.com.certacon.certabot.api.routers.get.get_global import router as get_global
from br.com.certacon.certabot.api.routers.post.SENATRAN.senatran_route import router as senatran_router

tags_metadata = [
    {
        "name": "auth",
        "description": "Autenticação via **JWT (Bearer Token)**. Comece por aqui: faça login, copie o token e clique no botão **Authorize** no topo do Swagger para liberar as rotas protegidas.",
        "externalDocs": {"description": "Como funciona Bearer Token", "url": "https://datatracker.ietf.org/doc/html/rfc6750"},
    },
    {
        "name": "mvp",
        "description": "Envio de arquivos e **auditoria** (quem enviou, quando, quais arquivos). Aceita campos opcionais pra facilitar testes.",
    },
    {
        "name": "health",
        "description": "Checagens simples de saúde do serviço.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description=(
        "API MVP do **Certabot** para upload de insumos (TXT/PFX/XLSX), "
        "registro de auditoria e autenticação JWT.\n\n"
        "**Fluxo recomendado para iniciantes:**\n"
        "1) Abra `/docs`\n"
        "2) Use `/auth/token` para gerar seu token\n"
        "3) Clique em **Authorize** (cadeado no topo) e cole: `Bearer SEU_TOKEN`\n"
        "4) Teste `/mvp/submit` enviando os arquivos\n"
    ),
    contact={"name": "Certacon · Suporte", "email": "certasky.info@certacon.com.br"},
    license_info={"name": "Proprietary"},
    terms_of_service="https://certacon.com.br/termos",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

def seed_users():
    db: Session = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            crud.create_user(db, "admin", "admin123", role="admin", full_name="Administrador")
        if not db.query(User).filter(User.username == "oper").first():
            crud.create_user(db, "oper", "oper123", role="operador", full_name="Operador Padrão")
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    seed_users()

app.include_router(auth_router.router)
app.include_router(nfe_router,      prefix="/mvp/nfe")
app.include_router(nfce_router,     prefix="/mvp/nfce")
app.include_router(cfe_router,      prefix="/mvp/cfe")
app.include_router(cte_router,      prefix="/mvp/cte")
app.include_router(senatran_router, prefix="/mvp/senatran")
app.include_router(get_global, prefix="/mvp/metrics")

@app.get("/health", tags=["health"], summary="Verifica se o serviço está de pé", description="Retorna informações básicas de saúde da API.")
def health():
    return {"status": "ok", "app": settings.APP_NAME}

from fastapi.openapi.utils import get_openapi
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["tags"] = tags_metadata
    openapi_schema["servers"] = [
        {"url": "http://127.0.0.1:2905", "description": "Local"},
        {"url": "http://localhost:2905", "description": "Local (localhost)"},
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    print("Criando/verificando tabelas…")
    Base.metadata.create_all(bind=engine)
    print("Tabelas OK.")
    uvicorn.run("main:app", host="0.0.0.0", port=2905, reload=True)
