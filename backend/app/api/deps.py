from functools import lru_cache

from app.container import build_orchestrator


@lru_cache(maxsize=1)
def get_orchestrator():
    return build_orchestrator()
