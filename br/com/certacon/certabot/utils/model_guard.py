from __future__ import annotations
from typing import Dict, Iterable, Tuple
from fastapi import HTTPException, UploadFile

MODEL_META: Dict[str, Tuple[str, str]] = {
    "55": ("NFE",  "/mvp/nfe/submit"),
    "65": ("NFCE", "/mvp/nfce/submit"),
    "57": ("CTE",  "/mvp/cte/submit"),
    "59": ("CFE",  "/mvp/cfe/submit"),
}

def _extract_model(chave: str) -> str | None:
    """
    Extrai '55'|'65'|'57'|'59' da chave (posições 20:22).
    Ignora linhas curtas e caracteres não numéricos.
    """
    s = "".join(ch for ch in chave.strip() if ch.isdigit())
    if len(s) < 22:
        return None
    m = s[20:22]
    return m if m in MODEL_META else None

def _iter_lines(up: UploadFile):
    pos = up.file.tell()
    up.file.seek(0)
    try:
        for raw in up.file:
            try:
                yield raw.decode("utf-8", errors="ignore")
            except AttributeError:
                yield raw
    finally:
        up.file.seek(pos)

def count_models_from_txt_upload(chave_txt: UploadFile) -> Dict[str, int]:
    counts = {"55": 0, "65": 0, "57": 0, "59": 0}
    for line in _iter_lines(chave_txt):
        model = _extract_model(line)
        if model in counts:
            counts[model] += 1
    return counts

def enforce_expected_model(chave_txt: UploadFile, expected_model: str) -> None:
    """
    Garante que o TXT está coerente com o endpoint.
      - Se não houver nenhuma chave do modelo esperado -> erro.
      - Se houver modelos “intrusos” -> erro com sugestão de endpoints corretos.
    """
    counts = count_models_from_txt_upload(chave_txt)
    total = sum(counts.values())
    ok = counts.get(expected_model, 0)

    if total == 0:
        raise HTTPException(
            status_code=400,
            detail="TXT não contém chaves reconhecíveis (modelos 55/65/57/59). Verifique o arquivo."
        )

    others = {m: c for m, c in counts.items() if m != expected_model and c > 0}
    if ok == 0 or others:
        service_name, this_endpoint = MODEL_META[expected_model]
        parts = [f"Modelo {expected_model}: {ok}"]
        parts.extend([f"Modelo {m}: {c}" for m, c in others.items()])
        counts_msg = "; ".join(parts)

        suggestions = []
        for m, c in others.items():
            s_name, s_ep = MODEL_META[m]
            suggestions.append(f"{s_name} → {s_ep} ({c} chave(s))")

        msg = (
            f"{service_name}: o TXT enviado não corresponde ao endpoint.\n"
            f"Resumo por modelo: {counts_msg}.\n"
        )
        if ok == 0:
            msg += f"Nenhuma chave do modelo {expected_model} foi encontrada. "
        if suggestions:
            msg += "Use os endpoints adequados: " + ", ".join(suggestions)

        raise HTTPException(status_code=400, detail=msg)
