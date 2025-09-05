from datetime import datetime


def _nowstamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _safe_name(s: str) -> str:
    s = (s or "").strip()
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in s) or "CLIENTE"