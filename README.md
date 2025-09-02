# MVP CERTABOT — FastAPI

API MVP para **upload de insumos** (TXT/PFX/XLSX), **autenticação JWT** e **auditoria** (logins e submissões).  
Projeto pensado para ser **didático (trainee-friendly)**, modular e pronto para rodar **localmente** e em **Docker**.

---

## ✨ Principais recursos

- **Login JWT (Bearer)** com PBKDF2 (evita dores do `bcrypt` no Windows).
- **`/mvp/submit`**: upload de arquivos por serviço (**NFE / CTE / NFCE / CFE / SENATRAN**).
  - Todos os arquivos e campos **podem ser opcionais** (facilita testes).
  - Salva em `uploads/{service}/{username}/{timestamp_uuid}/`.
  - Registra **auditoria em banco** (quem, quando, o quê).
- **Auditoria**:
  - `login_logs`: cada tentativa de login (sucesso/falha, IP, User-Agent).
  - `service_submissions`: cada submissão com paths gravados.
- **Criação de tabelas e seed** na **inicialização** (idempotente).
- **Swagger `/docs`** com textos, exemplos e dicas passo‑a‑passo.
- **Dockerfile + docker-compose** prontos (SQLite por padrão, MSSQL opcional).

---

## 🧱 Stack

- **Python 3.12+**, **FastAPI**, **Uvicorn**
- **SQLAlchemy (sync)** + **SQLite** por padrão  
  *(ou MSSQL via `pyodbc`, ver seção Docker MSSQL)*
- **python-jose (JWT)**, **passlib[pbkdf2]**
- **pydantic v2** + **pydantic-settings** (env)

---

## 📂 Estrutura de pastas (resumo)

```
.
├─ main.py                            # App runner (raiz do projeto)
├─ br/
│  └─ com/certacon/certabot/
│     ├─ api/
│     │  ├─ core/
│     │  │  ├─ config.py             # Settings (.env)
│     │  │  └─ security.py           # Hash/verify e JWT
│     │  ├─ routers/
│     │  │  ├─ auth.py               # /auth/token
│     │  │  └─ mvp.py                # /mvp/submit
│     │  └─ deps.py                  # deps: get_db, require_roles
│     ├─ db/
│     │  ├─ base.py                  # Base declarative
│     │  ├─ models.py                # User, LoginLog, ServiceSubmission
│     │  ├─ crud.py                  # CRUDs básicos
│     │  ├─ session.py               # engine + SessionLocal
│     │  └─ schemas/
│     │     ├─ auth.py               # TokenOut
│     │     ├─ common.py             # ErrorResponse
│     │     └─ mvp.py                # SubmitOut, ServiceType
│     └─ utils/
│        └─ storage.py               # save_upload
├─ uploads/                           # volume mapeado (persistência)
├─ .env                               # config (ver abaixo)
├─ requirements.txt
├─ Dockerfile
└─ docker-compose.yml
```

> ⚠️ Todos os diretórios de pacote precisam de `__init__.py`.

---

## ⚙️ Configuração (`.env`)

```env
APP_NAME=MVP Certabot
JWT_SECRET=troque-por-um-uuid-ou-32chars
JWT_ALG=HS256
JWT_EXPIRE_MIN=60

# SQLite padrão
DATABASE_URL=sqlite:///./app.db

# Exemplo MSSSQL (se for usar pyodbc):
# DATABASE_URL=mssql+pyodbc://USUARIO:SENHA@HOST:1433/NomeBanco?driver=ODBC+Driver+18+for+SQL+Server

UPLOAD_DIR=./uploads
TZ=America/Sao_Paulo
```

---

## 🚀 Como rodar (local)

