import pytest, json
from unittest.mock import MagicMock
from app.services.router_service import RouterService
from app.models.schemas import TaskType
from fastapi import HTTPException

@pytest.fixture
def router_svc(tmp_path):
    config = {"version":"1.0.0","routing_rules":[
        {"task_type":"structured_extraction","default_model":"claude-haiku-4-5","high_stakes_model":"claude-sonnet-4-6","fallback_model":"claude-sonnet-4-6","deterministic_first":False,"cache_ttl_seconds":86400,"max_tokens":1024},
        {"task_type":"trait_mapping","default_model":"claude-sonnet-4-6","high_stakes_model":"claude-sonnet-4-6","fallback_model":"claude-sonnet-4-6","deterministic_first":False,"cache_ttl_seconds":86400,"max_tokens":2048},
        {"task_type":"specification_generation","default_model":"claude-sonnet-4-6","high_stakes_model":"claude-opus-4-6","fallback_model":"claude-sonnet-4-6","deterministic_first":False,"cache_ttl_seconds":0,"max_tokens":4096},
        {"task_type":"validation","default_model":"rule_engine","high_stakes_model":"claude-haiku-4-5","fallback_model":"claude-haiku-4-5","deterministic_first":True,"cache_ttl_seconds":86400,"max_tokens":1024},
        {"task_type":"delta_interpretation","default_model":"math_layer","high_stakes_model":"claude-haiku-4-5","fallback_model":"claude-haiku-4-5","deterministic_first":True,"cache_ttl_seconds":86400,"max_tokens":1024},
        {"task_type":"scout_synthesis","default_model":"claude-sonnet-4-6","high_stakes_model":"claude-sonnet-4-6","fallback_model":"claude-sonnet-4-6","deterministic_first":False,"cache_ttl_seconds":86400,"max_tokens":2048},
        {"task_type":"vision_assessment","default_model":"claude-sonnet-4-6","high_stakes_model":"claude-sonnet-4-6","fallback_model":"claude-sonnet-4-6","deterministic_first":False,"cache_ttl_seconds":86400,"max_tokens":2048},
        {"task_type":"output_validation","default_model":"rule_engine","high_stakes_model":"claude-haiku-4-5","fallback_model":"claude-haiku-4-5","deterministic_first":True,"cache_ttl_seconds":86400,"max_tokens":1024},
        {"task_type":"anomaly_interpretation","default_model":"claude-haiku-4-5","high_stakes_model":"claude-sonnet-4-6","fallback_model":"claude-sonnet-4-6","deterministic_first":False,"cache_ttl_seconds":86400,"max_tokens":1024}
    ],"per_system_allocation":{}}
    f = tmp_path / "routing_rules.json"
    f.write_text(json.dumps(config))
    s = MagicMock()
    s.routing_config_path = str(f)
    return RouterService(s)

@pytest.mark.parametrize("task_type,expected",[
    (TaskType.STRUCTURED_EXTRACTION,"claude-haiku-4-5"),(TaskType.TRAIT_MAPPING,"claude-sonnet-4-6"),
    (TaskType.SPECIFICATION_GENERATION,"claude-sonnet-4-6"),(TaskType.VALIDATION,"rule_engine"),
    (TaskType.DELTA_INTERPRETATION,"math_layer"),(TaskType.SCOUT_SYNTHESIS,"claude-sonnet-4-6"),
    (TaskType.VISION_ASSESSMENT,"claude-sonnet-4-6"),(TaskType.OUTPUT_VALIDATION,"rule_engine"),
    (TaskType.ANOMALY_INTERPRETATION,"claude-haiku-4-5")
])
def test_all_task_types_resolve(router_svc,task_type,expected):
    assert router_svc.resolve(task_type)["default_model"] == expected

def test_high_stakes_escalates(router_svc):
    assert router_svc.resolve(TaskType.SPECIFICATION_GENERATION,high_stakes=True)["default_model"] == "claude-opus-4-6"

def test_unknown_task_type_raises_422(router_svc):
    router_svc._rules.pop("structured_extraction",None)
    with pytest.raises(HTTPException) as e: router_svc.resolve(TaskType.STRUCTURED_EXTRACTION)
    assert e.value.status_code == 422

def test_all_nine_task_types_registered(router_svc):
    assert len(router_svc.all_task_types()) == 9
    for tt in TaskType: assert tt.value in router_svc.all_task_types()

def test_spec_gen_no_cache(router_svc):
    assert router_svc.resolve(TaskType.SPECIFICATION_GENERATION)["cache_ttl_seconds"] == 0

def test_validation_deterministic(router_svc):
    assert router_svc.resolve(TaskType.VALIDATION)["deterministic_first"] is True
