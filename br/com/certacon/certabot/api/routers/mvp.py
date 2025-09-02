# br/com/certacon/certabot/api/routers/mvp.py
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import uuid

from br.com.certacon.certabot.api.core.config import settings
from br.com.certacon.certabot.api.deps import require_roles, get_db
from br.com.certacon.certabot.db import crud
from br.com.certacon.certabot.db.schemas.mvp import SubmitOut, ServiceType
from br.com.certacon.certabot.db.schemas.common import ErrorResponse
from br.com.certacon.certabot.utils.storage import save_upload

router = APIRouter(prefix="/mvp", tags=["mvp"])

def assert_extension(file: UploadFile, allowed_ext: set[str], field_name: str):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: extensão inválida '{ext}'. Permitidas: {sorted(allowed_ext)}"
        )

@router.post(
    "/submit",
    response_model=SubmitOut,
    response_model_exclude_none=True,
    summary="Envia arquivos do serviço e registra auditoria",
    description=(
        "Cria um **job** com os arquivos enviados e registra no banco quem enviou, quando e o tipo de serviço.\n\n"
        "**Passo a passo para dev trainee:**\n"
        "1) Faça login em `/auth/token` e clique em **Authorize** no Swagger\n"
        "2) Escolha o `service_type` (ex.: `NFE`)\n"
        "3) Anexe `chave_txt` (TXT), `pfx_file` (PFX) e `placa_xlsx` (XLSX) — **todos opcionais** para facilitar testes\n"
        "4) Envie. A resposta retorna `job_id` e o caminho onde os arquivos foram salvos\n\n"
        "_Obs.: Senhas nunca são persistidas em claro; somente paths e metadados._"
    ),
    responses={
        200: {
            "description": "Submissão criada",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Submissão recebida",
                        "job_id": "d7a0a2e5-3b6c-489e-8e5f-9e7a5a2f0f21",
                        "service_type": "NFE",
                        "stored_at": "C:/app/uploads/NFE/admin/20250101T120000_d7a0a2e5-3b6c-489e-8e5f-9e7a5a2f0f21",
                        "user": "admin"
                    }
                }
            }
        },
        400: {"model": ErrorResponse, "description": "Extensão inválida ou dados incorretos"},
        401: {"model": ErrorResponse, "description": "Token ausente ou inválido"},
        403: {"model": ErrorResponse, "description": "Perfil sem permissão"},
    },
)
async def submit_job(
    service_type: ServiceType = Form(..., description="Tipo do serviço: NFE | CTE | NFCE | CFE | SENATRAN"),
    # Opcionais para facilitar testes
    chave_txt: Optional[UploadFile] = File(None, description="Arquivo .txt com chaves (opcional)"),
    pfx_file: Optional[UploadFile] = File(None, description="Certificado .pfx (opcional)"),
    pfx_password: Optional[str] = Form(None, description="Senha do .pfx (não é armazenada)"),
    placa_xlsx: Optional[UploadFile] = File(None, description="Planilha .xlsx com placas (opcional)"),
    gov_cpf: Optional[str] = Form(None, description="CPF gov.br (opcional)"),
    gov_password: Optional[str] = Form(None, description="Senha gov.br (não é armazenada)"),
    user = Depends(require_roles("admin", "operador")),
    db: Session = Depends(get_db),
):
    if chave_txt:
        assert_extension(chave_txt, {".txt"}, "CHAVE.TXT")
    if pfx_file:
        assert_extension(pfx_file, {".pfx"}, "PFX")
    if placa_xlsx:
        assert_extension(placa_xlsx, {".xlsx"}, "PLACA.XLSX")

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    job_id = str(uuid.uuid4())
    dest = Path(settings.UPLOAD_DIR) / service_type / user.username / f"{ts}_{job_id}"
    dest.mkdir(parents=True, exist_ok=True)

    saved_chave = save_upload(chave_txt, dest / f"chaves{Path(chave_txt.filename).suffix.lower()}") if chave_txt else None
    saved_pfx   = save_upload(pfx_file, dest / f"cert{Path(pfx_file.filename).suffix.lower()}") if pfx_file else None
    saved_xlsx  = save_upload(placa_xlsx, dest / f"placas{Path(placa_xlsx.filename).suffix.lower()}") if placa_xlsx else None

    crud.create_submission(
        db,
        job_id=job_id,
        user_id=user.id,
        service_type=service_type,
        base_path=str(dest),
        chave_txt_path=saved_chave,
        pfx_path=saved_pfx,
        xlsx_path=saved_xlsx,
        gov_cpf=gov_cpf,
    )

    return {
        "message": "Submissão recebida",
        "job_id": job_id,
        "service_type": service_type,
        "stored_at": str(dest),
        "user": user.username,
    }
