"""Shared helpers for the NVIDIA Model Rankings scripts (standard library only)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "data" / "models.json"
REMOVED = ROOT / "data" / "removed.json"
CSV = ROOT / "data" / "models.csv"
README = ROOT / "README.md"
REPO = "Yoosseph/nvidia-model-rankings"
REPO_URL = f"https://github.com/{REPO}"
SITE_URL = "https://yoosseph.github.io/nvidia-model-rankings/"

API_MODELS_URL = "https://integrate.api.nvidia.com/v1/models"
API_CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
BUILD_URL = "https://build.nvidia.com"

CATEGORIES = {
    "llm": "Language & multimodal models",
    "safety": "Safety & guardrail models",
    "reward": "Reward models",
    "embedding": "Embedding & retrieval models",
    "document": "Document & chart parsing models",
    "detection": "Detection models",
}
# Free Endpoint: listed by /v1/models, has an NVIDIA model card, no past deprecation date.
# Deprecated:    listed by /v1/models, but the model page shows a past deprecation date or redirects away.
# Unlisted:      listed by /v1/models, but NVIDIA no longer publishes a model page or card for it.
STATUSES = {"Free Endpoint", "Deprecated", "Unlisted"}
ARCHITECTURES = {"Dense", "MoE", "Hybrid", "Unknown"}
PARAMETER_BASES = {"checkpoint", "stated", None}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def fmt_params(value: int | None) -> str:
    """Human-readable parameter count with three significant figures (e.g. 561B, 10.7B, 800M)."""
    if value is None:
        return "N/A"
    for suffix, unit in (("T", 10**12), ("B", 10**9), ("M", 10**6), ("K", 10**3)):
        if value >= unit:
            n = value / unit
            text = f"{n:.3g}" if n < 1000 else f"{n:.0f}"
            return f"{text}{suffix}"
    return str(value)


def fmt_context(value: int | None) -> str:
    """Context length in the conventional binary units (131072 -> 128K, 1048576 -> 1M)."""
    if value is None:
        return "N/A"
    if value % (1 << 20) == 0:
        return f"{value >> 20}M"
    if value % 1024 == 0:
        return f"{value >> 10}K"
    return f"{value / 1000:.3g}K" if value >= 1000 else str(value)


def rank(models: list[dict]) -> list[dict]:
    """Sort by total parameters (descending); unknown counts last; ties by name."""
    return sorted(models, key=lambda m: (m["total_parameters"] is None, -(m["total_parameters"] or 0), m["name"].lower()))
