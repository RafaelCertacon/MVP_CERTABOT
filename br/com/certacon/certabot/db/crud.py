from typing import Optional
from sqlalchemy.orm import Session
from br.com.certacon.certabot.db import models
from br.com.certacon.certabot.api.core.security import hash_password, verify_password


# ----- Users
def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

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

# ----- Login logs
def create_login_log(db: Session, user_id: int, ip: str, user_agent: str, success: bool = True) -> models.LoginLog:
    log = models.LoginLog(user_id=user_id, ip=ip, user_agent=user_agent, success=1 if success else 0)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

# ----- Submissions
def create_submission(
    db: Session,
    *,
    job_id: str,
    user_id: int,
    service_type: str,
    base_path: str,
    chave_txt_path: Optional[str],
    pfx_path: Optional[str],
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
        xlsx_path=xlsx_path,
        gov_cpf=gov_cpf
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
