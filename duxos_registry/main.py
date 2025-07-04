from fastapi import FastAPI
from .api.routes import router as node_router

app = FastAPI(title="DuxOS Node Registry")

app.include_router(node_router, prefix="/nodes")

# For local dev: uvicorn duxos_registry.main:app --reload 