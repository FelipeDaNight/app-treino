"""Seed por usuário: cria os Treinos A-D + Corrida com sua biblioteca de
exercícios (séries/reps/carga padrão) para uma conta recém-cadastrada,
sem nenhuma sessão/registro de exemplo — todo o histórico de treinos deve
vir de sessões reais que o usuário registrou.
"""

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


def seed_treinos_padrao(db: Session, usuario_id: int) -> None:
    """Cria a biblioteca padrão de treinos para uma conta nova. Não commita —
    quem chama decide quando persistir (normalmente junto da criação do
    usuário, na mesma transação)."""

    for i, t in enumerate(TREINOS):
        treino = models.Treino(
            usuario_id=usuario_id,
            nome=t["nome"],
            categoria=t["categoria"],
            tipo=t["tipo"],
            duracao_min=t["duracao_min"],
            ordem=i,
        )
        db.add(treino)
        db.flush()

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
