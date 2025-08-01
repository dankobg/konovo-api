import os
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.errors import register_app_exception_handlers
from app.routes import router
from app.services import KONOVO_BASE_URL, AuthService, ProductService


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        base_url=KONOVO_BASE_URL,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    app.state.auth_service = AuthService(app.state.http_client)
    app.state.product_service = ProductService(app.state.http_client)
    yield
    await app.state.http_client.aclose()


app = FastAPI(
    lifespan=lifespan,
    title="Konovo API",
    summary="konovo api task",
    description="konovo api full-stack example",
    version="1.0.0",
    servers=[{"url": "http://localhost:8000", "description": "dev server"}],
)


register_app_exception_handlers(app)

allow_origins = (os.getenv("CORS_ALLOW_ORIGINS") or "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[*allow_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
