import os, sys
from pathlib import Path

BASE_DIR = Path(os.getenv("DATA_DIR", str(Path.cwd()))).resolve()
PASTA_SAIDA = Path(os.getenv("PASTA_SAIDA", str(BASE_DIR / "saida_modelos"))).resolve()

def _ensure_outdir():
    try:
        PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # erro de permissão? path inválido?
        raise RuntimeError(f"Falha ao criar PASTA_SAIDA='{PASTA_SAIDA}': {e}")

# cria na importação e imprime onde ficou
_ensure_outdir()
print(f"[router_controle] PASTA_SAIDA -> {PASTA_SAIDA}", file=sys.stderr)