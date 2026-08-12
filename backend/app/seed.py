"""Seed inicial: replica os dados do protótipo (Treinos A-D + Corrida, com
biblioteca de exercícios e um histórico recente de sessões), usando datas
relativas a hoje para que o app não comece "vazio".
"""

import uuid
from datetime import date, timedelta

from sqlalchemy.orm import Session

from . import models

TREINOS = [
    {
        "nome": "Treino A - Peito e Tríceps",
        "categoria": "Superiores",
        "tipo": "forca",
        "duracao_min": 45,
        "exercicios": [
            ("Supino reto com barra", 40, 4, 10),
            ("Supino inclinado com halteres", 16, 3, 12),
            ("Crucifixo com halteres", 14, 3, 12),
            ("Crossover no cabo", 12, 3, 12),
            ("Supino máquina", 35, 3, 10),
            ("Tríceps corda", 20, 3, 15),
            ("Tríceps testa", 16, 3, 12),
            ("Mergulho no banco", 0, 3, 15),
        ],
    },
    {
        "nome": "Treino B - Pernas",
        "categoria": "Inferiores",
        "tipo": "forca",
        "duracao_min": 50,
        "exercicios": [
            ("Agachamento livre", 60, 4, 10),
            ("Leg press", 90, 4, 12),
            ("Cadeira extensora", 35, 3, 15),
            ("Cadeira flexora", 30, 3, 15),
            ("Afundo com halteres", 10, 3, 12),
            ("Stiff com barra", 40, 3, 12),
            ("Panturrilha em pé", 40, 4, 15),
            ("Panturrilha sentado", 25, 3, 15),
        ],
    },
    {
        "nome": "Treino C - Costas e Bíceps",
        "categoria": "Superiores",
        "tipo": "forca",
        "duracao_min": 45,
        "exercicios": [
            ("Puxada frontal", 45, 4, 10),
            ("Remada curvada", 40, 4, 10),
            ("Remada unilateral", 18, 3, 12),
            ("Puxada aberta", 42, 3, 10),
            ("Rosca direta", 14, 3, 12),
            ("Rosca alternada", 12, 3, 12),
            ("Rosca martelo", 12, 3, 12),
        ],
    },
    {
        "nome": "Treino D - Ombro e Abdômen",
        "categoria": "Ombro",
        "tipo": "forca",
        "duracao_min": 35,
        "exercicios": [
            ("Desenvolvimento com halteres", 12, 4, 10),
            ("Elevação lateral", 8, 3, 15),
            ("Elevação frontal", 8, 3, 15),
            ("Encolhimento de trapézio", 20, 3, 12),
            ("Abdominal supra", 0, 3, 20),
            ("Prancha isométrica", 0, 3, 1),
        ],
    },
    {
        "nome": "Corrida",
        "categoria": "Cardio",
        "tipo": "corrida",
        "duracao_min": 30,
        "exercicios": [],
    },
]


def _get_or_create_exercicio(db: Session, nome: str) -> models.Exercicio:
    ex = db.query(models.Exercicio).filter(models.Exercicio.nome == nome).first()
    if ex:
        return ex
    ex = models.Exercicio(nome=nome)
    db.add(ex)
    db.flush()
    return ex


def seed_if_empty(db: Session) -> None:
    if db.query(models.Treino).first() is not None:
        return

    treinos_by_nome: dict[str, models.Treino] = {}
    exercicios_by_treino: dict[str, dict[str, models.TreinoExercicio]] = {}

    for i, t in enumerate(TREINOS):
        treino = models.Treino(
            nome=t["nome"],
            categoria=t["categoria"],
            tipo=t["tipo"],
            duracao_min=t["duracao_min"],
            ordem=i,
        )
        db.add(treino)
        db.flush()
        treinos_by_nome[t["nome"]] = treino
        exercicios_by_treino[t["nome"]] = {}

        for j, (nome, carga, series, reps) in enumerate(t["exercicios"]):
            exercicio = _get_or_create_exercicio(db, nome)
            link = models.TreinoExercicio(
                treino_id=treino.id,
                exercicio_id=exercicio.id,
                ordem=j,
                series_padrao=series,
                reps_padrao=reps,
                carga_padrao=carga,
            )
            db.add(link)
            exercicios_by_treino[t["nome"]][nome] = link

    db.flush()

    today = date.today()

    def add_sessao(treino_nome: str, dias_atras: int, itens: list[tuple[str, float, int, int]]):
        treino = treinos_by_nome[treino_nome]
        data = today - timedelta(days=dias_atras)
        sessao_id = uuid.uuid4().hex
        for nome, peso, series, reps in itens:
            exercicio = _get_or_create_exercicio(db, nome)
            db.add(
                models.RegistroCarga(
                    treino_id=treino.id,
                    exercicio_id=exercicio.id,
                    sessao_id=sessao_id,
                    data=data,
                    peso=peso,
                    series=series,
                    reps=reps,
                )
            )

    def add_corrida(dias_atras: int, distancia_km: float, tempo_min: int):
        treino = treinos_by_nome["Corrida"]
        data = today - timedelta(days=dias_atras)
        db.add(
            models.RegistroCarga(
                treino_id=treino.id,
                exercicio_id=None,
                sessao_id=uuid.uuid4().hex,
                data=data,
                distancia_km=distancia_km,
                tempo_min=tempo_min,
            )
        )

    add_sessao(
        "Treino A - Peito e Tríceps",
        9,
        [
            ("Supino reto com barra", 40, 4, 10),
            ("Supino inclinado com halteres", 16, 3, 12),
            ("Crucifixo com halteres", 14, 3, 12),
            ("Tríceps corda", 20, 3, 15),
        ],
    )
    add_corrida(8, 5, 32)
    add_sessao(
        "Treino B - Pernas",
        6,
        [
            ("Agachamento livre", 60, 4, 10),
            ("Leg press", 90, 4, 12),
            ("Cadeira extensora", 35, 3, 15),
        ],
    )
    add_sessao(
        "Treino C - Costas e Bíceps",
        4,
        [
            ("Puxada frontal", 45, 4, 10),
            ("Remada curvada", 40, 4, 10),
            ("Rosca direta", 14, 3, 12),
        ],
    )
    add_corrida(4, 3, 18)
    add_sessao(
        "Treino D - Ombro e Abdômen",
        2,
        [
            ("Desenvolvimento com halteres", 12, 4, 10),
            ("Elevação lateral", 8, 3, 15),
            ("Abdominal supra", 0, 3, 20),
        ],
    )

    db.commit()
