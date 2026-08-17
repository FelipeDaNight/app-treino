# App de Treino

App de treino de academia/corrida, mobile-first, com backend real (não é
mais um protótipo em mock). Cada usuário cria sua conta, monta seus
treinos, registra o que fez em cada sessão (peso, séries, reps ou
distância/tempo pra corrida) e acompanha tudo por um calendário. Funciona
como PWA — dá pra instalar na tela de início do iPhone e abrir sem barra
do Safari.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite. Autenticação por sessão em
  cookie assinado (`bcrypt` pro hash de senha).
- **Frontend:** HTML/CSS/JS puro (sem framework, sem build step) — servido
  como estático pelo próprio FastAPI. Tema escuro com laranja de destaque.
- **Deploy:** Dockerfile + `fly.toml` prontos pro Fly.io (plano grátis com
  volume persistente).

## Funcionalidades

- Login e cadastro — cada conta só vê os próprios treinos e histórico.
- Montar treinos (nome, categoria, exercícios com séries/reps/carga,
  reordenáveis).
- Executar um treino do dia: escolhe os exercícios feitos, ajusta peso/
  séries/reps com steppers de toque, salva a sessão.
- Registrar corrida (distância + tempo).
- Calendário por mês/ano: dias com treino ficam marcados; clicar num dia
  mostra o que foi feito, com opção de excluir o registro.
- Administrar exercícios: criar novos exercícios e vinculá-los a um treino.
- Perfil: foto e logoff.

## Rodando localmente

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000` — a primeira tela é login/cadastro. Detalhes
de configuração (variáveis de ambiente, deploy no Fly.io, estrutura de
dados, endpoints) estão em [`backend/README.md`](backend/README.md).

## Estrutura do repositório

```
backend/    API FastAPI + banco SQLite
frontend/   HTML/CSS/JS estático servido pelo backend
Dockerfile  imagem pra deploy
fly.toml    configuração do Fly.io (volume persistente)
project/    protótipo visual original (Claude Design) — histórico, não é o app real
chats/      transcrição das conversas de design do protótipo — histórico
```

`project/` e `chats/` são o material original do protótipo visual que deu
origem a este app; ficam aqui como referência de como o design foi
pensado, mas o código que roda de verdade é `backend/` + `frontend/`.
