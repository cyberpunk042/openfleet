"""Dual-GPU configuration (M-MU05).

Configuration structures for running two GPU models simultaneously
when 19GB VRAM (8GB + 11GB) is available.

Design doc requirement:
> LocalAI config for two GPU backends.
> GPU assignment per model.
> Router knows which GPU has which model.
> No-swap routing for common cases.

Status: FUTURE — depends on second GPU hardware.
This module defines the configuration schema. Actual GPU management
will be implemented when hardware is available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GPUSlot:
    """A GPU slot that can host one model."""

    gpu_id: int                    # 0 = first GPU, 1 = second GPU
    vram_mb: int                   # Total VRAM in MB
    model_loaded: str = ""         # Currently loaded model name
    vram_used_mb: int = 0
    always_loaded: bool = False    # If True, model stays resident

    @property
    def vram_free_mb(self) -> int:
        return max(self.vram_mb - self.vram_used_mb, 0)

    @property
    def utilization_pct(self) -> float:
        if not self.vram_mb:
            return 0.0
        return (self.vram_used_mb / self.vram_mb) * 100

    def can_fit(self, model_vram_mb: int) -> bool:
        return model_vram_mb <= self.vram_free_mb

    def to_dict(self) -> dict:
        return {
            "gpu_id": self.gpu_id,
            "vram_mb": self.vram_mb,
            "vram_free_mb": self.vram_free_mb,
            "model_loaded": self.model_loaded,
            "utilization_pct": round(self.utilization_pct, 1),
            "always_loaded": self.always_loaded,
        }


@dataclass
class DualGPUConfig:
    """Configuration for dual-GPU LocalAI setup.

    GPU 0 (8GB):  Fleet default model — always loaded
    GPU 1 (11GB): Specialist model — loaded on demand
    """

    gpu_0: GPUSlot = field(
        default_factory=lambda: GPUSlot(gpu_id=0, vram_mb=8192),
    )
    gpu_1: GPUSlot = field(
        default_factory=lambda: GPUSlot(gpu_id=1, vram_mb=11264),
    )
    default_model: str = "qwen3-8b"
    specialist_models: list[str] = field(
        default_factory=lambda: ["phi-4", "deepseek-r1-8b"],
    )

    def best_gpu_for_model(self, model: str, model_vram_mb: int) -> Optional[int]:
        """Which GPU should host this model?

        Default model always goes to GPU 0.
        Specialist models go to GPU 1.
        Returns None if neither GPU can fit the model.
        """
        if model == self.default_model:
            return 0 if self.gpu_0.can_fit(model_vram_mb) else None
        if self.gpu_1.can_fit(model_vram_mb):
            return 1
        if self.gpu_0.can_fit(model_vram_mb):
            return 0
        return None

    def needs_swap(self, model: str) -> bool:
        """Does loading this model require a swap?

        No swap needed if the model is already loaded on either GPU.
        """
        if self.gpu_0.model_loaded == model:
            return False
        if self.gpu_1.model_loaded == model:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "gpu_0": self.gpu_0.to_dict(),
            "gpu_1": self.gpu_1.to_dict(),
            "default_model": self.default_model,
            "specialist_models": self.specialist_models,
        }