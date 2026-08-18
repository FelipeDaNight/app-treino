import calendar
import uuid
from collections import OrderedDict
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db
from ..uploads import remover_imagem_upload, salvar_imagem_upload

router = APIRouter(prefix="/api/registros", tags=["registros"])


def _obter_treino_do_usuario(db: Session, treino_id: int, usuario_id: int) -> models.Treino:
    treino = (
        db.query(models.Treino)
        .filter(models.Treino.id == treino_id, models.Treino.usuario_id == usuario_id)
        .first()
    )
    if not treino:
        raise HTTPException(404, "Treino não encontrado")
    return treino


@router.post("/foto", response_model=schemas.FotoUploadOut)
async def upload_foto_sessao(
    arquivo: UploadFile = File(...),
    usuario: models.Usuario = Depends(get_current_user),
):
    foto_url = await salvar_imagem_upload(arquivo, f"sessao-{usuario.id}")
    return schemas.FotoUploadOut(foto_url=foto_url)


@router.post("/sessao", response_model=list[int], status_code=201)
def salvar_sessao(
    payload: schemas.SessaoCreate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    _obter_treino_do_usuario(db, payload.treino_id, usuario.id)
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
            usuario_id=usuario.id,
            treino_id=payload.treino_id,
            exercicio_id=link.exercicio_id,
            sessao_id=sessao_id,
            data=data,
            peso=item.peso,
            series=item.series,
            reps=item.reps,
            foto_url=payload.foto_url,
        )
        db.add(registro)
        db.flush()
        ids.append(registro.id)

    db.commit()
    return ids


@router.post("/corrida", response_model=int, status_code=201)
def salvar_corrida(
    payload: schemas.CorridaCreate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    _obter_treino_do_usuario(db, payload.treino_id, usuario.id)

    data = payload.data or date.today()
    registro = models.RegistroCarga(
        usuario_id=usuario.id,
        treino_id=payload.treino_id,
        exercicio_id=None,
        sessao_id=uuid.uuid4().hex,
        data=data,
        distancia_km=payload.distancia_km,
        tempo_min=payload.tempo_min,
        foto_url=payload.foto_url,
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
    usuario: models.Usuario = Depends(get_current_user),
):
    primeiro = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    ultimo = date(ano, mes, ultimo_dia)

    rows = (
        db.query(models.RegistroCarga.data)
        .filter(
            models.RegistroCarga.usuario_id == usuario.id,
            models.RegistroCarga.data >= primeiro,
            models.RegistroCarga.data <= ultimo,
        )
        .distinct()
        .all()
    )
    dias = sorted({r[0] for r in rows})
    return schemas.CalendarioMesOut(ano=ano, mes=mes, dias_com_registro=dias)


@router.get("/dia", response_model=schemas.DiaOut)
def registros_do_dia(
    data: date = Query(...),
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    rows = (
        db.query(models.RegistroCarga)
        .filter(models.RegistroCarga.usuario_id == usuario.id, models.RegistroCarga.data == data)
        .order_by(models.RegistroCarga.criado_em, models.RegistroCarga.id)
        .all()
    )

    grupos: "OrderedDict[str, list[models.RegistroCarga]]" = OrderedDict()
    for row in rows:
        chave = row.sessao_id or f"registro-{row.id}"
        grupos.setdefault(chave, []).append(row)

    entradas = []
    for chave, itens in grupos.items():
        primeiro = itens[0]
        treino = primeiro.treino
        if treino.tipo == "corrida":
            entradas.append(
                schemas.DiaEntrada(
                    sessao_id=chave,
                    treino_id=treino.id,
                    label=treino.nome,
                    tipo="corrida",
                    distancia_km=primeiro.distancia_km,
                    tempo_min=primeiro.tempo_min,
                    foto_url=primeiro.foto_url,
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
                    sessao_id=chave,
                    treino_id=treino.id,
                    label=treino.nome,
                    tipo="forca",
                    exercicios=linhas,
                    foto_url=primeiro.foto_url,
                )
            )

    return schemas.DiaOut(data=data, entradas=entradas)


@router.delete("/sessao/{sessao_id}", status_code=204)
def excluir_sessao(
    sessao_id: str,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    if sessao_id.startswith("registro-"):
        try:
            registro_id = int(sessao_id.removeprefix("registro-"))
        except ValueError:
            raise HTTPException(404, "Sessão não encontrada")
        query = db.query(models.RegistroCarga).filter(
            models.RegistroCarga.id == registro_id, models.RegistroCarga.usuario_id == usuario.id
        )
    else:
        query = db.query(models.RegistroCarga).filter(
            models.RegistroCarga.sessao_id == sessao_id, models.RegistroCarga.usuario_id == usuario.id
        )

    linhas = query.all()
    if not linhas:
        raise HTTPException(404, "Sessão não encontrada")
    foto_url = linhas[0].foto_url

    for linha in linhas:
        db.delete(linha)
    db.commit()

    remover_imagem_upload(foto_url)
    return None
