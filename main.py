import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.routers.webhook import router
from backend.routers.stats import router as stats_router
from backend.routers.mobile.auth import router as mobile_auth_router
from backend.routers.mobile.dashboard import router as mobile_dashboard_router
from backend.routers.mobile.squad import router as mobile_squad_router
from backend.routers.mobile.logs import router as mobile_logs_router
from backend.routers.mobile.reports import router as mobile_reports_router
from backend.routers.mobile.profile import router as mobile_profile_router
from backend.routers.mobile.notifications import router as mobile_notifications_router

# Enable LangSmith tracing at startup
os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGCHAIN_TRACING_V2).lower()
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

app = FastAPI(title="FitSquad Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(stats_router)

API_V1 = "/api/v1"
app.include_router(mobile_auth_router, prefix=API_V1)
app.include_router(mobile_dashboard_router, prefix=API_V1)
app.include_router(mobile_squad_router, prefix=API_V1)
app.include_router(mobile_logs_router, prefix=API_V1)
app.include_router(mobile_reports_router, prefix=API_V1)
app.include_router(mobile_profile_router, prefix=API_V1)
app.include_router(mobile_notifications_router, prefix=API_V1)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "fitsquad-backend"}
