"""Model config templates (M-MU02).

Defines and manages LocalAI model configurations for current and
upgrade-candidate models. Each config maps to a YAML file that
LocalAI reads to load the model.

Design doc requirement:
> Create YAML configs for: Qwen3-8B, Phi-4-mini, Llama 3.3 8B, DeepSeek R1 8B.
> Template format compatible with LocalAI.
> Document chat templates and stop tokens per model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """LocalAI model configuration template."""

    name: str
    family: str                        # qwen, llama, phi, deepseek, hermes
    parameters_b: float                # Billion parameters
    quantization: str = "Q4_K_M"       # GGUF quantization level
    vram_gb: float = 0.0               # Estimated VRAM requirement
    context_size: int = 8192
    gpu_layers: int = 33               # Full GPU offload by default
    threads: int = 4
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop_tokens: list[str] = field(default_factory=list)
    chat_template: str = ""            # Chat message template
    chat_format: str = ""              # Chat wrapper template
    gguf_filename: str = ""            # Expected GGUF file
    capabilities: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.parameters_b}B, {self.quantization})"

    def to_yaml_dict(self) -> dict:
        """Convert to a dict suitable for YAML serialization as LocalAI config."""
        config: dict = {
            "name": self.name,
            "backend": "llama-cpp",
            "parameters": {
                "model": self.gguf_filename,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "context_size": self.context_size,
                "gpu_layers": self.gpu_layers,
                "threads": self.threads,
                "repeat_penalty": self.repeat_penalty,
            },
        }

        if self.stop_tokens:
            config["parameters"]["stop"] = self.stop_tokens

        if self.chat_template:
            config["template"] = {"chat_message": self.chat_template}
            if self.chat_format:
                config["template"]["chat"] = self.chat_format

        return config

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "family": self.family,
            "parameters_b": self.parameters_b,
            "quantization": self.quantization,
            "vram_gb": self.vram_gb,
            "context_size": self.context_size,
            "gpu_layers": self.gpu_layers,
            "gguf_filename": self.gguf_filename,
            "capabilities": self.capabilities,
            "stop_tokens": self.stop_tokens,
            "notes": self.notes,
        }


# ─── Model Config Registry ──────────────────────────────────────


# ChatML template used by Qwen, Hermes, and similar models
_CHATML_MESSAGE = """\
<|im_start|>{{.RoleName}}
{{.Content}}<|im_end|>"""

_CHATML_CHAT = """\
{{.Input}}
<|im_start|>assistant
"""

_CHATML_STOP = ["<|im_end|>", "<|endoftext|>"]

# Llama 3 template
_LLAMA3_MESSAGE = """\
<|start_header_id|>{{.RoleName}}<|end_header_id|>

{{.Content}}<|eot_id|>"""

_LLAMA3_CHAT = """\
{{.Input}}
<|start_header_id|>assistant<|end_header_id|>

