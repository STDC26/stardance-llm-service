import json
from pathlib import Path
from fastapi import HTTPException
from app.models.schemas import TaskType
from app.core.config import Settings


class RouterService:
    def __init__(self, settings: Settings) -> None:
        config_path = Path(settings.routing_config_path)
        with config_path.open() as f:
            config = json.load(f)
        self._rules: dict[str, dict] = {
            r["task_type"]: r for r in config["routing_rules"]
        }

    def resolve(self, task_type: TaskType, high_stakes: bool = False) -> dict:
        rule = self._rules.get(task_type.value)
        if not rule:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown task_type: '{task_type}'. Register a routing rule first.",
            )
        if high_stakes and rule.get("high_stakes_model"):
            return {**rule, "default_model": rule["high_stakes_model"]}
        return rule

    def all_task_types(self) -> list[str]:
        return list(self._rules.keys())
