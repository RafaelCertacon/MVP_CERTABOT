from fastapi import APIRouter, Depends, File, Form, UploadFile, Request, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from br.com.certacon.certabot.api.deps import require_roles, get_db
from br.com.certacon.certabot.db.schemas.mvp import SubmitOut
from br.com.certacon.certabot.db.schemas.common import ErrorResponse
from br.com.certacon.certabot.utils.validation import validate_nfe_like
from br.com.certacon.certabot.utils.storage import save_upload
from br.com.certacon.certabot.utils.fs import suffix, run_separator_using_jobid
from br.com.certacon.certabot.utils.model_guard import enforce_expected_model, count_models_from_txt_upload
from br.com.certacon.certabot.utils.audit import make_job_folder, start_submission, log_event, bump_status, raise_and_log, record_file_movement

router = APIRouter(tags=["cte"])

def _resp(job_id: str, base: Path, user, split):
    return {"message": "Submissão recebida", "job_id": job_id, "service_type": "CTE", "stored_at": str(base), "split": split, "user": user.username}

@router.post("/submit", response_model=SubmitOut, responses={200: {"description": "ok"}, 400: {"model": ErrorResponse}})
async def submit_cte(
    request: Request,
    chave_txt: UploadFile = File(..., description="TXT com chaves CT-e (modelo 57)"),
    pfx_file: UploadFile = File(..., description="Certificado .pfx"),
    pfx_password: str = Form(...),
    user = Depends(require_roles("admin", "operador")),
    db: Session = Depends(get_db),
):
    service = "CTE"
    ip = request.client.host if request.client else "-"
    ua = request.headers.get("user-agent", "-")

    job_id, dest = make_job_folder(service, user.username)
    sub = start_submission(db, user=user, service=service, base_path=dest, ip=ip, ua=ua)

    try:
        enforce_expected_model(chave_txt, "57")
        log_event(db, sub, event_type="MODEL_ENFORCED", message="Modelo esperado: 57", meta={"counts": count_models_from_txt_upload(chave_txt)})
    except HTTPException as e:
        raise_and_log(db, sub, status="REJECTED_MODEL_MISMATCH", event_type="ERROR", http_status=e.status_code, msg="Model mismatch", meta={"detail": e.detail})

    try:
        validate_nfe_like(service, chave_txt=chave_txt, pfx_file=pfx_file, pfx_password=pfx_password)
    except HTTPException as e:
        raise_and_log(db, sub, status="REJECTED_VALIDATION", event_type="ERROR", http_status=e.status_code, msg="Validation error", meta={"detail": e.detail})

    try:
        saved_chave = save_upload(chave_txt, dest / f"chaves{suffix(chave_txt)}")
        saved_pfx   = save_upload(pfx_file, dest / f"cert{suffix(pfx_file)}")
        sub.chave_txt_path, sub.pfx_path = saved_chave, saved_pfx
        db.add(sub); db.commit(); db.refresh(sub)

        record_file_movement(db, sub, file_role="INPUT_TXT", path=Path(saved_chave))
        record_file_movement(db, sub, file_role="INPUT_PFX", path=Path(saved_pfx))
        bump_status(db, sub, "FILES_SAVED")
    except Exception as e:
        raise_and_log(db, sub, status="ERROR_SAVE", event_type="ERROR", http_status=500, msg="Falha ao salvar arquivos", meta={"error": str(e)})

    try:
        split = run_separator_using_jobid(path_txt=Path(saved_chave), folder_base=dest / "split", job_id=job_id)
        log_event(db, sub, event_type="SPLIT_DONE", message="Split finalizado", meta=split)
        bump_status(db, sub, "SPLIT_DONE")
    except Exception as e:
        raise_and_log(db, sub, status="ERROR_SPLIT", event_type="ERROR", http_status=500, msg="Falha no split", meta={"error": str(e)})

    return _resp(job_id, dest, user, split)
