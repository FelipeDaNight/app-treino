from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import SESSION_KEY, get_current_user, hash_password, verify_password
from ..database import get_db
from ..seed import seed_treinos_padrao
from ..uploads import remover_imagem_upload, salvar_imagem_upload

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
    foto_antiga = usuario.foto_perfil_url
    usuario.foto_perfil_url = await salvar_imagem_upload(arquivo, f"perfil-{usuario.id}")
    db.commit()
    db.refresh(usuario)

    remover_imagem_upload(foto_antiga)

    return usuario
