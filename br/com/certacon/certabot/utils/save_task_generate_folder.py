import json

from fastapi import UploadFile
from typing import Optional
from br.com.certacon.certabot.utils.nome_folder_salvo import _nowstamp
from br.com.certacon.certabot.utils.save_folder_saida import PASTA_SAIDA
from pathlib import Path

async def _save_upload(dst_dir: Path, up: UploadFile, name_override: Optional[str] = None) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    fname = name_override or (up.filename or "file")
    dst = dst_dir / fname
    if dst.exists():
        dst = dst_dir / f"{dst.stem}_{_nowstamp()}{dst.suffix}"
    with open(dst, "wb") as f:
        while True:
            chunk = await up.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    await up.close()
    return dst

def _task_dir(task_id: str) -> Path:
    for p in PASTA_SAIDA.iterdir():
        if p.is_dir() and p.name.endswith(f"_{task_id}"):
            return p
    raise FileNotFoundError(f"task_id '{task_id}' não encontrada")

def _write_meta(base: Path, data: dict):
    (base / "metadata.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _read_meta(base: Path) -> dict:
    f = base / "metadata.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}