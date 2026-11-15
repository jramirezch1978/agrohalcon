from functools import lru_cache

from app.config import ajustes
from app.fuentes.cache import CacheDisco
from app.fuentes.nasa_power import ClienteNasaPower


@lru_cache
def cliente_power() -> ClienteNasaPower:
    a = ajustes()
    return ClienteNasaPower(CacheDisco(a.cache_dir, a.cache_ttl_horas), timeout_s=a.power_timeout_s)


@lru_cache
def cliente_soilgrids() -> "ClienteSoilGrids":
    from app.fuentes.soilgrids import ClienteSoilGrids
    a = ajustes()
    return ClienteSoilGrids(CacheDisco(a.cache_dir / "soilgrids", 24 * 90))   # la textura del suelo casi no cambia: 90 días
