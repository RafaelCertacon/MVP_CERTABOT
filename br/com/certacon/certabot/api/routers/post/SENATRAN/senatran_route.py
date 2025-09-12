from fastapi import APIRouter, Depends, File, Form, UploadFile, Request, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional

from br.com.certacon.certabot.api.deps import require_roles, get_db
from br.com.certacon.certabot.db.schemas.mvp import SubmitOut
from br.com.certacon.certabot.db.schemas.common import ErrorResponse
from br.com.certacon.certabot.utils.validation import validate_senatran
from br.com.certacon.certabot.utils.storage import save_upload
from br.com.certacon.certabot.utils.fs import suffix
from br.com.certacon.certabot.utils.audit import make_job_folder, start_submission, log_event, bump_status, raise_and_log, record_file_movement

router = APIRouter(tags=["senatran"])

def _resp(job_id: str, base: Path, user):
    return {"message": "Submissão recebida", "job_id": job_id, "service_type": "SENATRAN", "stored_at": str(base), "split": None, "user": user.username}

@router.post("/submit", response_model=SubmitOut, responses={200: {"description": "ok"}, 400: {"model": ErrorResponse}})
async def submit_senatran(
    request: Request,
    placa_xlsx: UploadFile = File(..., description="Planilha .xlsx com placas"),
    pfx_file: Optional[UploadFile] = File(None, description="Certificado .pfx (opcional se usar GOV)"),
    pfx_password: Optional[str] = Form(None),
    gov_cpf: Optional[str] = Form(None),
    gov_password: Optional[str] = Form(None),
    user = Depends(require_roles("admin", "operador")),
    db: Session = Depends(get_db),
):
    service = "SENATRAN"
    ip = request.client.host if request.client else "-"
    ua = request.headers.get("user-agent", "-")

    job_id, dest = make_job_folder(service, user.username)
    sub = start_submission(db, user=user, service=service, base_path=dest, ip=ip, ua=ua)

    try:
        validate_senatran(placa_xlsx=placa_xlsx, pfx_file=pfx_file, pfx_password=pfx_password, gov_cpf=gov_cpf, gov_password=gov_password)
        log_event(db, sub, event_type="VALIDATED", message="Planilha + método de autenticação ok")
    except HTTPException as e:
        raise_and_log(db, sub, status="REJECTED_VALIDATION", event_type="ERROR", http_status=e.status_code, msg="Validation error", meta={"detail": e.detail})

    try:
        saved_xlsx = save_upload(placa_xlsx, dest / f"placas{suffix(placa_xlsx)}")
        saved_pfx  = save_upload(pfx_file,   dest / f"cert{suffix(pfx_file)}") if pfx_file else None

        sub.xlsx_path = saved_xlsx
        sub.pfx_path  = saved_pfx
        sub.gov_cpf   = gov_cpf
        db.add(sub); db.commit(); db.refresh(sub)

        record_file_movement(db, sub, file_role="INPUT_XLSX", path=Path(saved_xlsx))
        if saved_pfx:
            record_file_movement(db, sub, file_role="INPUT_PFX", path=Path(saved_pfx))

        bump_status(db, sub, "FILES_SAVED")
        bump_status(db, sub, "READY", message="Aguardando processamento SENATRAN")
    except Exception as e:
        raise_and_log(db, sub, status="ERROR_SAVE", event_type="ERROR", http_status=500, msg="Falha ao salvar arquivos", meta={"error": str(e)})

    return _resp(job_id, dest, user)
