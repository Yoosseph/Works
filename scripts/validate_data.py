#!/usr/bin/env python3
"""Validate data/models.json and data/removed.json, and check that generated files are current."""
from __future__ import annotations

import sys
from datetime import date
from urllib.parse import urlparse

from catalog import ARCHITECTURES, CATEGORIES, CSV, MODELS, PARAMETER_BASES, README, REMOVED, STATUSES, load_json
from generate_readme import outputs

REQUIRED_STR = ("id", "name", "developer", "category", "architecture", "endpoint_status", "nvidia_url",
                "endpoint_source", "last_verified")
URL_FIELDS = ("nvidia_url", "parameter_source", "endpoint_source")


def is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def is_date(v) -> bool:
    try:
        date.fromisoformat(v)
        return True
    except (TypeError, ValueError):
        return False


def check_model(m: dict, errors: list[str]) -> None:
    label = m.get("id") or m.get("name") or "<unnamed>"
    err = lambda msg: errors.append(f"{label}: {msg}")
    for key in REQUIRED_STR:
        if not isinstance(m.get(key), str) or not m[key].strip():
            err(f"missing or empty {key}")
    if m.get("category") not in CATEGORIES:
        err(f"invalid category {m.get('category')!r}")
    if m.get("architecture") not in ARCHITECTURES:
        err(f"invalid architecture {m.get('architecture')!r}")
    if m.get("endpoint_status") not in STATUSES:
        err(f"invalid endpoint_status {m.get('endpoint_status')!r}")
    if not isinstance(m.get("free_endpoint"), bool):
        err("free_endpoint must be true or false")
    elif m["free_endpoint"] != (m.get("endpoint_status") == "Free Endpoint"):
        err("free_endpoint disagrees with endpoint_status")
    if m.get("endpoint_status") == "Deprecated" and not (m.get("deprecation_date") or "redirects" in (m.get("notes") or "")):
        err("Deprecated records need a deprecation_date or a redirect note")
    if m.get("deprecation_date") is not None and not is_date(m["deprecation_date"]):
        err("deprecation_date must be an ISO date or null")
    if not is_date(m.get("last_verified")):
        err("last_verified must be an ISO date")
    elif date.fromisoformat(m["last_verified"]) > date.today():
        err("last_verified is in the future")
    if not str(m.get("nvidia_url", "")).startswith("https://build.nvidia.com/"):
        err("nvidia_url must point at build.nvidia.com (the page slug may differ from the API id)")
    for key in URL_FIELDS:
        v = m.get(key)
        if v is None and key == "parameter_source" and m.get("total_parameters") is None:
            continue
        if not isinstance(v, str) or urlparse(v).scheme != "https" or not urlparse(v).netloc:
            err(f"{key} must be an https URL")
    total, active = m.get("total_parameters"), m.get("active_parameters")
    for key, v in (("total_parameters", total), ("active_parameters", active), ("context_length", m.get("context_length"))):
        if v is not None and (not is_int(v) or v <= 0):
            err(f"{key} must be a positive integer or null")
    if is_int(total) and is_int(active) and active > total:
        err("active_parameters exceeds total_parameters")
    if m.get("parameter_basis") not in PARAMETER_BASES:
        err(f"invalid parameter_basis {m.get('parameter_basis')!r}")
    if (total is None) != (m.get("parameter_basis") is None):
        err("parameter_basis must be set exactly when total_parameters is known")
    if m.get("architecture") == "MoE" and total is not None and active is None:
        err("MoE records with a total count must state active_parameters")
    if not isinstance(m.get("model_type"), list) or not all(isinstance(t, str) and t for t in m["model_type"]):
        err("model_type must be a list of strings")
    elif m.get("category") == "llm" and not m["model_type"]:
        err("LLM records need at least one model_type")
    if "notes" in m and (not isinstance(m["notes"], str) or not m["notes"].strip()):
        err("notes must be a non-empty string when present")


def main() -> int:
    errors: list[str] = []
    models, removed = load_json(MODELS), load_json(REMOVED)
    if not isinstance(models, list) or not isinstance(removed, list):
        print("ERROR: models.json and removed.json must contain arrays")
        return 1
    ids = [m.get("id") for m in models]
    for dup in sorted({i for i in ids if ids.count(i) > 1}, key=str):
        errors.append(f"duplicate id: {dup}")
    for m in models:
        check_model(m, errors)
    for r in removed:
        if not isinstance(r.get("id"), str) or not isinstance(r.get("name"), str):
            errors.append(f"removed record needs id and name: {r}")
        if r.get("id") in ids:
            errors.append(f"{r.get('id')}: listed in both models.json and removed.json")
        if not is_date(r.get("not_listed_since")) or (r.get("deprecation_date") is not None and not is_date(r["deprecation_date"])):
            errors.append(f"{r.get('id')}: invalid dates in removed.json")
    try:
        for path, text in outputs().items():
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                errors.append(f"{path.relative_to(README.parent)} is stale; run python scripts/generate_readme.py")
    except Exception as e:  # a crash in generation is itself a data error
        errors.append(f"README/CSV generation failed: {e!r}")
    if errors:
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1
    llms = sum(m["category"] == "llm" for m in models)
    print(f"Validated {len(models)} models ({llms} LLMs) and {len(removed)} removed records; {CSV.name} and README are current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
