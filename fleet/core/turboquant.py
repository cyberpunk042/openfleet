"""TurboQuant integration (M-MU06).

Configuration and monitoring for Google TurboQuant KV cache
compression when it lands in the llama.cpp/GGUF ecosystem.

Design doc requirement:
> Monitor llama.cpp for TurboQuant support.
> When available: rebuild model configs with extended context.
> Benchmark: context window vs quality vs VRAM.

Status: FUTURE — depends on llama.cpp ecosystem support.
This module defines the configuration schema and context extension
calculations. Actual integration will be implemented when GGUF
builds with TurboQuant support are available.
"""

from __future__ import annotations

from dataclasses import dataclass


# TurboQuant compresses KV caches to 3 bits — 6x memory reduction
KV_COMPRESSION_RATIO = 6.0


@dataclass
class TurboQuantConfig:
    """Configuration for TurboQuant-enabled model."""

    model_name: str
    base_context_size: int           # Original context window
    base_kv_cache_mb: float          # KV cache memory at base context
    turboquant_enabled: bool = False
    compression_ratio: float = KV_COMPRESSION_RATIO

    @property
    def extended_context_size(self) -> int:
        """Context size achievable with TurboQuant in same VRAM."""
        if not self.turboquant_enabled:
            return self.base_context_size
        return int(self.base_context_size * self.compression_ratio)

    @property
    def compressed_kv_cache_mb(self) -> float:
        """KV cache memory after TurboQuant compression."""
        if not self.turboquant_enabled:
            return self.base_kv_cache_mb
        return self.base_kv_cache_mb / self.compression_ratio

    @property
    def vram_saved_mb(self) -> float:
        return self.base_kv_cache_mb - self.compressed_kv_cache_mb

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "base_context_size": self.base_context_size,
            "extended_context_size": self.extended_context_size,
            "base_kv_cache_mb": round(self.base_kv_cache_mb, 1),
            "compressed_kv_cache_mb": round(self.compressed_kv_cache_mb, 1),
            "vram_saved_mb": round(self.vram_saved_mb, 1),
            "turboquant_enabled": self.turboquant_enabled,
        }


# Pre-computed estimates for fleet models
FLEET_TURBOQUANT_ESTIMATES: dict[str, TurboQuantConfig] = {
    "hermes-3b": TurboQuantConfig(
        model_name="hermes-3b",
        base_context_size=8192,
        base_kv_cache_mb=256,
    ),
    "qwen3-8b": TurboQuantConfig(
        model_name="qwen3-8b",
        base_context_size=8192,
        base_kv_cache_mb=512,
    ),
}