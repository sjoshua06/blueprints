from fastapi import FastAPI

from api.setup_routes import router as setup_router
from api.user_routes import router as user_router
from api.project_router import router as project_router
from api.bom_routes import router as bom_router

app = FastAPI(title="Supply Chain AI Backend")

app.include_router(setup_router)
app.include_router(user_router)
app.include_router(project_router)
app.include_router(bom_router)