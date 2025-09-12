from pathlib import Path
from datetime import datetime
from br.com.certacon.certabot.utils.save_folder_saida import _ensure_outdir

def processar_arquivo_txt_sem_enviar(path_txt: Path, pasta_saida: Path) -> dict:
    _ensure_outdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_base = pasta_saida / timestamp
    pasta_modelo_55 = pasta_base / "modelo_55"
    pasta_modelo_65 = pasta_base / "modelo_65"
    pasta_modelo_57 = pasta_base / "modelo_57"
    pasta_modelo_59 = pasta_base / "modelo_59"  # <<< novo

    for p in (pasta_modelo_55, pasta_modelo_65, pasta_modelo_57, pasta_modelo_59):
        p.mkdir(parents=True, exist_ok=True)

    ch55, ch65, ch57, ch59 = [], [], [], []  # <<< novo
    with open(path_txt, "r", encoding="utf-8", errors="ignore") as f:
        for linha in f:
            chave = linha.strip()
            if len(chave) > 22:
                modelo = "".join(c for c in chave if c.isdigit())[20:22] if not chave[20:22].isdigit() else chave[20:22]
                if   modelo == "55": ch55.append(chave)
                elif modelo == "65": ch65.append(chave)
                elif modelo == "57": ch57.append(chave)
                elif modelo == "59": ch59.append(chave)  # <<< novo

    caminho_55 = pasta_modelo_55 / "modelo_55.txt"
    caminho_65 = pasta_modelo_65 / "modelo_65.txt"
    caminho_57 = pasta_modelo_57 / "modelo_57.txt"
    caminho_59 = pasta_modelo_59 / "modelo_59.txt"  # <<< novo

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
        "modelo_57": {
            "qtd_chaves": len(ch57),
            "download": f"/nfe-55-65/download/modelo_57/{timestamp}" if ch57 else None,
            "path": None,
        },
        "modelo_59": {  # <<< novo
            "qtd_chaves": len(ch59),
            "download": f"/nfe-55-65/download/modelo_59/{timestamp}" if ch59 else None,
            "path": None,
        },
    }

    if ch55:
        with open(caminho_55, "w", encoding="utf-8") as f:
            f.writelines(ch + "\n" for ch in ch55)
        links["modelo_55"]["path"] = caminho_55.as_posix()

    if ch65:
        with open(caminho_65, "w", encoding="utf-8") as f:
            f.writelines(ch + "\n" for ch in ch65)
        links["modelo_65"]["path"] = caminho_65.as_posix()

    if ch57:
        with open(caminho_57, "w", encoding="utf-8") as f:
            f.writelines(ch + "\n" for ch in ch57)
        links["modelo_57"]["path"] = caminho_57.as_posix()

    if ch59:  # <<< novo
        with open(caminho_59, "w", encoding="utf-8") as f:
            f.writelines(ch + "\n" for ch in ch59)
        links["modelo_59"]["path"] = caminho_59.as_posix()

    return links
