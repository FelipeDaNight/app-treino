from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/exercicios", tags=["exercicios"])


@router.get("", response_model=list[schemas.ExercicioOut])
def listar_exercicios(db: Session = Depends(get_db)):
    return db.query(models.Exercicio).order_by(models.Exercicio.nome).all()
