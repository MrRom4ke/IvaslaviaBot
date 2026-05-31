from fastapi import APIRouter

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
def stats_overview() -> dict:
    return {"note": "TODO: implement statistics"}
