# br/com/certacon/certabot/api/routers/nfe/router.py
from fastapi import APIRouter, Depends, File, Form, UploadFile, Request, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import uuid

from br.com.certacon.certabot.api.core.config import settings
from br.com.certacon.certabot.api.deps import require_roles, get_db
from br.com.certacon.certabot.db import crud
from br.com.certacon.certabot.db.schemas.mvp import SubmitOut
from br.com.certacon.certabot.db.schemas.common import ErrorResponse
from br.com.certacon.certabot.utils.validation import validate_nfe_like
from br.com.certacon.certabot.utils.storage import save_upload
from br.com.certacon.certabot.utils.fs import suffix, run_separator_using_jobid
from br.com.certacon.certabot.utils.model_guard import enforce_expected_model, count_models_from_txt_upload
from br.com.certacon.certabot.utils.filemeta import file_sha256, file_size, guess_mime

router = APIRouter(tags=["nfe"])

def _make_job_folder(service_name: str, username: str) -> tuple[str, Path]:
    job_id = str(uuid.uuid4())
    dest = Path(settings.UPLOAD_DIR) / service_name / username / job_id
    dest.mkdir(parents=True, exist_ok=True)
    return job_id, dest

def _response_ok(*, job_id: str, service_name: str, base_path: Path, user, split_result: dict | None):
    return {
        "message": "Submissão recebida",
        "job_id": job_id,
        "service_type": service_name,
        "stored_at": str(base_path),
        "split": split_result,
        "user": user.username,
    }

@router.post(
    "/submit",
    response_model=SubmitOut,
    responses={200: {"description": "Submissão criada"}, 400: {"model": ErrorResponse}},
    summary="NFE: enviar TXT de chaves + PFX (com senha) e realizar split por modelo",
)
async def submit_nfe(
    request: Request,
    chave_txt: UploadFile = File(..., description="Arquivo .txt com chaves NFe"),
    pfx_file: UploadFile = File(..., description="Certificado .pfx"),
    pfx_password: str = Form(..., description="Senha do .pfx (não é armazenada)"),
    user = Depends(require_roles("admin", "operador")),
    db: Session = Depends(get_db),
):
    service = "NFE"
    ip = request.client.host if request.client else "-"
    ua = request.headers.get("user-agent", "-")

    # (1) criar job e submissão ANTES das validações
    job_id, dest = _make_job_folder(service, user.username)
    sub = crud.create_submission(
        db,
        job_id=job_id,
        user_id=user.id,
        service_type=service,
        base_path=str(dest),
        chave_txt_path=None,
        pfx_path=None,
        csv_path=None,
        xlsx_path=None,
        gov_cpf=None,
    )
    crud.create_submission_event(
        db, submission_id=sub.id, job_id=job_id, user_id=user.id, service_type=service,
        event_type="SUBMISSION_CREATED", message=f"IP={ip}", meta={"user_agent": ua}
    )

    # (2) ENFORCE MODELO
    try:
        enforce_expected_model(chave_txt, expected_model="55")
        # registra contagem pra observabilidade
        counts = count_models_from_txt_upload(chave_txt)
        crud.create_submission_event(
            db, submission_id=sub.id, job_id=job_id, user_id=user.id, service_type=service,
            event_type="MODEL_ENFORCED", message="Modelo esperado: 55", meta={"counts": counts}
        )
    except HTTPException as e:
        crud.create_submission_event(
            db, submission_id=sub.id, job_id=job_id, user_id=user.id, service_type=service,
            event_type="ERROR", message="Model mismatch", meta={"detail": e.detail}
        )
        crud.update_submission_status(db, sub.id, "REJECTED_MODEL_MISMATCH", message="Modelo divergente")
        raise

    # (3) VALIDAÇÃO DE INSUMOS
    try:
        validate_nfe_like(service, chave_txt=chave_txt, pfx_file=pfx_file, pfx_password=pfx_password)
    except HTTPException as e:
        crud.create_submission_event(
            db, submission_id=sub.id, job_id=job_id, user_id=user.id, service_type=service,
            event_type="ERROR", message="Validation error", meta={"detail": e.detail}
        )
        crud.update_submission_status(db, sub.id, "REJECTED_VALIDATION", message="Falha na validação")
        raise

    # (4) SALVAR ARQUIVOS
    try:
        saved_chave = save_upload(chave_txt, dest / f"chaves{suffix(chave_txt)}")
        saved_pfx   = save_upload(pfx_file, dest / f"cert{suffix(pfx_file)}")
        # atualizar campos
        sub.chave_txt_path = saved_chave
        sub.pfx_path = saved_pfx
        db.add(sub); db.commit(); db.refresh(sub)

        # movimentos
        for role, p in (("INPUT_TXT", saved_chave), ("INPUT_PFX", saved_pfx)):
            if not p:
                continue
            path = Path(p)
            crud.create_file_movement(
                db,
                submission_id=sub.id, job_id=job_id,
                file_role=role, file_name=path.name, file_path=str(path),
                mime_type=guess_mime(path), size_bytes=file_size(path), sha256=file_sha256(path),
            )
        crud.update_submission_status(db, sub.id, "FILES_SAVED")
    except Exception as e:
        crud.create_submission_event(
            db, submission_id=sub.id, job_id=job_id, user_id=user.id, service_type=service,
            event_type="ERROR", message="File save error", meta={"error": str(e)}
        )
        crud.update_submission_status(db, sub.id, "ERROR_SAVE", message="Falha ao salvar arquivos")
        raise HTTPException(status_code=500, detail="Falha ao salvar arquivos")

    # (5) SPLIT
    try:
        split_result = run_separator_using_jobid(
            path_txt=Path(saved_chave),
            folder_base=dest / "split",
            job_id=job_id,
        )
        crud.create_submission_event(
            db, submission_id=sub.id, job_id=job_id, user_id=user.id, service_type=service,
            event_type="SPLIT_DONE", message="Split finalizado", meta=split_result
        )
        crud.update_submission_status(db, sub.id, "SPLIT_DONE")
    except Exception as e:
        crud.create_submission_event(
            db, submission_id=sub.id, job_id=job_id, user_id=user.id, service_type=service,
            event_type="ERROR", message="Split error", meta={"error": str(e)}
        )
        crud.update_submission_status(db, sub.id, "ERROR_SPLIT", message="Falha no split")
        raise HTTPException(status_code=500, detail="Falha ao separar TXT")

    return _response_ok(job_id=job_id, service_name=service, base_path=dest, user=user, split_result=split_result)
