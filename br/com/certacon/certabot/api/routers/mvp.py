# from typing import Optional
# from fastapi import APIRouter, Depends, File, Form, UploadFile
# from sqlalchemy.orm import Session
# from pathlib import Path
# import uuid
#
# from br.com.certacon.certabot.api.core.config import settings
# from br.com.certacon.certabot.api.deps import require_roles, get_db
# from br.com.certacon.certabot.db import crud
# from br.com.certacon.certabot.db.schemas.mvp import SubmitOut, ServiceType
# from br.com.certacon.certabot.db.schemas.common import ErrorResponse
# from br.com.certacon.certabot.utils.send_service_separate import _none_if_empty_str
# from br.com.certacon.certabot.utils.storage import save_upload
#
# # utils (implemente/cole na tua pasta utils)
# from br.com.certacon.certabot.utils.validation import (
#     validate_payload_nfe_nfce_cfe, validate_payload_senatran,
# )
# from br.com.certacon.certabot.utils.fs import (
#     svc_name,
#     suffix,
#     run_separator_using_jobid,
# )
#
# router = APIRouter(prefix="/mvp", tags=["mvp"])
#
#
# @router.post(
#     "/submit",
#     response_model=SubmitOut,
#     response_model_exclude_none=True,
#     summary="Envio de arquivos (NFE/NFCE/CFE/SENATRAN) com validação e split por modelo quando aplicável",
#     description=(
#         "Cria um job, valida obrigatórios por serviço e, para NFE/NFCE/CFE, separa o TXT por modelo "
#         "usando o próprio job_id como nome de pasta. Para SENATRAN valida .xlsx e credenciais (PFX+senha ou GOV)."
#     ),
#     responses={
#         200: {"description": "Submissão criada"},
#         400: {"model": ErrorResponse, "description": "Extensão inválida ou dados incorretos"},
#         401: {"model": ErrorResponse, "description": "Token ausente ou inválido"},
#         403: {"model": ErrorResponse, "description": "Perfil sem permissão"},
#     },
# )
# async def submit_job(
#     service_type: ServiceType = Form(..., description="Tipo do serviço: NFE | NFCE | CFE | SENATRAN"),
#     # NFE/NFCE/CFE
#     chave_txt: Optional[UploadFile] = File(None, description="Arquivo .txt com chaves (CFE/NFE/NFCE)"),
#     pfx_file: Optional[UploadFile] = File(None, description="Certificado .pfx (CFE/NFE/NFCE/SENATRAN)"),
#     pfx_password: Optional[str] = Form(None, description="Senha do .pfx (não é armazenada)"),
#     planilha_csv: Optional[UploadFile] = File(None, description="Planilha .csv (apenas CFE)"),
#     # SENATRAN
#     placa_xlsx: Optional[UploadFile] = File(None, description="Planilha .xlsx (obrigatório p/ SENATRAN)"),
#     gov_cpf: Optional[str] = Form(None, description="CPF gov.br (alternativo ao PFX para SENATRAN)"),
#     gov_password: Optional[str] = Form(None, description="Senha gov.br (não é armazenada)"),
#     # contexto
#     user = Depends(require_roles("admin", "operador")),
#     db: Session = Depends(get_db),
# ):
#
#     chave_txt   = _none_if_empty_str(chave_txt)
#     pfx_file    = _none_if_empty_str(pfx_file)
#     planilha_csv= _none_if_empty_str(planilha_csv)
#     placa_xlsx  = _none_if_empty_str(placa_xlsx)
#     st = svc_name(service_type)
#
#     if st in {"NFE", "NFCE", "CFE"}:
#         validate_payload_nfe_nfce_cfe(
#             service_type=service_type,
#             chave_txt=chave_txt,
#             pfx_file=pfx_file,
#             pfx_password=pfx_password,
#             planilha_csv=planilha_csv,
#         )
#     elif st == "SENATRAN":
#         validate_payload_senatran(
#             service_type=service_type,
#             planilha_xlsx=placa_xlsx,
#             pfx_file=pfx_file,
#             pfx_password=pfx_password,
#             gov_cpf=gov_cpf,
#             gov_password=gov_password,
#         )
#     else:
#         from fastapi import HTTPException
#         raise HTTPException(status_code=400, detail=f"Serviço '{st}' não suportado nesta rota.")
#
#     job_id = str(uuid.uuid4())
#     dest = Path(settings.UPLOAD_DIR) / st / user.username / job_id
#     dest.mkdir(parents=True, exist_ok=True)
#
#     saved_chave = save_upload(chave_txt, dest / f"chaves{suffix(chave_txt)}") if chave_txt else None
#     saved_pfx   = save_upload(pfx_file, dest / f"cert{suffix(pfx_file)}") if pfx_file else None
#     saved_csv   = save_upload(planilha_csv, dest / f"planilha{suffix(planilha_csv)}") if planilha_csv else None
#     saved_xlsx  = save_upload(placa_xlsx, dest / f"placas{suffix(placa_xlsx)}") if placa_xlsx else None
#
#     split_result = None
#     if st in {"NFE", "NFCE", "CFE"} and saved_chave:
#         try:
#             split_result = run_separator_using_jobid(
#                 path_txt=Path(saved_chave),
#                 folder_base=dest / "split",
#                 job_id=job_id,
#             )
#         except Exception as e:
#             split_result = {"erro": f"Falha ao separar TXT: {e.__class__.__name__}: {e}"}
#     elif st in {"SENATRAN"}:
#         print("Lógica para validação da planilha com as placas")
#
#     crud.create_submission(
#         db,
#         job_id=job_id,
#         user_id=user.id,
#         service_type=service_type,
#         base_path=str(dest),
#         chave_txt_path=saved_chave,
#         pfx_path=saved_pfx,
#         csv_path=saved_csv,
#         xlsx_path=saved_xlsx,
#         gov_cpf=gov_cpf if st == "SENATRAN" else None,
#     )
#
#     return {
#         "message": "Submissão recebida",
#         "job_id": job_id,
#         "service_type": st,
#         "stored_at": str(dest),
#         "split": split_result,
#         "user": user.username,
#     }
