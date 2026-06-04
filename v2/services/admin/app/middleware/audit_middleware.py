import json
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from v2.services.admin.app.core.security import decode_access_token
from v2.services.admin.app.services.audit_service import audit_service
from v2.shared.db.models import Admin
from v2.shared.db.session import SessionLocal


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware для автоматического логирования действий администраторов."""

    AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    AUDITABLE_PATHS = {
        "/applications": "application",
        "/drawings": "drawing",
        "/operator-tickets": "ticket",
        "/winners": "winner",
        "/channels": "channel",
        "/moderation": "moderation",
    }

    ACTION_MAPPING = {
        ("POST", "/applications/{application_id}/moderate-profile"): "moderate_profile",
        ("POST", "/applications/{application_id}/moderate-payment"): "moderate_payment",
        ("POST", "/drawings"): "create_drawing",
        ("PATCH", "/drawings/{drawing_id}"): "update_drawing",
        ("DELETE", "/drawings/{drawing_id}"): "delete_drawing",
        ("POST", "/drawings/{drawing_id}/select-winners"): "select_winners_random",
        ("POST", "/drawings/{drawing_id}/select-winners-manual"): "select_winners_manual",
        ("POST", "/operator-tickets/{ticket_id}/reply"): "reply_ticket",
        ("PATCH", "/operator-tickets/{ticket_id}/status"): "update_ticket_status",
        ("POST", "/channels"): "create_channel",
        ("DELETE", "/channels/{channel_id}"): "delete_channel",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Сохраняем body для логирования (только для небольших запросов)
        body_for_log = None
        if request.method in self.AUDITABLE_METHODS:
            try:
                body_bytes = await request.body()
                if len(body_bytes) < 10000:  # Логируем только небольшие body
                    body_for_log = json.loads(body_bytes.decode()) if body_bytes else None
                # Восстанавливаем body для handler
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except Exception:
                pass

        response = await call_next(request)

        # Логируем только успешные запросы от авторизованных админов
        if response.status_code < 400 and request.method in self.AUDITABLE_METHODS:
            self._log_request_sync(request, body_for_log)

        return response

    def _log_request_sync(self, request: Request, body_for_log: dict | None) -> None:
        """Синхронно логирует запрос администратора."""
        path = request.url.path

        # Проверяем, нужно ли логировать этот путь
        should_audit = any(path.startswith(audit_path) for audit_path in self.AUDITABLE_PATHS)
        if not should_audit:
            return

        # Получаем информацию об админе из токена
        admin_id, admin_username = self._extract_admin_from_token(request)
        if not admin_username or not admin_id:
            return

        # Определяем тип действия
        action = self._determine_action(request.method, path)
        entity_type = self._determine_entity_type(path)
        entity_id = self._extract_entity_id(path)

        # Получаем IP и User-Agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Записываем в БД
        db = SessionLocal()
        try:
            audit_service.log_action(
                db=db,
                admin_id=admin_id,
                admin_username=admin_username,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=body_for_log,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception:
            pass
        finally:
            db.close()

    def _determine_action(self, method: str, path: str) -> str:
        """Определяет действие на основе метода и пути."""
        # Нормализуем путь, заменяя ID на шаблон
        normalized_path = path
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part.isdigit():
                parts[i] = "{" + parts[i-1].rstrip("s") + "_id}"
        normalized_path = "/".join(parts)

        # Ищем в маппинге
        key = (method, normalized_path)
        if key in self.ACTION_MAPPING:
            return self.ACTION_MAPPING[key]

        # Стандартные действия
        if method == "POST":
            return "create"
        elif method == "PATCH" or method == "PUT":
            return "update"
        elif method == "DELETE":
            return "delete"

        return method.lower()

    def _determine_entity_type(self, path: str) -> str | None:
        """Определяет тип сущности на основе пути."""
        for audit_path, entity in self.AUDITABLE_PATHS.items():
            if path.startswith(audit_path):
                return entity
        return None

    def _extract_entity_id(self, path: str) -> int | None:
        """Извлекает ID сущности из пути."""
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part.isdigit() and i > 0:
                return int(part)
        return None

    def _extract_admin_from_token(self, request: Request) -> tuple[int | None, str | None]:
        """Извлекает информацию об админе из токена авторизации."""
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None, None

        token = auth_header[7:]
        payload = decode_access_token(token)
        if not payload:
            return None, None

        username = payload.get("sub")
        if not username:
            return None, None

        # Получаем admin_id из БД
        db = SessionLocal()
        try:
            admin = db.query(Admin).filter(Admin.username == username).one_or_none()
            if admin and admin.is_active:
                return admin.id, admin.username
        except Exception:
            pass
        finally:
            db.close()

        return None, None