```bash
python -m venv .venv
# Windows
.venv\Scriptsctivate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- **Swagger:** http://127.0.0.1:8000/docs  
- **ReDoc:**   http://127.0.0.1:8000/redoc  
- **Health:**  http://127.0.0.1:8000/health

> Ao subir, o app **cria/valida tabelas** e faz **seed** de usuários:
>
> - `admin / admin123` (admin)  
> - `oper / oper123` (operador)

---

## 🧪 Teste rápido (cURL)

### 1) Login
```bash
curl -X POST http://127.0.0.1:8000/auth/token   -H "Content-Type: application/x-www-form-urlencoded"   -d "username=admin&password=admin123"
```
Resposta
```json
{"access_token":"<JWT>","token_type":"bearer","role":"admin"}
```

### 2) Submissão (multipart)

**Mínimo (só o tipo):**
```bash
TOKEN="<JWT>"
curl -X POST http://127.0.0.1:8000/mvp/submit   -H "Authorization: Bearer $TOKEN"   -F "service_type=NFE"
```

**Com arquivos (todos opcionais):**
```bash
curl -X POST http://127.0.0.1:8000/mvp/submit   -H "Authorization: Bearer $TOKEN"   -F "service_type=NFE"   -F "chave_txt=@chaves.txt;type=text/plain"   -F "pfx_file=@cert.pfx;type=application/x-pkcs12"   -F "pfx_password=senhaDoPFX"   -F "placa_xlsx=@placas.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"   -F "gov_cpf=12345678900"   -F "gov_password=senhaGov"
```

---

## 🔐 Como usar o Swagger (trainee-friendly)

1. Abra **/docs**  
2. Em **/auth/token** clique em **Try it out**, informe `username` e `password`, **Execute**  
3. Copie `access_token`  
4. Clique no botão **Authorize** (cadeado, topo direito)  
5. Cole como: `Bearer SEU_TOKEN`  
6. Vá para **/mvp/submit** → **Try it out** → preencha `service_type` e anexe arquivos que quiser → **Execute**

---

## 🗃️ Banco & Auditoria

**Modelos principais**
- `User(id, username, role, password_hash, ...)`
- `LoginLog(id, user_id, ip, user_agent, success, created_at)`
- `ServiceSubmission(id, job_id, user_id, service_type, base_path, chave_txt_path, pfx_path, xlsx_path, gov_cpf, created_at)`

**Observações**
- Campos de arquivo/credenciais **podem ser `NULL`** (`nullable=True`).  
- Senhas **não são persistidas** (apenas paths e metadados).  
- Tabelas são criadas no startup (`Base.metadata.create_all`).

---

## 🐳 Docker

### Build & Up (SQLite padrão)
```bash
docker compose build
docker compose up -d
# acessar: http://SEU_SERVIDOR:8000/docs
```

### Ajustando o comando do Uvicorn

- Se **main.py está na raiz** do projeto: `main:app`
- Se estiver em **br/com/certacon/certabot/main.py**: `br.com.certacon.certabot.main:app`

**Exemplos** no `Dockerfile`/compose:
```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
# OU
CMD ["uvicorn", "br.com.certacon.certabot.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

---

## ⚠️ Troubleshooting

- **Error loading ASGI app. Could not import module "MVP_CERTABOT/main"**  
  Use **pontos** no target do Uvicorn (ex.: `main:app`), **não** `/`.

- **`python-multipart is not installed`**  
  `pip install python-multipart`.

- **`MissingGreenlet: aioodbc`**  
  Driver **async** com engine **sync**. Troque para `mssql+pyodbc` **ou** migre todo o stack para async.

- **`bcrypt.__about__` (Windows)**  
  Aqui usamos **PBKDF2**; se for usar `bcrypt`, fixe `bcrypt==4.1.3`.

- **Dentro do container, módulo não encontrado**  
  Verifique `WORKDIR`, o que foi copiado e o **target** do Uvicorn.

---

## 🛡️ Boas práticas de produção

- Troque `JWT_SECRET` por um valor forte (32+ chars/UUID).
- Restrinja CORS (`allow_origins=["https://seu-dominio.com"]`).
- Coloque um **reverse proxy** (Nginx/Traefik) com TLS.
- Monitore `/health` e logs.
- Faça **backups** do volume `uploads/` e do banco.
- Use **Alembic** para migrações de schema.

---

## 📜 Endpoints (resumo)

- `POST /auth/token` → Gera token JWT. Body: `username`, `password` (form urlencoded).  
- `POST /mvp/submit` → Upload por serviço (multipart form). Campos opcionais: `chave_txt`, `pfx_file`, `pfx_password`, `placa_xlsx`, `gov_cpf`, `gov_password`.  
- `GET /health` → Status simples da API.

---

## 🤝 Contribuição
- Commits descritivos.  
- PRs com descrição e passos de teste.

---

## 📄 Licença

**Proprietary – Certacon** (uso interno).

---

## 💬 Suporte

- **Timezone:** America/Sao_Paulo  
- Precisa de ajuda? Use o **/docs** e o botão **Authorize** para testar as rotas.
