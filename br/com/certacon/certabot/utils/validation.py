from __future__ import annotations

from typing import Iterable, Optional
from pathlib import Path
from fastapi import HTTPException, UploadFile


def _assert_extension(file: UploadFile, allowed_ext: Iterable[str], field_name: str) -> None:
    """
    Valida a extensão do arquivo enviado.
    """
    ext = Path(file.filename or "").suffix.lower()
    allowed = set(allowed_ext)
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: extensão inválida '{ext}'. Permitidas: {sorted(allowed)}",
        )


def _normalize_service_type(service_type) -> str:
    """
    Retorna o nome do enum como string UPPER (funciona para Enum[str] e Enum padrão).
    """
    try:
        return service_type.value.upper()  # Enum[str]
    except Exception:
        return getattr(service_type, "name", str(service_type)).upper()


def validate_payload_nfe_nfce_cfe(
    service_type,
    *,
    chave_txt: Optional[UploadFile],
    pfx_file: Optional[UploadFile],
    pfx_password: Optional[str],
    planilha_csv: Optional[UploadFile] = None,
) -> None:
    """
    Regras de validação de borda (HTTP) para NFE/NFCE/CFE:3

      - NFE / NFCE: exigem .txt + .pfx + senha
      - CFE       : exige .txt + .pfx + senha + .csv

    Observações:
      - As senhas não são persistidas, apenas validadas como presença (não vazias).
      - Extensões são checadas quando os arquivos existem.
    """
    st = _normalize_service_type(service_type)
    if st not in {"NFE", "NFCE", "CFE"}:
        return

    if chave_txt:
        _assert_extension(chave_txt, {".txt"}, "chave_txt")
    if pfx_file:
        _assert_extension(pfx_file, {".pfx"}, "pfx_file")
    if planilha_csv:
        _assert_extension(planilha_csv, {".csv"}, "planilha_xlsx")

    missing: list[str] = []
    if not chave_txt:
        missing.append("arquivo .txt (chave_txt)")
    if not pfx_file:
        missing.append("certificado .pfx (pfx_file)")
    if not pfx_password:
        missing.append("senha do .pfx (pfx_password)")
    if st == "CFE" and not planilha_csv:
        missing.append("planilha .csv (planilha_xlsx)")

    if len(missing) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"{st}: campos obrigatórios ausentes: {', '.join(missing)}",
        )

def check_and_validate_senatran_auth_method(gov_cpf, gov_password, pfx_file, pfx_password):
    missing: list[str] = []

    if (gov_cpf and gov_password) or (pfx_file and pfx_password):
        return missing

    if not gov_cpf and not pfx_file and not gov_password and not pfx_password:
        missing.append("Forneça as informações de autenticação na plataforma")
    else:
        if gov_cpf or gov_password:
            if not gov_cpf:
                missing.append("Forneça um CPF para login no gov")
            if not gov_password:
                missing.append("Forneça uma senha para login no gov")

        if pfx_file or pfx_password:
            if not pfx_file:
                missing.append("Forneça um arquivo de certificado digital para login")
            if not pfx_password:
                missing.append("Forneça uma senha do certificado digital para login")

    return missing


def validate_payload_senatran(
    service_type,
    *,
    planilha_xlsx: Optional[UploadFile],
    pfx_file: Optional[UploadFile],
    pfx_password: Optional[str],
    gov_cpf: Optional[str],
    gov_password: Optional[str]
) -> None:
    """
    Regras de validação de borda (HTTP) para Senatran

      - exige a planilha no formato ideal, além de um certificado digital ou um login no GOV

    Observações:
      - As senhas não são persistidas, apenas validadas como presença (não vazias).
      - Extensões são checadas quando os arquivos existem.
    """
    st = _normalize_service_type(service_type)
    if st not in {"SENATRAN"}:
        return

    if planilha_xlsx:
        _assert_extension(planilha_xlsx, {".xlsx"}, "planilha_xlsx")
    if pfx_file:
        _assert_extension(pfx_file, {".pfx"}, "pfx_file")

    missing = check_and_validate_senatran_auth_method(gov_cpf, gov_password, pfx_file, pfx_password)

    if len(missing) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"{st}: campos obrigatórios ausentes: {', '.join(missing)}",
        )
