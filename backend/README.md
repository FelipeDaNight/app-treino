# App de Treino — backend

FastAPI + SQLite. Serve a API REST em `/api/*` e também o frontend estático
(`../frontend`) em `/`, então um único processo roda o app inteiro.
Multiusuário: cada conta tem login próprio e vê só os próprios treinos e
registros.

## Rodando localmente

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000` — a primeira tela é login/cadastro. Ao criar
uma conta, ela já vem com os Treinos A–D e Corrida (e seus exercícios)
prontos para usar; nenhuma sessão/registro de exemplo é criada, só o que
você realmente registrar aparece no histórico.

Sem a variável `SECRET_KEY` definida, o servidor gera uma aleatória a cada
início — funciona para testar, mas todo mundo é deslogado a cada restart.

## Instalando como PWA no iPhone

O Safari do iOS só registra o service worker (necessário para o app
funcionar como PWA instalável) em `localhost` ou em origens **HTTPS**.
Depois do deploy (veja abaixo), a URL pública já vem em HTTPS — é só abrir
no Safari do iPhone, tocar em **Compartilhar → Adicionar à Tela de Início**,
e o app abre em modo standalone (sem barra do Safari), com ícone próprio.

## Deploy no Fly.io (grátis, com volume persistente)

O banco SQLite e as fotos de perfil precisam sobreviver a restarts e
deploys — por isso usamos um volume persistente, não o disco efêmero de
containers comuns.

```bash
# instala a CLI do Fly.io (rode isso na SUA máquina, não neste sandbox)
curl -L https://fly.io/install.sh | sh
fly auth login

# na raiz do projeto (onde estão Dockerfile e fly.toml)
fly launch --no-deploy   # detecta o Dockerfile e o fly.toml existentes; ajuste o nome do app se pedir
fly volumes create app_treino_data --size 1 --region gru

# gera e define a chave de sessão (nunca comite isso em nenhum arquivo)
fly secrets set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

fly deploy
```

Depois disso, `fly.toml` já aponta o volume para `/data` (onde o
`DATA_DIR` do app grava `treino.db` e a pasta `uploads/`), força HTTPS, e
configura o cookie de sessão como `Secure` (via `SESSION_HTTPS_ONLY=true`).
`fly status` mostra a URL pública (`https://<app>.fly.dev`).

Esse fluxo não pode ser executado a partir deste ambiente de sessão —
a rede daqui bloqueia fly.io, ngrok, Docker Hub e a maioria dos hosts
externos (só libera GitHub e registries de pacotes). Rode os comandos
acima na sua máquina.

## Variáveis de ambiente

| Variável              | Obrigatória em produção | Efeito                                                             |
| ---------------------- | ------------------------ | -------------------------------------------------------------------- |
| `SECRET_KEY`           | Sim                       | Assina o cookie de sessão. Sem ela, todo mundo é deslogado a cada restart. |
| `DATA_DIR`             | Recomendada               | Pasta onde ficam `treino.db` e `uploads/`. Aponte para o volume persistente. |
| `SESSION_HTTPS_ONLY`   | Sim (atrás de HTTPS)      | `true` marca o cookie de sessão como `Secure` (só trafega em HTTPS). |

## Estrutura de dados

- `Usuario` — conta de login (usuário, hash de senha, foto de perfil).
- `Exercicio` — biblioteca global de exercícios (nome + imagem), compartilhada
  entre contas apenas como referência (sem dado pessoal).
- `Treino` — um treino (ex: "Treino A - Peito e Tríceps") ou a modalidade
  "Corrida" (`tipo='corrida'"), pertence a um `Usuario`.
- `TreinoExercicio` — vínculo treino↔exercício com séries/reps/carga padrão
  (a "biblioteca" de exercícios conhecidos daquele treino).
- `RegistroCarga` — log de uma sessão: peso/séries/reps por exercício numa
  data (treinos de força), ou distância/tempo (corrida), pertence a um
  `Usuario`. Registros da mesma sessão compartilham `sessao_id` para
  aparecerem agrupados no calendário (e podem ser excluídos juntos).

## Autenticação

Sessão via cookie assinado e `httpOnly` (sem token exposto ao JS). Toda
rota de `/api/treinos`, `/api/exercicios` e `/api/registros` exige login e
filtra os dados pelo usuário da sessão — pedir o `id` de um treino de outra
conta retorna 404, não os dados de outra pessoa.

- `POST /api/auth/signup` — cria conta (nome de usuário único, senha ≥ 8
  caracteres, hash bcrypt), já semeia os treinos padrão e loga automaticamente
- `POST /api/auth/login` / `POST /api/auth/logout`
- `GET /api/auth/me` — usuário logado (ou `null`)
- `POST /api/auth/foto` — upload de foto de perfil (JPEG/PNG/WEBP, até 5MB)

## Endpoints principais

- `GET/POST /api/treinos`
- `GET /api/treinos/{id}` — detalhe com biblioteca de exercícios e último
  valor registrado de cada um
- `POST /api/treinos/{id}/exercicios` / `DELETE /api/treinos/{id}/exercicios/{treino_exercicio_id}`
- `GET /api/treinos/{id}/ultima-corrida`
- `POST /api/registros/sessao` / `POST /api/registros/corrida`
- `GET /api/registros/calendario?ano=&mes=`
- `GET /api/registros/dia?data=YYYY-MM-DD`
- `DELETE /api/registros/sessao/{sessao_id}` — apaga um treino salvo de um
  dia (e o dia some do calendário se não sobrar nenhum registro)
