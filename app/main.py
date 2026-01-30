from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router

app = FastAPI(
    title="Quiz Programming API",
    description="API Backend pour l'application de quiz de programmation",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis les applications frontend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*","http://localhost:8080"],   # toutes les origines
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, PATCH, etc.
    allow_headers=["*"],   # tous les headers
)

app.include_router(router, prefix="")
