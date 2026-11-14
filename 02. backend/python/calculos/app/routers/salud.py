from fastapi import APIRouter

router = APIRouter()


@router.get("/salud")
async def salud() -> dict:
    return {"estado": "ok", "servicio": "agroshift-calculos", "fase": 1}
