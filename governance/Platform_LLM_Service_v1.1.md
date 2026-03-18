# Platform_LLM_Service_v1.1
# SD Platform LLM Service Contract
# DRJ Approved | Sprint 3

## Overview

All LLM calls across the SD platform route through the Platform LLM Service.
No system calls Anthropic API directly.

## Service

- Repo: `STDC26/sd-llm-service`
- Railway: `sd-llm-service-production.up.railway.app`
- Version: 1.0.0

## Routing

Config-driven via `app/config/routing_rules.json`. 9 task types registered.

| Task Type | Default Model | High Stakes Model |
|-----------|--------------|-------------------|
| structured_extraction | claude-haiku-4-5 | claude-sonnet-4-6 |
| trait_mapping | claude-sonnet-4-6 | claude-sonnet-4-6 |
| specification_generation | claude-sonnet-4-6 | claude-opus-4-6 |
| validation | rule_engine | claude-haiku-4-5 |
| delta_interpretation | math_layer | claude-haiku-4-5 |
| scout_synthesis | claude-sonnet-4-6 | claude-sonnet-4-6 |
| vision_assessment | claude-sonnet-4-6 | claude-sonnet-4-6 |
| output_validation | rule_engine | claude-haiku-4-5 |
| anomaly_interpretation | claude-haiku-4-5 | claude-sonnet-4-6 |

## Prompt Registry

All prompts must be registered before use. Canon-gated prompts require DRJ approval.

### BSA Prompts

| Prompt ID | Status | Authority |
|-----------|--------|-----------|
| bsa.brief_parse | ACTIVE | DTC |
| bsa.delta_interp | ACTIVE | DTC |
| bsa.scout_synth | ACTIVE | DTC |
| bsa.hcts_map | DEPRECATED (v0.9 PRE-CANON) | Requires DRJ canon approval |
| bsa.spec_gen | DEPRECATED (v0.9 PRE-CANON) | Requires DRJ canon approval |
| bsa.canon_validate | DEPRECATED (v0.9 PRE-CANON) | Requires DRJ canon approval |

Canon-gated prompts upgrade to v1.0 ACTIVE after first successful integration cycle + DRJ review.

## Call Contract

```
POST /v1/llm/call
{
  "call_id": "uuid",
  "calling_system": "BSA|BASE|CORTEX",
  "task_type": "structured_extraction|...",
  "prompt_id": "bsa.brief_parse",
  "prompt_version": "1.0.0|null",
  "payload": { ... },
  "high_stakes_flag": false,
  "cache_eligible": true,
  "cache_ttl_seconds": 86400
}
```

## Observability

- `GET /v1/llm/cost` — cost breakdown by system/model/date
- `GET /v1/llm/metrics` — latency percentiles, error rates, cache hit rates
- `GET /v1/llm/audit/{call_id}` — full audit record per call
- `GET /v1/llm/limits` — rate limit state and per-system allocation
