from fastapi import FastAPI

from api.setup_routes import router as setup_router
from api.user_routes import router as user_router

from api.bom_routes import router as bom_router
from api.risk_routes import router as risk_router
from api.dashboard_router import router as dashboard_router
from api.internal_risk_routes import router as internal_risk_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Supply Chain AI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allowed domains
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST, PUT, DELETE
    allow_headers=["*"],          # all headers
)
app.include_router(setup_router)
app.include_router(user_router)

app.include_router(bom_router)
app.include_router(risk_router)
app.include_router(dashboard_router)
app.include_router(internal_risk_router)
