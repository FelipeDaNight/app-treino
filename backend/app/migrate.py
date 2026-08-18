"""Migrações leves e idempotentes, rodadas no startup.

`Base.metadata.create_all()` só cria tabelas que ainda não existem — não
altera tabelas já existentes para adicionar colunas novas. Como não há
Alembic configurado (SQLite + app pequeno), fazemos isso manualmente aqui:
checa se a coluna já existe e, se não, adiciona com ALTER TABLE. Rodar de
novo não faz nada (idempotente).
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _tem_coluna(engine: Engine, tabela: str, coluna: str) -> bool:
    inspetor = inspect(engine)
    colunas = {c["name"] for c in inspetor.get_columns(tabela)}
    return coluna in colunas


def rodar_migracoes(engine: Engine) -> None:
    if not _tem_coluna(engine, "registros_carga", "foto_url"):
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE registros_carga ADD COLUMN foto_url VARCHAR"))

    # Índices que faltavam nas colunas mais consultadas do app (adicionados
    # depois que o banco já existia — CREATE INDEX IF NOT EXISTS é seguro
    # de rodar de novo).
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_treino_exercicios_treino_id "
                "ON treino_exercicios (treino_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_registros_carga_treino_id "
                "ON registros_carga (treino_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_registros_carga_exercicio_id "
                "ON registros_carga (exercicio_id)"
            )
        )
