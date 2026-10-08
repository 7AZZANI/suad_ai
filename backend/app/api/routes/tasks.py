from __future__ import annotations

from fastapi import APIRouter

from app.tasks import list_recipes, load_recipe

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("")
async def all_recipes() -> list[dict]:
    return [
        {
            "name": r.name,
            "title": r.title,
            "description": r.description,
            "tools": r.tools,
        }
        for r in list_recipes()
    ]


@router.get("/{name}")
async def get_recipe(name: str) -> dict:
    r = load_recipe(name)
    return {
        "name": r.name,
        "title": r.title,
        "description": r.description,
        "tools": r.tools,
        "guidance": r.guidance,
        "steps": r.steps,
    }
