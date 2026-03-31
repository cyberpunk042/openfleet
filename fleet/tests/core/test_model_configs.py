"""Tests for model config templates (M-MU02)."""

from fleet.core.model_configs import (
    MODEL_CONFIGS,
    ModelConfig,
    get_model_config,
    list_model_configs,
    list_upgrade_candidates,
    models_fitting_vram,
)


# ─── ModelConfig Dataclass ─────────────────────────────────────


def test_model_config_display_name():
    cfg = ModelConfig(name="test", family="test", parameters_b=3.0)
    assert cfg.display_name == "test (3.0B, Q4_K_M)"


def test_model_config_defaults():
    cfg = ModelConfig(name="test", family="test", parameters_b=1.0)
    assert cfg.quantization == "Q4_K_M"
    assert cfg.context_size == 8192
    assert cfg.temperature == 0.2
    assert cfg.top_p == 0.9
    assert cfg.gpu_layers == 33
    assert cfg.stop_tokens == []
    assert cfg.capabilities == []


# ─── to_yaml_dict ──────────────────────────────────────────────


def test_to_yaml_dict_basic():
    cfg = ModelConfig(
        name="test-model", family="test", parameters_b=3.0,
        gguf_filename="test.gguf",
    )
    d = cfg.to_yaml_dict()
    assert d["name"] == "test-model"
    assert d["backend"] == "llama-cpp"
    assert d["parameters"]["model"] == "test.gguf"
    assert d["parameters"]["temperature"] == 0.2
    assert d["parameters"]["context_size"] == 8192


def test_to_yaml_dict_with_stop_tokens():
    cfg = ModelConfig(
        name="test", family="test", parameters_b=3.0,
        stop_tokens=["<|end|>", "<|stop|>"],
    )
    d = cfg.to_yaml_dict()
    assert d["parameters"]["stop"] == ["<|end|>", "<|stop|>"]


def test_to_yaml_dict_without_stop_tokens():
    cfg = ModelConfig(name="test", family="test", parameters_b=3.0)
    d = cfg.to_yaml_dict()
    assert "stop" not in d["parameters"]


def test_to_yaml_dict_with_chat_template():
    cfg = ModelConfig(
        name="test", family="test", parameters_b=3.0,
        chat_template="<|im_start|>{{.RoleName}}\n{{.Content}}<|im_end|>",
        chat_format="{{.Input}}\n<|im_start|>assistant\n",
    )
    d = cfg.to_yaml_dict()
    assert "template" in d
    assert "chat_message" in d["template"]
    assert "chat" in d["template"]


def test_to_yaml_dict_without_chat_template():
    cfg = ModelConfig(name="test", family="test", parameters_b=3.0)
    d = cfg.to_yaml_dict()
    assert "template" not in d


def test_to_yaml_dict_chat_template_no_format():
    cfg = ModelConfig(
        name="test", family="test", parameters_b=3.0,
        chat_template="<|im_start|>{{.RoleName}}\n{{.Content}}<|im_end|>",
    )
    d = cfg.to_yaml_dict()
    assert "template" in d
    assert "chat_message" in d["template"]
    assert "chat" not in d["template"]


# ─── to_dict ───────────────────────────────────────────────────


def test_to_dict():
    cfg = ModelConfig(
        name="hermes-3b", family="hermes", parameters_b=3.0,
        vram_gb=2.0, gguf_filename="hermes.gguf",
        capabilities=["structured"], stop_tokens=["<|end|>"],
        notes="Test note.",
    )
    d = cfg.to_dict()
    assert d["name"] == "hermes-3b"
    assert d["family"] == "hermes"
    assert d["parameters_b"] == 3.0
    assert d["vram_gb"] == 2.0
    assert d["capabilities"] == ["structured"]
    assert d["notes"] == "Test note."


# ─── Registry ─────────────────────────────────────────────────


def test_registry_has_current_models():
    assert "hermes-3b" in MODEL_CONFIGS
    assert "hermes" in MODEL_CONFIGS


