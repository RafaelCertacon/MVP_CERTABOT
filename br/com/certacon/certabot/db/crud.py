import json
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from br.com.certacon.certabot.db import models
from br.com.certacon.certabot.api.core.security import hash_password, verify_password

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def _meta_to_text(meta):
    if meta is None:
        return None
    if isinstance(meta, (dict, list)):
        return json.dumps(meta, ensure_ascii=False)
    return str(meta)

def create_user(db: Session, username: str, password: str, role: str, full_name: str = "") -> models.User:
    u = models.User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        full_name=full_name
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def verify_user_password(user: models.User, password: str) -> bool:
    return verify_password(password, user.password_hash)

def create_login_log(db: Session, user_id: int, ip: str, user_agent: str, success: bool = True) -> models.LoginLog:
    log = models.LoginLog(user_id=user_id, ip=ip, user_agent=user_agent, success=1 if success else 0)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def create_submission(
    db: Session,
    *,
    job_id: str,
    user_id: int,
    service_type: str,
    base_path: str,
    chave_txt_path: Optional[str],
    pfx_path: Optional[str],
    csv_path: Optional[str],
    xlsx_path: Optional[str],
    gov_cpf: Optional[str],
) -> models.ServiceSubmission:
    sub = models.ServiceSubmission(
        job_id=job_id,
        user_id=user_id,
        service_type=service_type,
        base_path=base_path,
        chave_txt_path=chave_txt_path,
        pfx_path=pfx_path,
        csv_path=csv_path,
        xlsx_path=xlsx_path,
        gov_cpf=gov_cpf,
        status="RECEIVED",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

def update_submission_status(db: Session, submission_id: int, new_status: str, *, message: str = "", meta: Dict[str, Any] | None = None) -> models.ServiceSubmission:
    sub = db.query(models.ServiceSubmission).filter(models.ServiceSubmission.id == submission_id).first()
    if not sub:
        return None
    old = sub.status
    sub.status = new_status
    db.add(sub)
    # linha de evento
    ev = models.SubmissionEvent(
        submission_id=submission_id,
        job_id=sub.job_id,
        user_id=sub.user_id,
        service_type=sub.service_type,
        event_type="STATUS_CHANGED",
        message=message or f"{old} -> {new_status}",
        meta=meta or {"from": old, "to": new_status},
    )
    db.add(ev)
    db.commit()
    db.refresh(sub)
    return sub

def create_submission_event(
    db: Session,
    *,
    submission_id: int,
    job_id: str,
    user_id: int,
    service_type: str,
    event_type: str,
    message: str = "",
    meta: Dict[str, Any] | None = None,
) -> models.SubmissionEvent:
    ev = models.SubmissionEvent(
        submission_id=submission_id,
        job_id=job_id,
        user_id=user_id,
        service_type=service_type,
        event_type=event_type,
        message=message,
        meta=_meta_to_text(meta),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev

def create_file_movement(
    db: Session,
    *,
    submission_id: int,
    job_id: str,
    file_role: str,
    file_name: str,
    file_path: str,
    mime_type: Optional[str],
    size_bytes: Optional[int],
    sha256: Optional[str],
) -> models.FileMovement:
    f = models.FileMovement(
        submission_id=submission_id,
        job_id=job_id,
        file_role=file_role,
        file_name=file_name,
        file_path=file_path,
        mime_type=mime_type,
        size_bytes=size_bytes,
        sha256=sha256,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f
