"""YAML/JSON task-recipe loader.

A recipe is a declarative playbook: which tools an agent should use, the
guidance prompt, and the steps. Recipes live in ``recipes/`` and are loaded
at request time so they can be edited without a restart.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.core.errors import NotFoundError

RECIPES_DIR = Path(__file__).parent / "recipes"


@dataclass
class TaskRecipe:
    name: str
    title: str
    description: str
    tools: list[str] = field(default_factory=list)
    guidance: str = ""
    steps: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> TaskRecipe:
        return cls(
            name=name,
            title=data.get("title", name),
            description=data.get("description", ""),
            tools=list(data.get("tools", [])),
            guidance=data.get("guidance", ""),
            steps=list(data.get("steps", [])),
            raw=data,
        )


def _parse(path: Path) -> dict[str, Any]:
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text) or {}
    return json.loads(text)


def list_recipes() -> list[TaskRecipe]:
    out: list[TaskRecipe] = []
    for path in sorted(RECIPES_DIR.glob("*")):
        if path.suffix in (".yaml", ".yml", ".json"):
            out.append(TaskRecipe.from_dict(path.stem, _parse(path)))
    return out


def load_recipe(name: str) -> TaskRecipe:
    for ext in (".yaml", ".yml", ".json"):
        path = RECIPES_DIR / f"{name}{ext}"
        if path.exists():
            return TaskRecipe.from_dict(name, _parse(path))
    raise NotFoundError(f"Task recipe '{name}' not found.")
