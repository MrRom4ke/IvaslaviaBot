from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

router = APIRouter(prefix="/storage", tags=["storage"])

STORAGE_PATH = Path("/app/v2/storage/files")


@router.get("/files/{file_path:path}")
def get_file(file_path: str) -> FileResponse:
    """
    Получить файл из storage.
    В production это должно быть заменено на S3/CDN.
    """
    full_path = STORAGE_PATH / file_path

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Проверка, что файл находится внутри STORAGE_PATH (защита от path traversal)
    try:
        full_path.resolve().relative_to(STORAGE_PATH.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return FileResponse(full_path)
