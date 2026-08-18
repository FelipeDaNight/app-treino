import os
import uuid

from fastapi import HTTPException, UploadFile

from .database import UPLOADS_DIR

TAMANHO_MAX_IMAGEM = 5 * 1024 * 1024  # 5MB
TIPOS_IMAGEM_PERMITIDOS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


async def salvar_imagem_upload(arquivo: UploadFile, prefixo: str) -> str:
    """Valida e salva uma imagem enviada, devolvendo a URL pública (/uploads/...)."""
    extensao = TIPOS_IMAGEM_PERMITIDOS.get(arquivo.content_type)
    if not extensao:
        raise HTTPException(422, "Envie uma imagem JPEG, PNG ou WEBP")

    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAX_IMAGEM:
        raise HTTPException(422, "Imagem muito grande (máximo 5MB)")

    nome_arquivo = f"{prefixo}-{uuid.uuid4().hex}{extensao}"
    caminho = os.path.join(UPLOADS_DIR, nome_arquivo)
    with open(caminho, "wb") as f:
        f.write(conteudo)

    return f"/uploads/{nome_arquivo}"


def remover_imagem_upload(url: str) -> None:
    """Remove um arquivo de /uploads/ com segurança, ignorando se não existir."""
    if not url or not url.startswith("/uploads/"):
        return
    caminho = os.path.join(UPLOADS_DIR, os.path.basename(url))
    if not os.path.abspath(caminho).startswith(os.path.abspath(UPLOADS_DIR)):
        return
    try:
        os.remove(caminho)
    except OSError:
        pass
