import bcrypt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import models
from .database import get_db

SESSION_KEY = "usuario_id"


def hash_password(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        return False


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.Usuario:
    usuario_id = request.session.get(SESSION_KEY)
    if not usuario_id:
        raise HTTPException(401, "Não autenticado")
    usuario = db.get(models.Usuario, usuario_id)
    if not usuario:
        request.session.clear()
        raise HTTPException(401, "Não autenticado")
    return usuario


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> models.Usuario | None:
    usuario_id = request.session.get(SESSION_KEY)
    if not usuario_id:
        return None
    return db.get(models.Usuario, usuario_id)
