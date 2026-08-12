from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------- Exercicio ----------


class ExercicioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    imagem_url: Optional[str] = None


# ---------- Treino: criação ----------


class NovoExercicioTreino(BaseModel):
    nome: str
    series_padrao: int = 3
    reps_padrao: int = 12
    carga_padrao: float = 0


class TreinoCreate(BaseModel):
    nome: str
    categoria: str
    tipo: str = "forca"
    duracao_min: Optional[int] = None
    exercicios: list[NovoExercicioTreino] = []


# ---------- Treino: listagem ----------


class TreinoSummary(BaseModel):
    id: int
    nome: str
    categoria: str
    tipo: str
    duracao_min: Optional[int] = None
    total_exercicios: int
    ultima_data: Optional[date] = None


# ---------- Treino: detalhe (execução / edição / admin) ----------


class UltimoValor(BaseModel):
    peso: Optional[float] = None
    series: Optional[int] = None
    reps: Optional[int] = None
    data: Optional[date] = None


class UltimaCorridaOut(BaseModel):
    distancia_km: float
    tempo_min: int
    data: date


class TreinoExercicioOut(BaseModel):
    treino_exercicio_id: int
    exercicio_id: int
    nome: str
    imagem_url: Optional[str] = None
    ordem: int
    series_padrao: int
    reps_padrao: int
    carga_padrao: float
    ultimo: Optional[UltimoValor] = None


class TreinoDetail(BaseModel):
    id: int
    nome: str
    categoria: str
    tipo: str
    duracao_min: Optional[int] = None
    exercicios: list[TreinoExercicioOut]
    ultima_data: Optional[date] = None


# ---------- Adicionar exercício a um treino existente (admin / criação) ----------


class AdicionarExercicioTreino(BaseModel):
    nome: str
    series_padrao: int = 3
    reps_padrao: int = 12
    carga_padrao: float = 0


# ---------- Registro de sessão (força) ----------


class ItemSessao(BaseModel):
    treino_exercicio_id: int
    peso: float = 0
    series: int = 1
    reps: int = 1


class SessaoCreate(BaseModel):
    treino_id: int
    data: Optional[date] = None
    itens: list[ItemSessao]


# ---------- Registro de corrida ----------


class CorridaCreate(BaseModel):
    treino_id: int
    data: Optional[date] = None
    distancia_km: float
    tempo_min: int


# ---------- Calendário ----------


class DiaExercicioLinha(BaseModel):
    nome: str
    peso: Optional[float] = None
    series: Optional[int] = None
    reps: Optional[int] = None


class DiaEntrada(BaseModel):
    treino_id: int
    label: str
    tipo: str  # 'forca' | 'corrida'
    exercicios: list[DiaExercicioLinha] = []
    distancia_km: Optional[float] = None
    tempo_min: Optional[int] = None


class DiaOut(BaseModel):
    data: date
    entradas: list[DiaEntrada]


class CalendarioMesOut(BaseModel):
    ano: int
    mes: int
    dias_com_registro: list[date]
