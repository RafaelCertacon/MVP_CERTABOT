import os
import shutil
import requests
from datetime import datetime


def processar_arquivo_txt(file, pasta_saida):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_base = os.path.join(pasta_saida, timestamp)
    pasta_modelo_55 = os.path.join(pasta_base, "modelo_55")
    pasta_modelo_65 = os.path.join(pasta_base, "modelo_65")
    os.makedirs(pasta_modelo_55, exist_ok=True)
    os.makedirs(pasta_modelo_65, exist_ok=True)

    caminho_temporario = f"temp_{timestamp}.txt"
    with open(caminho_temporario, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    chaves_modelo_55 = []
    chaves_modelo_65 = []
    with open(caminho_temporario, "r") as f:
        for linha in f.readlines():
            chave = linha.strip()
            if len(chave) > 20:
                modelo = chave[20:22]
                if modelo == "55":
                    chaves_modelo_55.append(chave)
                elif modelo == "65":
                    chaves_modelo_65.append(chave)

    caminho_modelo_55 = os.path.join(pasta_modelo_55, "modelo_55.txt")
    caminho_modelo_65 = os.path.join(pasta_modelo_65, "modelo_65.txt")

    links = {
        "mensagem": "Separação concluída!",
        "timestamp": timestamp,
        "modelo_55": {
            "qtd_chaves": len(chaves_modelo_55),
            "download": None
        },
        "modelo_65": {
            "qtd_chaves": len(chaves_modelo_65),
            "download": None
        }
    }

    # if chaves_modelo_55:
    #     with open(caminho_modelo_55, "w") as f:
    #         f.writelines([ch + "\n" for ch in chaves_modelo_55])
    #     try:
    #         with open(caminho_modelo_55, "rb") as file_to_send:
    #             response = requests.post(
    #                 "http://localhost/nfe_sp/upload_file",
    #                 files={"file": ("modelo_55.txt", file_to_send, "text/plain")},
    #
    #                 # headers={"Authorization": f"Bearer {token}"}
    #             )
    #             if response.status_code == 200:
    #                 print("✓ Arquivo modelo_55.txt enviado com sucesso para /upload_file")
    #             else:
    #                 print(f"✗ Falha ao enviar modelo_55.txt: {response.status_code} - {response.text}")
    #     except Exception as err:
    #         print(f"Erro ao enviar arquivo modelo_55.txt: {err}")
    #
    #     links["modelo_55"]["download"] = f"/nfe-55-65/download/modelo_55/{timestamp}"
    #
    # if chaves_modelo_65:
    #     with open(caminho_modelo_65, "w") as f:
    #         f.writelines([ch + "\n" for ch in chaves_modelo_65])
    #     links["modelo_65"]["download"] = f"/nfe-55-65/download/modelo_65/{timestamp}"

    os.remove(caminho_temporario)
    return links


def get_download_path(timestamp, modelo):
    return os.path.join("saida_modelos", timestamp, modelo, f"{modelo}.txt")