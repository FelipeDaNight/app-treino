import calendar
import uuid
from collections import OrderedDict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/registros", tags=["registros"])


@router.post("/sessao", response_model=list[int], status_code=201)
def salvar_sessao(payload: schemas.SessaoCreate, db: Session = Depends(get_db)):
    treino = db.get(models.Treino, payload.treino_id)
    if not treino:
        raise HTTPException(404, "Treino não encontrado")
    if not payload.itens:
        raise HTTPException(422, "Nenhum exercício selecionado")

    data = payload.data or date.today()
    sessao_id = uuid.uuid4().hex
    ids = []
    for item in payload.itens:
        link = (
            db.query(models.TreinoExercicio)
            .filter(
                models.TreinoExercicio.id == item.treino_exercicio_id,
                models.TreinoExercicio.treino_id == payload.treino_id,
            )
            .first()
        )
        if not link:
            raise HTTPException(422, f"Exercício {item.treino_exercicio_id} não pertence a este treino")
        registro = models.RegistroCarga(
            treino_id=payload.treino_id,
            exercicio_id=link.exercicio_id,
            sessao_id=sessao_id,
            data=data,
            peso=item.peso,
            series=item.series,
            reps=item.reps,
        )
        db.add(registro)
        db.flush()
        ids.append(registro.id)

    db.commit()
    return ids


@router.post("/corrida", response_model=int, status_code=201)
def salvar_corrida(payload: schemas.CorridaCreate, db: Session = Depends(get_db)):
    treino = db.get(models.Treino, payload.treino_id)
    if not treino:
        raise HTTPException(404, "Treino não encontrado")

    data = payload.data or date.today()
    registro = models.RegistroCarga(
        treino_id=payload.treino_id,
        exercicio_id=None,
        sessao_id=uuid.uuid4().hex,
        data=data,
        distancia_km=payload.distancia_km,
        tempo_min=payload.tempo_min,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro.id


@router.get("/calendario", response_model=schemas.CalendarioMesOut)
def calendario_mes(
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    primeiro = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    ultimo = date(ano, mes, ultimo_dia)

    rows = (
        db.query(models.RegistroCarga.data)
        .filter(models.RegistroCarga.data >= primeiro, models.RegistroCarga.data <= ultimo)
        .distinct()
        .all()
    )
    dias = sorted({r[0] for r in rows})
    return schemas.CalendarioMesOut(ano=ano, mes=mes, dias_com_registro=dias)


@router.get("/dia", response_model=schemas.DiaOut)
def registros_do_dia(data: date = Query(...), db: Session = Depends(get_db)):
    rows = (
        db.query(models.RegistroCarga)
        .filter(models.RegistroCarga.data == data)
        .order_by(models.RegistroCarga.criado_em, models.RegistroCarga.id)
        .all()
    )

    grupos: "OrderedDict[str, list[models.RegistroCarga]]" = OrderedDict()
    for row in rows:
        chave = row.sessao_id or f"registro-{row.id}"
        grupos.setdefault(chave, []).append(row)

    entradas = []
    for itens in grupos.values():
        primeiro = itens[0]
        treino = primeiro.treino
        if treino.tipo == "corrida":
            entradas.append(
                schemas.DiaEntrada(
                    treino_id=treino.id,
                    label=treino.nome,
                    tipo="corrida",
                    distancia_km=primeiro.distancia_km,
                    tempo_min=primeiro.tempo_min,
                )
            )
        else:
            linhas = [
                schemas.DiaExercicioLinha(
                    nome=item.exercicio.nome if item.exercicio else "",
                    peso=item.peso,
                    series=item.series,
                    reps=item.reps,
                )
                for item in itens
            ]
            entradas.append(
                schemas.DiaEntrada(
                    treino_id=treino.id,
                    label=treino.nome,
                    tipo="forca",
                    exercicios=linhas,
                )
            )

    return schemas.DiaOut(data=data, entradas=entradas)
