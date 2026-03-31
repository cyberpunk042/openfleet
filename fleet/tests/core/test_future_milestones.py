"""Tests for FUTURE milestones (M-MU05, M-MU06, M-MU08, M-BR08).

These milestones depend on hardware/ecosystem availability.
Tests cover configuration schemas and calculation logic only.
"""

from fleet.core.cluster_peering import ClusterNode, ClusterPeeringConfig
from fleet.core.dual_gpu import DualGPUConfig, GPUSlot
from fleet.core.router_unification import UnifiedRoutingRequest, UnifiedRoutingResult
from fleet.core.turboquant import (
    FLEET_TURBOQUANT_ESTIMATES,
    KV_COMPRESSION_RATIO,
    TurboQuantConfig,
)


# ─── M-MU05: Dual-GPU Configuration ──────────────────────────


def test_gpu_slot_defaults():
    g = GPUSlot(gpu_id=0, vram_mb=8192)
    assert g.vram_free_mb == 8192
    assert g.utilization_pct == 0.0


def test_gpu_slot_utilization():
    g = GPUSlot(gpu_id=0, vram_mb=8192, vram_used_mb=4096)
    assert abs(g.utilization_pct - 50.0) < 0.1


def test_gpu_slot_can_fit():
    g = GPUSlot(gpu_id=0, vram_mb=8192, vram_used_mb=2048)
    assert g.can_fit(5000)
    assert not g.can_fit(7000)


def test_dual_gpu_config_defaults():
    cfg = DualGPUConfig()
    assert cfg.gpu_0.vram_mb == 8192
    assert cfg.gpu_1.vram_mb == 11264
    assert cfg.default_model == "qwen3-8b"


def test_dual_gpu_best_gpu_default_model():
    cfg = DualGPUConfig()
    assert cfg.best_gpu_for_model("qwen3-8b", 5500) == 0


def test_dual_gpu_best_gpu_specialist():
    cfg = DualGPUConfig()
    assert cfg.best_gpu_for_model("phi-4", 8000) == 1


def test_dual_gpu_needs_swap():
    cfg = DualGPUConfig()
    cfg.gpu_0.model_loaded = "qwen3-8b"
    assert not cfg.needs_swap("qwen3-8b")
    assert cfg.needs_swap("phi-4")


def test_dual_gpu_no_swap_either_gpu():
    cfg = DualGPUConfig()
    cfg.gpu_0.model_loaded = "qwen3-8b"
    cfg.gpu_1.model_loaded = "phi-4"
    assert not cfg.needs_swap("qwen3-8b")
    assert not cfg.needs_swap("phi-4")


def test_dual_gpu_to_dict():
    cfg = DualGPUConfig()
    d = cfg.to_dict()
    assert "gpu_0" in d
    assert "gpu_1" in d
    assert d["default_model"] == "qwen3-8b"


# ─── M-MU06: TurboQuant Integration ──────────────────────────


def test_turboquant_disabled():
    cfg = TurboQuantConfig(
        model_name="hermes-3b", base_context_size=8192,
        base_kv_cache_mb=256,
    )
    assert cfg.extended_context_size == 8192
    assert cfg.compressed_kv_cache_mb == 256
    assert cfg.vram_saved_mb == 0.0


def test_turboquant_enabled():
    cfg = TurboQuantConfig(
        model_name="hermes-3b", base_context_size=8192,
        base_kv_cache_mb=256, turboquant_enabled=True,
    )
    assert cfg.extended_context_size == int(8192 * KV_COMPRESSION_RATIO)
    assert cfg.compressed_kv_cache_mb < 256
    assert cfg.vram_saved_mb > 0


def test_turboquant_compression_ratio():
    assert KV_COMPRESSION_RATIO == 6.0


def test_turboquant_fleet_estimates():
    assert "hermes-3b" in FLEET_TURBOQUANT_ESTIMATES
    assert "qwen3-8b" in FLEET_TURBOQUANT_ESTIMATES


def test_turboquant_to_dict():
    cfg = TurboQuantConfig(
        model_name="qwen3-8b", base_context_size=8192,
        base_kv_cache_mb=512, turboquant_enabled=True,
    )
    d = cfg.to_dict()
    assert d["turboquant_enabled"] is True
    assert d["extended_context_size"] > 8192
    assert d["vram_saved_mb"] > 0


# ─── M-MU08: Cluster Peering ──────────────────────────────────


def test_cluster_node():
    n = ClusterNode(
        node_id="alpha", hostname="machine-1",
        localai_url="http://192.168.1.10:8090/v1",
        models_available=["qwen3-8b", "hermes-3b"],
        model_loaded="qwen3-8b", healthy=True,
    )
    assert n.healthy
    d = n.to_dict()
    assert d["node_id"] == "alpha"


def test_cluster_peering_healthy_nodes():
    cfg = ClusterPeeringConfig(nodes=[
        ClusterNode(node_id="a", hostname="m1", localai_url="http://m1:8090/v1", healthy=True),
        ClusterNode(node_id="b", hostname="m2", localai_url="http://m2:8090/v1", healthy=False),
    ])
    assert len(cfg.healthy_nodes()) == 1


def test_cluster_peering_node_with_model():
    cfg = ClusterPeeringConfig(nodes=[
        ClusterNode(
            node_id="a", hostname="m1", localai_url="http://m1:8090/v1",
            model_loaded="qwen3-8b", healthy=True,
        ),
        ClusterNode(
            node_id="b", hostname="m2", localai_url="http://m2:8090/v1",
            model_loaded="hermes-3b", healthy=True,
        ),
    ])
    node = cfg.node_with_model("qwen3-8b")
    assert node is not None
    assert node.node_id == "a"
    assert cfg.node_with_model("phi-4") is None


def test_cluster_peering_node_that_can_load():
    cfg = ClusterPeeringConfig(nodes=[
        ClusterNode(
            node_id="a", hostname="m1", localai_url="http://m1:8090/v1",
            models_available=["qwen3-8b"], model_loaded="hermes-3b", healthy=True,
        ),
    ])
    node = cfg.node_that_can_load("qwen3-8b")
    assert node is not None
    assert cfg.node_that_can_load("phi-4") is None


def test_cluster_peering_to_dict():
    cfg = ClusterPeeringConfig(nodes=[
        ClusterNode(node_id="a", hostname="m1", localai_url="http://m1:8090/v1", healthy=True),
    ])
    d = cfg.to_dict()
    assert d["healthy_count"] == 1
    assert len(d["nodes"]) == 1


# ─── M-BR08: AICP Router Unification ──────────────────────────


def test_unified_request():
    r = UnifiedRoutingRequest(
        source="fleet", task_type="heartbeat",
        complexity="low", budget_mode="economic",
    )
    d = r.to_dict()
    assert d["source"] == "fleet"
    assert d["budget_mode"] == "economic"


def test_unified_result():
    r = UnifiedRoutingResult(
        backend="localai", model="qwen3-8b",
        confidence_tier="trainee",
        fallback_chain=["openrouter-free", "claude-code"],
        reason="cheapest capable backend",
    )
    d = r.to_dict()
    assert d["backend"] == "localai"
    assert len(d["fallback_chain"]) == 2