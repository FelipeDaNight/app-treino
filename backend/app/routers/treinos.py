from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/treinos", tags=["treinos"])


def _ultima_data_treino(db: Session, treino_id: int):
    return (
        db.query(func.max(models.RegistroCarga.data))
        .filter(models.RegistroCarga.treino_id == treino_id)
        .scalar()
    )


def _ultimo_valor_exercicio(db: Session, treino_id: int, exercicio_id: int):
    row = (
        db.query(models.RegistroCarga)
        .filter(
            models.RegistroCarga.treino_id == treino_id,
            models.RegistroCarga.exercicio_id == exercicio_id,
        )
        .order_by(models.RegistroCarga.data.desc(), models.RegistroCarga.criado_em.desc())
        .first()
    )
    if not row:
        return None
    return schemas.UltimoValor(peso=row.peso, series=row.series, reps=row.reps, data=row.data)


def _obter_treino_do_usuario(db: Session, treino_id: int, usuario_id: int) -> models.Treino:
    treino = (
        db.query(models.Treino)
        .filter(models.Treino.id == treino_id, models.Treino.usuario_id == usuario_id)
        .first()
    )
    if not treino:
        raise HTTPException(404, "Treino não encontrado")
    return treino


@router.get("", response_model=list[schemas.TreinoSummary])
def listar_treinos(
    db: Session = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)
):
    treinos = (
        db.query(models.Treino)
        .filter(models.Treino.usuario_id == usuario.id)
        .order_by(models.Treino.ordem, models.Treino.id)
        .all()
    )
    out = []
    for t in treinos:
        out.append(
            schemas.TreinoSummary(
                id=t.id,
                nome=t.nome,
                categoria=t.categoria,
                tipo=t.tipo,
                duracao_min=t.duracao_min,
                total_exercicios=len(t.exercicios),
                ultima_data=_ultima_data_treino(db, t.id),
            )
        )
    return out


@router.post("", response_model=schemas.TreinoDetail, status_code=201)
def criar_treino(
    payload: schemas.TreinoCreate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    nome = payload.nome.strip()
    if not nome:
        raise HTTPException(422, "Nome do treino é obrigatório")

    max_ordem = (
        db.query(func.max(models.Treino.ordem))
        .filter(models.Treino.usuario_id == usuario.id)
        .scalar()
        or 0
    )
    treino = models.Treino(
        usuario_id=usuario.id,
        nome=nome,
        categoria=payload.categoria,
        tipo=payload.tipo,
        duracao_min=payload.duracao_min,
        ordem=max_ordem + 1,
    )
    db.add(treino)
    db.flush()

    for i, item in enumerate(payload.exercicios):
        nome = item.nome.strip()
        if not nome:
            continue
        exercicio = (
            db.query(models.Exercicio)
            .filter(func.lower(models.Exercicio.nome) == nome.lower())
            .first()
        )
        if not exercicio:
            exercicio = models.Exercicio(nome=nome)
            db.add(exercicio)
            db.flush()
        db.add(
            models.TreinoExercicio(
                treino_id=treino.id,
                exercicio_id=exercicio.id,
                ordem=i,
                series_padrao=item.series_padrao,
                reps_padrao=item.reps_padrao,
                carga_padrao=item.carga_padrao,
            )
        )

    db.commit()
    db.refresh(treino)
    return _treino_detail(db, treino)


def _treino_detail(db: Session, treino: models.Treino) -> schemas.TreinoDetail:
    exercicios = []
    for link in sorted(treino.exercicios, key=lambda l: l.ordem):
        exercicios.append(
            schemas.TreinoExercicioOut(
                treino_exercicio_id=link.id,
                exercicio_id=link.exercicio_id,
                nome=link.exercicio.nome,
                imagem_url=link.exercicio.imagem_url,
                ordem=link.ordem,
                series_padrao=link.series_padrao,
                reps_padrao=link.reps_padrao,
                carga_padrao=link.carga_padrao,
                ultimo=_ultimo_valor_exercicio(db, treino.id, link.exercicio_id),
            )
        )
    return schemas.TreinoDetail(
        id=treino.id,
        nome=treino.nome,
        categoria=treino.categoria,
        tipo=treino.tipo,
        duracao_min=treino.duracao_min,
        exercicios=exercicios,
        ultima_data=_ultima_data_treino(db, treino.id),
    )


@router.get("/{treino_id}", response_model=schemas.TreinoDetail)
def obter_treino(
    treino_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    treino = _obter_treino_do_usuario(db, treino_id, usuario.id)
    return _treino_detail(db, treino)


@router.get("/{treino_id}/ultima-corrida", response_model=schemas.UltimaCorridaOut | None)
def ultima_corrida(
    treino_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    _obter_treino_do_usuario(db, treino_id, usuario.id)
    row = (
        db.query(models.RegistroCarga)
        .filter(models.RegistroCarga.treino_id == treino_id)
        .order_by(models.RegistroCarga.data.desc(), models.RegistroCarga.criado_em.desc())
        .first()
    )
    if not row or row.distancia_km is None:
        return None
    return schemas.UltimaCorridaOut(distancia_km=row.distancia_km, tempo_min=row.tempo_min, data=row.data)


@router.post("/{treino_id}/exercicios", response_model=schemas.TreinoExercicioOut, status_code=201)
def adicionar_exercicio(
    treino_id: int,
    payload: schemas.AdicionarExercicioTreino,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    _obter_treino_do_usuario(db, treino_id, usuario.id)
    nome = payload.nome.strip()
    if not nome:
        raise HTTPException(422, "Nome do exercício é obrigatório")

    exercicio = (
        db.query(models.Exercicio)
        .filter(func.lower(models.Exercicio.nome) == nome.lower())
        .first()
    )
    if not exercicio:
        exercicio = models.Exercicio(nome=nome)
        db.add(exercicio)
        db.flush()

    max_ordem = (
        db.query(func.max(models.TreinoExercicio.ordem))
        .filter(models.TreinoExercicio.treino_id == treino_id)
        .scalar()
        or -1
    )
    link = models.TreinoExercicio(
        treino_id=treino_id,
        exercicio_id=exercicio.id,
        ordem=max_ordem + 1,
        series_padrao=payload.series_padrao,
        reps_padrao=payload.reps_padrao,
        carga_padrao=payload.carga_padrao,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return schemas.TreinoExercicioOut(
        treino_exercicio_id=link.id,
        exercicio_id=exercicio.id,
        nome=exercicio.nome,
        imagem_url=exercicio.imagem_url,
        ordem=link.ordem,
        series_padrao=link.series_padrao,
        reps_padrao=link.reps_padrao,
        carga_padrao=link.carga_padrao,
        ultimo=None,
    )


@router.delete("/{treino_id}/exercicios/{treino_exercicio_id}", status_code=204)
def remover_exercicio(
    treino_id: int,
    treino_exercicio_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    _obter_treino_do_usuario(db, treino_id, usuario.id)
    link = (
        db.query(models.TreinoExercicio)
        .filter(
            models.TreinoExercicio.id == treino_exercicio_id,
            models.TreinoExercicio.treino_id == treino_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(404, "Vínculo treino/exercício não encontrado")
    db.delete(link)
    db.commit()
    return None
