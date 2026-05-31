import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from v2.services.admin.app.api.routes.applications import router as applications_router
from v2.services.admin.app.api.routes.auth import router as auth_router
from v2.services.admin.app.api.routes.drawings import router as drawings_router
from v2.services.admin.app.api.routes.health import router as health_router
from v2.services.admin.app.api.routes.moderation import router as moderation_router
from v2.services.admin.app.api.routes.stats import router as stats_router
from v2.services.admin.app.api.routes.storage import router as storage_router
from v2.services.admin.app.api.routes.tickets import router as tickets_router
from v2.services.admin.app.api.routes.winners import router as winners_router
from v2.services.admin.app.core.config import settings

app = FastAPI(title=settings.app_name)

# CSP Middleware для разрешения загрузки изображений
class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Разрешаем загрузку изображений и внешних ресурсов для Swagger UI
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' http://localhost:8000; "
            "img-src 'self' data: http: https:; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' data: https://cdn.jsdelivr.net;"
        )
        # Отключаем кэширование для HTML-страниц
        if request.url.path.endswith(('.html', '/')) or '/admin' in request.url.path:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(CSPMiddleware)

# CORS для работы фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Миграции теперь управляются через Alembic.
# Запуск миграций: alembic upgrade head

# Статические файлы для админ-панели - используем абсолютный путь
static_dir = Path("/app/v2/services/admin/static")
if static_dir.exists() and static_dir.is_dir():
    app.mount("/admin", StaticFiles(directory=str(static_dir), html=True), name="admin")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(drawings_router)
app.include_router(applications_router)
app.include_router(moderation_router)
app.include_router(tickets_router)
app.include_router(stats_router)
app.include_router(winners_router)
app.include_router(storage_router)