"""

_LLAMA3_STOP = ["<|eot_id|>", "<|end_of_text|>"]


MODEL_CONFIGS: dict[str, ModelConfig] = {
    # ─── Current Models ──────────────────────────────────────────
    "hermes-3b": ModelConfig(
        name="hermes-3b",
        family="hermes",
        parameters_b=3.0,
        quantization="Q4_K_M",
        vram_gb=2.0,
        context_size=8192,
        gpu_layers=32,
        gguf_filename="hermes-3-llama-3.2-3b.Q4_K_M.gguf",
        stop_tokens=_CHATML_STOP,
        chat_template=_CHATML_MESSAGE,
        chat_format=_CHATML_CHAT,
        capabilities=["structured", "heartbeat"],
        notes="Current fleet default. 3B parameters, fast cold start (~10s).",
    ),
    "hermes": ModelConfig(
        name="hermes",
        family="hermes",
        parameters_b=7.0,
        quantization="Q4_K_M",
        vram_gb=4.4,
        context_size=8192,
        gpu_layers=24,
        gguf_filename="hermes-2-pro-mistral-7b.Q4_K_M.gguf",
        stop_tokens=_CHATML_STOP,
        chat_template=_CHATML_MESSAGE,
        chat_format=_CHATML_CHAT,
        capabilities=["structured", "reasoning", "code"],
        notes="7B reasoning model. Slow cold start (~80s).",
    ),

    # ─── Upgrade Candidates (M-MU02) ─────────────────────────────
    "qwen3-8b": ModelConfig(
        name="qwen3-8b",
        family="qwen",
        parameters_b=8.0,
        quantization="Q4_K_M",
        vram_gb=5.5,
        context_size=8192,
        gpu_layers=33,
        gguf_filename="qwen3-8b-q4_k_m.gguf",
        stop_tokens=_CHATML_STOP,
        chat_template=_CHATML_MESSAGE,
        chat_format=_CHATML_CHAT,
        capabilities=["structured", "reasoning", "code", "heartbeat"],
        notes=(
            "Primary upgrade candidate. 2.5x hermes-3b. "
            "ChatML format (same as hermes). Fits 8GB VRAM."
        ),
    ),
    "phi-4-mini": ModelConfig(
        name="phi-4-mini",
        family="phi",
        parameters_b=3.8,
        quantization="Q4_K_M",
        vram_gb=2.5,
        context_size=8192,  # Supports 128K but limited for CPU
        gpu_layers=0,       # CPU only — fallback model
        gguf_filename="phi-4-mini-q4_k_m.gguf",
        stop_tokens=["<|endoftext|>", "<|end|>"],
        chat_template="""\
<|user|>
{{.Content}}<|end|>""",
        chat_format="""\
{{.Input}}
<|assistant|>
""",
        capabilities=["structured", "code"],
        notes=(
            "CPU fallback upgrade. 128K context native. "
            "Replaces phi-2 as CPU fallback."
        ),
    ),
    "llama-3.3-8b": ModelConfig(
        name="llama-3.3-8b",
        family="llama",
        parameters_b=8.0,
        quantization="Q4_K_M",
        vram_gb=5.5,
        context_size=8192,
        gpu_layers=33,
        gguf_filename="llama-3.3-8b-instruct-q4_k_m.gguf",
        stop_tokens=_LLAMA3_STOP,
        chat_template=_LLAMA3_MESSAGE,
        chat_format=_LLAMA3_CHAT,
        capabilities=["structured", "reasoning", "code"],
        notes="Alternative to Qwen3-8B. Llama 3 instruction format.",
    ),
    "deepseek-r1-8b": ModelConfig(
        name="deepseek-r1-8b",
        family="deepseek",
        parameters_b=8.0,
        quantization="Q4_K_M",
        vram_gb=5.5,
        context_size=8192,
        gpu_layers=33,
        gguf_filename="deepseek-r1-distill-qwen-8b-q4_k_m.gguf",
        stop_tokens=_CHATML_STOP,
        chat_template=_CHATML_MESSAGE,
        chat_format=_CHATML_CHAT,
        capabilities=["reasoning", "code", "chain-of-thought"],
        notes=(
            "Chain-of-thought reasoning model. Distilled from DeepSeek R1. "
            "Good for adversarial challenge use — free local reasoning."
        ),
    ),
}


def get_model_config(name: str) -> Optional[ModelConfig]:
    """Get a model config by name."""
    return MODEL_CONFIGS.get(name)


def list_model_configs(gpu_only: bool = False) -> list[ModelConfig]:
    """List all model configs."""
    configs = list(MODEL_CONFIGS.values())
    if gpu_only:
        configs = [c for c in configs if c.gpu_layers > 0]
    return configs


def list_upgrade_candidates() -> list[ModelConfig]:
    """List models that are upgrade candidates (not currently deployed)."""
    current = {"hermes-3b", "hermes"}
    return [c for c in MODEL_CONFIGS.values() if c.name not in current]


def models_fitting_vram(vram_gb: float) -> list[ModelConfig]:
    """List models that fit in the given VRAM."""
    return [c for c in MODEL_CONFIGS.values() if c.vram_gb <= vram_gb and c.gpu_layers > 0]