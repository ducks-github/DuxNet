from fastapi import FastAPI
from .api.routes import router as node_router
from .api.wallet_routes import router as wallet_router

app = FastAPI(
    title="DuxOS Node Registry",
    description="Integrated node registry with wallet functionality",
    version="2.2.0"
)

app.include_router(node_router, prefix="/nodes")
app.include_router(wallet_router)

# For local dev: uvicorn duxos_registry.main:app --reload 