def test_registry_has_upgrade_candidates():
    assert "qwen3-8b" in MODEL_CONFIGS
    assert "phi-4-mini" in MODEL_CONFIGS
    assert "llama-3.3-8b" in MODEL_CONFIGS
    assert "deepseek-r1-8b" in MODEL_CONFIGS


def test_registry_minimum_count():
    assert len(MODEL_CONFIGS) >= 6


def test_hermes_3b_config():
    cfg = MODEL_CONFIGS["hermes-3b"]
    assert cfg.family == "hermes"
    assert cfg.parameters_b == 3.0
    assert cfg.gpu_layers > 0
    assert "heartbeat" in cfg.capabilities


def test_qwen3_8b_config():
    cfg = MODEL_CONFIGS["qwen3-8b"]
    assert cfg.family == "qwen"
    assert cfg.parameters_b == 8.0
    assert cfg.vram_gb <= 8.0  # Must fit 8GB VRAM
    assert "reasoning" in cfg.capabilities
    assert cfg.gpu_layers > 0


def test_phi_4_mini_cpu_only():
    cfg = MODEL_CONFIGS["phi-4-mini"]
    assert cfg.gpu_layers == 0  # CPU fallback
    assert cfg.family == "phi"


def test_deepseek_r1_has_cot():
    cfg = MODEL_CONFIGS["deepseek-r1-8b"]
    assert "chain-of-thought" in cfg.capabilities


def test_all_configs_have_gguf():
    for name, cfg in MODEL_CONFIGS.items():
        assert cfg.gguf_filename, f"{name} missing gguf_filename"
        assert cfg.gguf_filename.endswith(".gguf"), f"{name} gguf not .gguf"


def test_all_configs_have_stop_tokens():
    for name, cfg in MODEL_CONFIGS.items():
        assert len(cfg.stop_tokens) > 0, f"{name} has no stop tokens"


def test_all_configs_have_chat_template():
    for name, cfg in MODEL_CONFIGS.items():
        assert cfg.chat_template, f"{name} missing chat_template"


# ─── Lookup Functions ──────────────────────────────────────────


def test_get_model_config_exists():
    cfg = get_model_config("hermes-3b")
    assert cfg is not None
    assert cfg.name == "hermes-3b"


def test_get_model_config_missing():
    assert get_model_config("nonexistent") is None


def test_list_model_configs_all():
    configs = list_model_configs()
    assert len(configs) >= 6


def test_list_model_configs_gpu_only():
    configs = list_model_configs(gpu_only=True)
    for cfg in configs:
        assert cfg.gpu_layers > 0
    # phi-4-mini should be excluded
    names = [c.name for c in configs]
    assert "phi-4-mini" not in names


def test_list_upgrade_candidates():
    candidates = list_upgrade_candidates()
    names = [c.name for c in candidates]
    assert "hermes-3b" not in names
    assert "hermes" not in names
    assert "qwen3-8b" in names
    assert "phi-4-mini" in names


def test_models_fitting_vram_8gb():
    fits = models_fitting_vram(8.0)
    names = [c.name for c in fits]
    assert "hermes-3b" in names  # 2.0 GB
    assert "qwen3-8b" in names  # 5.5 GB


def test_models_fitting_vram_3gb():
    fits = models_fitting_vram(3.0)
    names = [c.name for c in fits]
    assert "hermes-3b" in names  # 2.0 GB
    # 8B models should NOT fit
    assert "qwen3-8b" not in names
    assert "llama-3.3-8b" not in names


def test_models_fitting_vram_excludes_cpu():
    fits = models_fitting_vram(10.0)
    names = [c.name for c in fits]
    # phi-4-mini has 0 gpu_layers, should be excluded
    assert "phi-4-mini" not in names


# ─── YAML Serialization Roundtrip ─────────────────────────────


def test_yaml_dict_has_required_localai_fields():
    for name, cfg in MODEL_CONFIGS.items():
        d = cfg.to_yaml_dict()
        assert "name" in d, f"{name} yaml missing name"
        assert "backend" in d, f"{name} yaml missing backend"
        assert "parameters" in d, f"{name} yaml missing parameters"
        assert "model" in d["parameters"], f"{name} yaml missing model path"