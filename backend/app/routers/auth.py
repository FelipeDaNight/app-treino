import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import SESSION_KEY, get_current_user, hash_password, verify_password
from ..database import UPLOADS_DIR, get_db
from ..seed import seed_treinos_padrao

router = APIRouter(prefix="/api/auth", tags=["auth"])

TAMANHO_MAX_FOTO = 5 * 1024 * 1024  # 5MB
TIPOS_IMAGEM_PERMITIDOS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@router.post("/signup", response_model=schemas.UsuarioOut, status_code=201)
def signup(payload: schemas.UsuarioCreate, request: Request, db: Session = Depends(get_db)):
    nome_usuario = payload.nome_usuario.strip()
    if not nome_usuario:
        raise HTTPException(422, "Nome de usuário é obrigatório")

    existente = (
        db.query(models.Usuario)
        .filter(func.lower(models.Usuario.nome_usuario) == nome_usuario.lower())
        .first()
    )
    if existente:
        raise HTTPException(409, "Esse nome de usuário já está em uso")

    usuario = models.Usuario(
        nome_usuario=nome_usuario,
        senha_hash=hash_password(payload.senha),
    )
    db.add(usuario)
    db.flush()

    seed_treinos_padrao(db, usuario.id)

    db.commit()
    db.refresh(usuario)

    request.session[SESSION_KEY] = usuario.id
    return usuario


@router.post("/login", response_model=schemas.UsuarioOut)
def login(payload: schemas.UsuarioLogin, request: Request, db: Session = Depends(get_db)):
    usuario = (
        db.query(models.Usuario)
        .filter(func.lower(models.Usuario.nome_usuario) == payload.nome_usuario.strip().lower())
        .first()
    )
    if not usuario or not verify_password(payload.senha, usuario.senha_hash):
        raise HTTPException(401, "Usuário ou senha inválidos")

    request.session[SESSION_KEY] = usuario.id
    return usuario


@router.post("/logout", status_code=204)
def logout(request: Request):
    request.session.clear()
    return None


@router.get("/me", response_model=schemas.UsuarioOut | None)
def me(request: Request, db: Session = Depends(get_db)):
    usuario_id = request.session.get(SESSION_KEY)
    if not usuario_id:
        return None
    return db.get(models.Usuario, usuario_id)


@router.post("/foto", response_model=schemas.UsuarioOut)
async def upload_foto(
    arquivo: UploadFile = File(...),
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    extensao = TIPOS_IMAGEM_PERMITIDOS.get(arquivo.content_type)
    if not extensao:
        raise HTTPException(422, "Envie uma imagem JPEG, PNG ou WEBP")

    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAX_FOTO:
        raise HTTPException(422, "Imagem muito grande (máximo 5MB)")

    nome_arquivo = f"perfil-{usuario.id}-{uuid.uuid4().hex}{extensao}"
    caminho = os.path.join(UPLOADS_DIR, nome_arquivo)
    with open(caminho, "wb") as f:
        f.write(conteudo)

    foto_antiga = usuario.foto_perfil_url
    usuario.foto_perfil_url = f"/uploads/{nome_arquivo}"
    db.commit()
    db.refresh(usuario)

    if foto_antiga and foto_antiga.startswith("/uploads/"):
        caminho_antigo = os.path.join(UPLOADS_DIR, os.path.basename(foto_antiga))
        if os.path.abspath(caminho_antigo).startswith(os.path.abspath(UPLOADS_DIR)):
            try:
                os.remove(caminho_antigo)
            except OSError:
                pass

    return usuario
