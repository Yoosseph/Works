#!/usr/bin/env python3
"""Conservative update helper. NVIDIA discovery is intentionally manual: review sources before editing JSON."""
from pathlib import Path
print("Automatic discovery is intentionally disabled.")
print("Review NVIDIA model pages and official parameter sources, then update data/models.json manually.")
print(f"Dataset: {Path(__file__).resolve().parents[1] / 'data/models.json'}")
