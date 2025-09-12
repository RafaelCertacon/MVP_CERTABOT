from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any
import shutil

from br.com.certacon.certabot.utils.separar_modelos_nfe import processar_arquivo_txt_sem_enviar


def svc_name(service_type) -> str:
    """
    Converte o Enum do tipo de serviço para string UPPER estável.
    """
    try:
        return service_type.value.upper()
    except Exception:
        return getattr(service_type, "name", str(service_type)).upper()


def suffix(file) -> str:
    """
    Retorna o sufixo (extensão) do UploadFile/Path-like já em lower case, ou '' se vazio.
    """
    try:
        name = getattr(file, "filename", None) or getattr(file, "name", None) or ""
    except Exception:
        name = ""
    return Path(name).suffix.lower() if name else ""


def run_separator_using_jobid(
    *,
    path_txt: Path,
    folder_base: Path,
    job_id: str,
) -> Dict[str, Any]:
    """
    Executa a separação de chaves (tua função) e readequa a estrutura de saída para usar o `job_id`
    no nome da pasta final, além de reescrever os links/paths retornados.

    Fluxo:
      1) Roda `processar_arquivo_txt_sem_enviar(path_txt, split_root)` -> cria split_root/{timestamp}/...
      2) Move split_root/{timestamp} -> folder_base/{job_id}
      3) Reescreve os campos 'download' e 'path' para refletirem o {job_id}
    """
    split_root = folder_base / "split_wip"
    split_root.mkdir(parents=True, exist_ok=True)

    result: Dict[str, Any] = processar_arquivo_txt_sem_enviar(
        path_txt=Path(path_txt),
        pasta_saida=split_root,
    )

    ts: Optional[str] = result.get("timestamp")
    if not ts:
        return result

    src = split_root / ts
    dst = folder_base / job_id
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        shutil.rmtree(dst)

    shutil.move(src.as_posix(), dst.as_posix())

    def _rewrite_download(url: Optional[str]) -> Optional[str]:
        if not isinstance(url, str) or not url.strip():
            return url
        parts = url.strip("/").split("/")
        if parts and parts[-1] == ts:
            parts[-1] = job_id
            return "/" + "/".join(parts)
        return url

    def _rewrite_path(p: Optional[str]) -> Optional[str]:
        if not isinstance(p, str) or not p:
            return p
        return p.replace(ts, job_id)

    for key in ("modelo_55", "modelo_65", "modelo_57"):
        block = result.get(key)
        if isinstance(block, dict):
            block["download"] = _rewrite_download(block.get("download"))
            block["path"] = _rewrite_path(block.get("path"))
            result[key] = block

    result["timestamp"] = job_id

    try:
        if split_root.exists() and not any(split_root.iterdir()):
            split_root.rmdir()
    except Exception:
        pass

    return {"ok": True, "job_id": job_id, "split_dir": str(folder_base), "Resultado": result}
