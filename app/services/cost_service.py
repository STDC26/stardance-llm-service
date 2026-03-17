import structlog
from app.core.config import Settings
from datetime import datetime, timezone
from typing import Any

log = structlog.get_logger()
_call_log: list[dict[str, Any]] = []


def get_call_log() -> list[dict[str, Any]]:
    return _call_log


class CostService:
    def __init__(self, settings: Settings) -> None:
        self._input_rates = settings.cost_per_million_input_tokens
        self._output_rates = settings.cost_per_million_output_tokens

    def compute(self, model: str, tokens_in: int, tokens_out: int) -> float:
        input_rate = self._input_rates.get(model, 3.00)
        output_rate = self._output_rates.get(model, 15.00)
        cost = (tokens_in / 1_000_000 * input_rate) + (tokens_out / 1_000_000 * output_rate)
        return round(cost, 6)

    async def log(self, call_id, calling_system, task_type, model, model_version, tokens_in, tokens_out, cost_usd, latency_ms, cache_hit, fallback_chain):
        entry = {"call_id": call_id, "calling_system": calling_system, "task_type": task_type, "model": model, "model_version": model_version, "tokens_in": tokens_in, "tokens_out": tokens_out, "cost_usd": cost_usd, "latency_ms": latency_ms, "cache_hit": cache_hit, "fallback_chain": fallback_chain, "logged_at": datetime.now(timezone.utc).isoformat(), "error": False}
        _call_log.append(entry)
        log.info("llm_call", **entry)
