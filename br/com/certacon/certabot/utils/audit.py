# br/com/certacon/certabot/utils/audit.py
from __future__ import annotations
from pathlib import Path
import uuid
from typing import Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from br.com.certacon.certabot.api.core.config import settings
from br.com.certacon.certabot.db import crud
from br.com.certacon.certabot.utils.filemeta import file_sha256, file_size, guess_mime

def make_job_folder(service: str, username: str) -> tuple[str, Path]:
    job_id = str(uuid.uuid4())
    dest = Path(settings.UPLOAD_DIR) / service / username / job_id
    dest.mkdir(parents=True, exist_ok=True)
    return job_id, dest

def start_submission(db: Session, *, user, service: str, base_path: Path, ip: str = "-", ua: str = "-"):
    sub = crud.create_submission(
        db,
        job_id=base_path.name,
        user_id=user.id,
        service_type=service,
        base_path=str(base_path),
        chave_txt_path=None,
        pfx_path=None,
        csv_path=None,
        xlsx_path=None,
        gov_cpf=None,
    )
    crud.create_submission_event(
        db,
        submission_id=sub.id, job_id=sub.job_id, user_id=sub.user_id, service_type=service,
        event_type="SUBMISSION_CREATED", message=f"IP={ip}", meta={"user_agent": ua},
    )
    return sub

def log_event(db: Session, sub, *, event_type: str, message: str = "", meta: Dict[str, Any] | None = None):
    crud.create_submission_event(
        db,
        submission_id=sub.id, job_id=sub.job_id, user_id=sub.user_id, service_type=sub.service_type,
        event_type=event_type, message=message, meta=meta,
    )

def bump_status(db: Session, sub, new_status: str, *, message: str = "", meta: Dict[str, Any] | None = None):
    crud.update_submission_status(db, sub.id, new_status, message=message, meta=meta)

def raise_and_log(db: Session, sub, *, status: str, event_type: str, http_status: int, msg: str, meta: Dict[str, Any] | None = None):
    log_event(db, sub, event_type=event_type, message=msg, meta=meta)
    bump_status(db, sub, status, message=msg, meta=meta)
    raise HTTPException(status_code=http_status, detail=msg)

def record_file_movement(db: Session, sub, *, file_role: str, path: Path):
    try:
        crud.create_file_movement(
            db,
            submission_id=sub.id,
            job_id=sub.job_id,
            file_role=file_role,
            file_name=path.name,
            file_path=str(path),
            mime_type=guess_mime(path),
            size_bytes=file_size(path),
            sha256=file_sha256(path),
        )
    except Exception:
        pass
