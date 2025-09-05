from pathlib import Path
from datetime import datetime
from br.com.certacon.certabot.utils.save_folder_saida import _ensure_outdir


def processar_arquivo_txt_sem_enviar(path_txt: Path, pasta_saida: Path) -> dict:
    _ensure_outdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_base = pasta_saida / timestamp
    pasta_modelo_55 = pasta_base / "modelo_55"
    pasta_modelo_65 = pasta_base / "modelo_65"
    pasta_modelo_57 = pasta_base / "modelo_57"   # 🔹 Nova pasta

    pasta_modelo_55.mkdir(parents=True, exist_ok=True)
    pasta_modelo_65.mkdir(parents=True, exist_ok=True)
    pasta_modelo_57.mkdir(parents=True, exist_ok=True)

    ch55, ch65, ch57 = [], [], []   # 🔹 Nova lista
    with open(path_txt, "r", encoding="utf-8", errors="ignore") as f:
        for linha in f:
            chave = linha.strip()
            if len(chave) > 22:
                modelo = chave[20:22]
                if modelo == "55":
                    ch55.append(chave)
                elif modelo == "65":
                    ch65.append(chave)
                elif modelo == "57":   # 🔹 Novo modelo CTe
                    ch57.append(chave)

    # Caminhos dos arquivos separados
    caminho_55 = pasta_modelo_55 / "modelo_55.txt"
    caminho_65 = pasta_modelo_65 / "modelo_65.txt"
    caminho_57 = pasta_modelo_57 / "modelo_57.txt"

    # Links de retorno
    links = {
        "mensagem": "Separação concluída!",
        "timestamp": timestamp,
        "modelo_55": {
            "qtd_chaves": len(ch55),
            "download": f"/nfe-55-65/download/modelo_55/{timestamp}" if ch55 else None,
            "path": None,
        },
        "modelo_65": {
            "qtd_chaves": len(ch65),
            "download": f"/nfe-55-65/download/modelo_65/{timestamp}" if ch65 else None,
            "path": None,
        },
        "modelo_57": {   # 🔹 Novo bloco
            "qtd_chaves": len(ch57),
            "download": f"/nfe-55-65/download/modelo_57/{timestamp}" if ch57 else None,
            "path": None,
        },
    }

    # Salvando arquivos separados
    if ch55:
        with open(caminho_55, "w", encoding="utf-8") as f:
            f.writelines([ch + "\n" for ch in ch55])
        links["modelo_55"]["path"] = caminho_55.as_posix()

    if ch65:
        with open(caminho_65, "w", encoding="utf-8") as f:
            f.writelines([ch + "\n" for ch in ch65])
        links["modelo_65"]["path"] = caminho_65.as_posix()

    if ch57:
        with open(caminho_57, "w", encoding="utf-8") as f:
            f.writelines([ch + "\n" for ch in ch57])
        links["modelo_57"]["path"] = caminho_57.as_posix()

    return links

def _dispatch_file_txt(file_path: Path, target_base: str) -> dict:
    """Envia TXT para {target_base}/upload_file"""
    with open(file_path, "rb") as fp:
        resp = requests.post(
            f"{target_base.rstrip('/')}/upload_file",
            files={"file": (file_path.name, fp, "text/plain")},
            timeout=120,
        )
    return {"status": resp.status_code, "text": resp.text[:800]}

def _dispatch_certificado(pfx_path: Path, senha: str, target_base: str) -> dict:
    """Envia PFX+senha para {target_base}/upload-certificado"""
    with open(pfx_path, "rb") as fp:
        resp = requests.post(
            f"{target_base.rstrip('/')}/upload-certificado",
            files={"file": ("certificado.pfx", fp, "application/x-pkcs12")},
            data={"senha": senha},
            timeout=300,
        )
    return {"status": resp.status_code, "text": resp.text[:800]}