# App de Treino — backend

FastAPI + SQLite. Serves the REST API under `/api/*` and also serves the
static frontend (`../frontend`) at `/`, so a single process runs the whole
app.

## Rodando localmente

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000` no navegador. O banco `treino.db` é criado e
populado automaticamente (Treinos A–D, Corrida e seus exercícios) na
primeira execução.

## Instalando como PWA no iPhone

O Safari do iOS só registra o service worker (necessário para o app
funcionar como PWA instalável) em `localhost` ou em origens **HTTPS**. Para
testar no celular:

1. Rode o servidor numa máquina acessível na sua rede/local, ou publique-o
   atrás de HTTPS (ex: `ngrok http 8000`, Cloudflare Tunnel, ou qualquer
   host com TLS).
2. No iPhone, abra a URL HTTPS no Safari.
3. Toque em **Compartilhar → Adicionar à Tela de Início**.
4. O app abre em modo standalone (sem barra do Safari), com ícone e splash
   próprios.

## Estrutura de dados

- `Exercicio` — biblioteca global de exercícios.
- `Treino` — um treino (ex: "Treino A - Peito e Tríceps") ou a modalidade
  "Corrida" (`tipo='corrida'`).
- `TreinoExercicio` — vínculo treino↔exercício com séries/reps/carga padrão
  (a "biblioteca" de exercícios conhecidos daquele treino).
- `RegistroCarga` — log de uma sessão: peso/séries/reps por exercício numa
  data (treinos de força), ou distância/tempo (corrida). Registros da mesma
  sessão compartilham `sessao_id` para aparecerem agrupados no calendário.

## Endpoints principais

- `GET/POST /api/treinos`
- `GET /api/treinos/{id}` — detalhe com biblioteca de exercícios e último
  valor registrado de cada um
- `POST /api/treinos/{id}/exercicios` / `DELETE /api/treinos/{id}/exercicios/{treino_exercicio_id}`
- `GET /api/treinos/{id}/ultima-corrida`
- `POST /api/registros/sessao` / `POST /api/registros/corrida`
- `GET /api/registros/calendario?ano=&mes=`
- `GET /api/registros/dia?data=YYYY-MM-DD`
