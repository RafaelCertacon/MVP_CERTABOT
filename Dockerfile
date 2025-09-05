# Dockerfile.mssql
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ACCEPT_EULA=Y \
    DEBIAN_FRONTEND=noninteractive

# Ferramentas + unixODBC p/ pyodbc
RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates apt-transport-https \
    unixodbc unixodbc-dev build-essential; \
  rm -rf /var/lib/apt/lists/*

# Repo Microsoft e drivers ODBC 18 e 17
RUN set -eux; \
  mkdir -p /etc/apt/keyrings; \
  curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg; \
  echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list; \
  apt-get update; \
  ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 msodbcsql17; \
  rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements (garanta pyodbc no arquivo)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Projeto
COPY . /app
RUN mkdir -p /app/uploads

EXPOSE 2905
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:2905/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "2905", "--workers", "2"]
