import os
from pathlib import Path

from aiogram import Bot

from v2.services.bot.app.core.config import settings


class FileStorageService:
    """Сервис для скачивания и хранения файлов из Telegram."""

    def __init__(self, storage_path: str = "/app/v2/storage/files"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def download_telegram_file(
        self,
        bot: Bot,
        file_id: str,
        user_id: int,
        drawing_id: int,
        evidence_type: str,
    ) -> str:
        """
        Скачивает файл из Telegram и сохраняет локально.

        Returns:
            Путь к сохраненному файлу относительно storage_path
        """
        file = await bot.get_file(file_id)
        if file.file_path is None:
            raise ValueError("File path is None")

        # Определяем расширение файла
        file_ext = Path(file.file_path).suffix or ".jpg"

        # Создаем структуру директорий: drawing_id/user_id/evidence_type/
        target_dir = self.storage_path / str(drawing_id) / str(user_id) / evidence_type
        target_dir.mkdir(parents=True, exist_ok=True)

        # Имя файла: file_unique_id + расширение
        file_name = f"{file.file_unique_id}{file_ext}"
        target_path = target_dir / file_name

        # Скачиваем файл
        await bot.download_file(file.file_path, target_path)

        # Возвращаем относительный путь
        relative_path = target_path.relative_to(self.storage_path)
        return str(relative_path)

    def get_file_url(self, file_key: str) -> str:
        """
        Генерирует URL для доступа к файлу.
        В production это может быть S3 URL или CDN.
        """
        # Для локальной разработки возвращаем путь к файлу
        return f"/storage/files/{file_key}"

    def file_exists(self, file_key: str) -> bool:
        """Проверяет существование файла."""
        file_path = self.storage_path / file_key
        return file_path.exists()


# Singleton instance
file_storage = FileStorageService()
