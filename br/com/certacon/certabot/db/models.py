from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from br.com.certacon.certabot.db.base import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey

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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="submissions")
