from pathlib import Path
from fastapi import UploadFile

def save_upload(up: UploadFile | None, dst: Path) -> str | None:
    if not up:
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        while True:
            chunk = up.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    return str(dst)
