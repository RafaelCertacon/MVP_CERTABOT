from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from br.com.certacon.certabot.db.base import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    full_name = Column(String(120))
    role = Column(String(32), nullable=False, default="operador")
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    logins = relationship("LoginLog", back_populates="user")
    submissions = relationship("ServiceSubmission", back_populates="user")

class LoginLog(Base):
    __tablename__ = "login_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip = Column(String(64))
    user_agent = Column(String(255))
    success = Column(Integer, default=1)  # 1 ok / 0 falha
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="logins")

class ServiceSubmission(Base):
    __tablename__ = "service_submissions"
    id = Column(Integer, primary_key=True)
    job_id = Column(String(64), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_type = Column(String(16), nullable=False)
    base_path = Column(Text, nullable=False)
    chave_txt_path = Column(Text, nullable=True)
    pfx_path = Column(Text, nullable=True)
    xlsx_path = Column(Text, nullable=True)
    csv_path = Column(Text, nullable=True)
    gov_cpf = Column(String(32), nullable=True)
    status = Column(String(32), nullable=False, default="RECEIVED")  # NEW: status atual
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="submissions")
    events = relationship("SubmissionEvent", back_populates="submission", cascade="all, delete-orphan")
    files = relationship("FileMovement", back_populates="submission", cascade="all, delete-orphan")

class SubmissionEvent(Base):
    """
    Linha do tempo/auditoria de uma submissão.
    Ex.: SUBMISSION_CREATED, MODEL_ENFORCED, FILE_SAVED, SPLIT_DONE, ERROR, DISPATCH_POSTED, STATUS_CHANGED...
    """
    __tablename__ = "submission_events"
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("service_submissions.id"), index=True, nullable=False)
    job_id = Column(String(64), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_type = Column(String(16), nullable=False)
    event_type = Column(String(64), nullable=False)
    message = Column(Text, nullable=True)
    meta = Column(JSON, nullable=True)  # detalhes (contagens por modelo, paths, HTTP status, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submission = relationship("ServiceSubmission", back_populates="events")

class FileMovement(Base):
    """
    Registro de movimentação/armazenamento de arquivo associado à submissão.
    """
    __tablename__ = "file_movements"
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("service_submissions.id"), index=True, nullable=False)
    job_id = Column(String(64), index=True, nullable=False)
    file_role = Column(String(32), nullable=False)  # ex.: INPUT_TXT, INPUT_PFX, INPUT_XLSX, INPUT_CSV, SPLIT_55, SPLIT_65, ...
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    mime_type = Column(String(128), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    sha256 = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submission = relationship("ServiceSubmission", back_populates="files")
