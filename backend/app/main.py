import os
import secrets

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from . import models
from .database import UPLOADS_DIR, engine
from .routers import auth, exercicios, registros, treinos

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="App de Treino API")

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    # Sem SECRET_KEY definida (uso local): gera uma por processo. Todas as
    # sessões caem quando o servidor reinicia. Em produção, defina SECRET_KEY
    # como variável de ambiente para as sessões sobreviverem a um restart/deploy.
    SECRET_KEY = secrets.token_hex(32)

HTTPS_ONLY = os.environ.get("SESSION_HTTPS_ONLY", "false").lower() == "true"

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=HTTPS_ONLY,
    max_age=60 * 60 * 24 * 30,  # 30 dias
)

app.include_router(auth.router)
app.include_router(treinos.router)
app.include_router(exercicios.router)
app.include_router(registros.router)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend"
)


@app.get("/sw.js")
def service_worker():
    # Nunca deixa nenhum cache (navegador, CDN) guardar o service worker —
    # sem isso o navegador pode demorar a perceber que existe uma versão nova.
    return FileResponse(
        os.path.join(FRONTEND_DIR, "sw.js"),
        media_type="text/javascript",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
