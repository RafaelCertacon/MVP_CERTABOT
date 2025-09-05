import os, json, shutil, requests

from br.com.certacon.certabot.api.routers.auth import router
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Literal, Dict, Any
from pathlib import Path
from datetime import datetime

from br.com.certacon.certabot.utils.nome_folder_salvo import _nowstamp, _safe_name
from br.com.certacon.certabot.utils.save_folder_saida import PASTA_SAIDA, _ensure_outdir
from br.com.certacon.certabot.utils.save_task_generate_folder import _save_upload, _write_meta
from br.com.certacon.certabot.utils.separar_modelos_nfe import processar_arquivo_txt_sem_enviar


@router.post("/separar-modelos")
async def separar_modelos(file: UploadFile = File(...)):
    """Compatibilidade: separa imediatamente ao subir apenas .txt."""
    try:
        tmp = Path(f"temp_{_nowstamp()}.txt")
        with open(tmp, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        res = processar_arquivo_txt_sem_enviar(tmp, PASTA_SAIDA)
        tmp.unlink(missing_ok=True)
        return JSONResponse(content=res)
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@router.post("/controle-upload")
async def controle_upload(
    empresa_baixa: str = Form(""),
    tipo_nota: str = Form(""),
    cnpjs: str = Form(""),
    volumetria_json: str = Form("{}"),
    pfx_password: Optional[str] = Form(None),
    txt_file: Optional[UploadFile] = File(None),
    pfx_file: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File([]),
):
    """Só guarda arquivos e metadados. NÃO separa nem envia."""
    _ensure_outdir()
    try:
        stamp = _nowstamp()
        cliente = _safe_name(empresa_baixa) if empresa_baixa else "CLIENTE"
        task_id = os.urandom(4).hex().upper()  # curto e único
        base = PASTA_SAIDA / f"{stamp}_{cliente}_{task_id}"
        base.mkdir(parents=True, exist_ok=True)

        saved = {"txt": None, "pfx": None, "attachments": []}

        if pfx_file:
            ext = os.path.splitext(pfx_file.filename or "")[1].lower()
            name = "certificado.p12" if ext == ".p12" else "certificado.pfx"
            saved["pfx"] = (await _save_upload(base, pfx_file, name_override=name)).as_posix()
            if pfx_password:
                (base / "pfx_password.DEV.txt").write_text(pfx_password, encoding="utf-8")

        for up in files or []:
            p = await _save_upload(base, up)
            saved["attachments"].append(p.as_posix())

        if txt_file:
            saved["txt"] = (await _save_upload(base, txt_file, name_override="input.txt")).as_posix()

        try:
            volumetria = json.loads(volumetria_json) if volumetria_json else {}
        except Exception:
            volumetria = {}

        meta = {
            "empresa_baixa": empresa_baixa,
            "tipo_nota": tipo_nota,
            "cnpjs": cnpjs,
            "volumetria": volumetria,
            "created_at": datetime.now().isoformat(),
            "paths": saved,
            "separated": False,
            "result": None,
            "dispatched": {"55": False, "65": False}
        }
        _write_meta(base, meta)

        return {"task_id": task_id, "base_dir": base.as_posix(), "saved": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
