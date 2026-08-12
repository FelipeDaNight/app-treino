from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Exercicio(Base):
    """Biblioteca global de exercícios (nome + imagem placeholder)."""

    __tablename__ = "exercicios"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False, unique=True)
    imagem_url = Column(String, nullable=True)

    treino_links = relationship(
        "TreinoExercicio", back_populates="exercicio", cascade="all, delete-orphan"
    )


class Treino(Base):
    """Um treino (ex: 'Treino A - Peito e Tríceps') ou a modalidade 'Corrida'."""

    __tablename__ = "treinos"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    tipo = Column(String, nullable=False, default="forca")  # 'forca' | 'corrida'
    duracao_min = Column(Integer, nullable=True)
    ordem = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)

    exercicios = relationship(
        "TreinoExercicio",
        back_populates="treino",
        cascade="all, delete-orphan",
        order_by="TreinoExercicio.ordem",
    )
    registros = relationship(
        "RegistroCarga", back_populates="treino", cascade="all, delete-orphan"
    )


class TreinoExercicio(Base):
    """Vínculo treino<->exercício com séries/reps/carga padrão (biblioteca do treino)."""

    __tablename__ = "treino_exercicios"

    id = Column(Integer, primary_key=True)
    treino_id = Column(Integer, ForeignKey("treinos.id"), nullable=False)
    exercicio_id = Column(Integer, ForeignKey("exercicios.id"), nullable=False)
    ordem = Column(Integer, default=0)
    series_padrao = Column(Integer, default=3)
    reps_padrao = Column(Integer, default=12)
    carga_padrao = Column(Float, default=0)

    treino = relationship("Treino", back_populates="exercicios")
    exercicio = relationship("Exercicio", back_populates="treino_links")


class RegistroCarga(Base):
    """Log de uma sessão: peso/séries/reps (força) ou distância/tempo (corrida) numa data."""

    __tablename__ = "registros_carga"

    id = Column(Integer, primary_key=True)
    treino_id = Column(Integer, ForeignKey("treinos.id"), nullable=False)
    exercicio_id = Column(Integer, ForeignKey("exercicios.id"), nullable=True)
    sessao_id = Column(String, nullable=True, index=True)
    data = Column(Date, nullable=False, index=True)
    peso = Column(Float, nullable=True)
    series = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    distancia_km = Column(Float, nullable=True)
    tempo_min = Column(Integer, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    treino = relationship("Treino", back_populates="registros")
    exercicio = relationship("Exercicio")
