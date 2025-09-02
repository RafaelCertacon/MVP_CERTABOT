import shutil
from typing import Optional
from pathlib import Path
from fastapi import UploadFile

def save_upload(upload: Optional[UploadFile], target: Path) -> Optional[str]:
    if not upload:
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return str(target)