from __future__ import annotations
from typing import Iterable, Optional
from pathlib import Path
from fastapi import HTTPException, UploadFile

def _assert_extension(file: UploadFile, allowed_ext: Iterable[str], field_name: str) -> None:
    ext = Path(file.filename or "").suffix.lower()
    allowed = set(allowed_ext)
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: extensão inválida '{ext}'. Permitidas: {sorted(allowed)}",
        )

def validate_nfe_like(service_name: str, *, chave_txt: UploadFile, pfx_file: UploadFile, pfx_password: Optional[str]) -> None:
    if not chave_txt:   raise HTTPException(400, detail=f"{service_name}: arquivo .txt (chave_txt) é obrigatório")
    if not pfx_file:    raise HTTPException(400, detail=f"{service_name}: certificado .pfx (pfx_file) é obrigatório")
    if not pfx_password:raise HTTPException(400, detail=f"{service_name}: senha do .pfx (pfx_password) é obrigatória")
    _assert_extension(chave_txt, {".txt"}, "chave_txt")
    _assert_extension(pfx_file, {".pfx"}, "pfx_file")

def validate_cfe(*, chave_txt: UploadFile, pfx_file: UploadFile, pfx_password: Optional[str], planilha_csv: UploadFile) -> None:
    if not chave_txt:   raise HTTPException(400, detail="CFE: arquivo .txt (chave_txt) é obrigatório")
    if not pfx_file:    raise HTTPException(400, detail="CFE: certificado .pfx (pfx_file) é obrigatório")
    if not pfx_password:raise HTTPException(400, detail="CFE: senha do .pfx (pfx_password) é obrigatória")
    if not planilha_csv:raise HTTPException(400, detail="CFE: planilha .csv (planilha_csv) é obrigatória")
    _assert_extension(chave_txt, {".txt"}, "chave_txt")
    _assert_extension(pfx_file, {".pfx"}, "pfx_file")
    _assert_extension(planilha_csv, {".csv"}, "planilha_csv")

def validate_senatran(*, placa_xlsx: UploadFile, pfx_file: Optional[UploadFile], pfx_password: Optional[str], gov_cpf: Optional[str], gov_password: Optional[str]) -> None:
    if not placa_xlsx:
        raise HTTPException(400, detail="SENATRAN: planilha .xlsx (placa_xlsx) é obrigatória")
    _assert_extension(placa_xlsx, {".xlsx"}, "placa_xlsx")

    has_pfx = bool(pfx_file and pfx_password)
    has_gov = bool(gov_cpf and gov_password)
    if not (has_pfx or has_gov):
        raise HTTPException(400, detail="SENATRAN: informe (pfx_file + pfx_password) OU (gov_cpf + gov_password).")
    if pfx_file:
        _assert_extension(pfx_file, {".pfx"}, "pfx_file")
