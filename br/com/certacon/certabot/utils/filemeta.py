import hashlib, mimetypes, os
from pathlib import Path
from typing import Tuple, Optional

def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def file_size(path: Path) -> int:
    return os.path.getsize(path)

def guess_mime(path: Path) -> Optional[str]:
    m, _ = mimetypes.guess_type(path.as_posix())
    return m
