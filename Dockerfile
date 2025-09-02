# ---------- base ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependências de build leves
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Copia requirements primeiro (melhor cache)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# cria pasta de uploads
RUN mkdir -p /app/uploads

# Troque a porta se quiser
EXPOSE 2025

# Healthcheck básico
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:2025/health || exit 1

# Comando padrão (2 workers é ok pra VM pequena; aumente se quiser)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "2025", "--workers", "2"]
