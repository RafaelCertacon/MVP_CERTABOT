from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from br.com.certacon.certabot.utils.nome_folder_salvo import _nowstamp
from br.com.certacon.certabot.utils.save_folder_saida import _ensure_outdir
from br.com.certacon.certabot.utils.save_task_generate_folder import _save_upload, _write_meta
from br.com.certacon.certabot.utils.separar_modelos_nfe import processar_arquivo_txt_sem_enviar
router = APIRouter()

PASTA_SAIDA: Path = Path("./saida").resolve()

@router.post("/controle-upload")
async def controle_upload(
    empresa_baixa: str = Form(""),
    tipo_nota: str = Form(""),
    cnpjs: str = Form(""),
    volumetria_json: str = Form("{}"),
    pfx_password: Optional[str] = Form(None),
    separar: bool = Form(True),
    txt_file: Optional[UploadFile] = File(None),
    pfx_file: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File([]),
):
    """
    Guarda arquivos + metadados e (opcionalmente) separa o TXT por modelos (55/65/57).
    - `separar=True` (default): chama `processar_arquivo_txt_sem_enviar` após salvar o TXT.
    - Retorna `result` com links/contagens quando a separação ocorrer.
    """
    _ensure_outdir()
    try:
        stamp = _nowstamp()
        cliente = _safe_name(empresa_baixa) if empresa_baixa else "CLIENTE"
        task_id = os.urandom(4).hex().upper()
        base = PASTA_SAIDA / f"{stamp}_{cliente}_{task_id}"
        base.mkdir(parents=True, exist_ok=True)

        saved = {"txt": None, "pfx": None, "attachments": []}

        if pfx_file:
            ext = os.path.splitext(pfx_file.filename or "")[1].lower()
            name = "certificado.p12" if ext == ".p12" else "certificado.pfx"
            pfx_path = await _save_upload(base, pfx_file, name_override=name)
            saved["pfx"] = pfx_path.as_posix()
            if pfx_password:
                (base / "pfx_password.DEV.txt").write_text(pfx_password, encoding="utf-8")

        for up in files or []:
            p = await _save_upload(base, up)
            saved["attachments"].append(p.as_posix())

        if txt_file:
            txt_path = await _save_upload(base, txt_file, name_override="input.txt")
            saved["txt"] = txt_path.as_posix()
        else:
            txt_path = None

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
            "dispatched": {"55": False, "65": False, "57": False},
            "task_id": task_id,
            "base_dir": base.as_posix(),
        }

        separation_result = None
        if separar and txt_path:
            separation_result = processar_arquivo_txt_sem_enviar(Path(txt_path), PASTA_SAIDA)
            meta["separated"] = True
            meta["result"] = separation_result

        _write_meta(base, meta)

        return JSONResponse(
            content={
                "ok": True,
                "message": "Arquivos salvos com sucesso.",
                "task_id": task_id,
                "base_dir": base.as_posix(),
                "saved": saved,
                "separated": meta["separated"],
                "result": separation_result,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _safe_name(x: str) -> str:
    import re
    x = (x or "").strip()
    x = re.sub(r"[^\w\-\.]+", "_", x, flags=re.UNICODE)
    return x[:60] or "CLIENTE"
