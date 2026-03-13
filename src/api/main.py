"""FastAPI backend for MMM System."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import channels, models, optimizer, sync

app = FastAPI(title="MMM System API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sync.router)
app.include_router(channels.router)
app.include_router(models.router)
app.include_router(optimizer.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
