#!/usr/bin/env python3
"""Validate model records and ensure README is generated from current data."""
import json, re, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"Free Endpoint", "Hosted Endpoint", "Download Available", "Partner Endpoint", "Unknown"}
ARCH = {"Dense", "MoE", "Hybrid", "Unknown"}
def fail(msg): print(f"ERROR: {msg}"); return 1
def main():
    data = json.loads((ROOT/"data/models.json").read_text()); errors=[]; names=set()
    if not isinstance(data,list): return fail("models.json must contain an array")
    for i,m in enumerate(data):
        for key in ("name","developer","nvidia_url","architecture","endpoint_status","parameter_source","endpoint_source","last_verified"):
            if not isinstance(m.get(key),str) or not m[key]: errors.append(f"record {i}: missing {key}")
        if m.get("name") in names: errors.append(f"duplicate model: {m.get('name')}")
        names.add(m.get("name"))
        if m.get("architecture") not in ARCH: errors.append(f"{m.get('name')}: invalid architecture")
        if m.get("endpoint_status") not in STATUSES: errors.append(f"{m.get('name')}: invalid endpoint status")
        for key in ("nvidia_url","parameter_source","endpoint_source"):
            if urlparse(m.get(key,"{}")).scheme not in ("http","https"): errors.append(f"{m.get('name')}: invalid URL {key}")
        total, active = m.get("total_parameters"), m.get("active_parameters")
        if total is not None and (not isinstance(total,int) or total < 0): errors.append(f"{m.get('name')}: invalid total")
        if active is not None and (not isinstance(active,int) or active < 0): errors.append(f"{m.get('name')}: invalid active")
        if active is not None and total is not None and active > total: errors.append(f"{m.get('name')}: active exceeds total")
        try: date.fromisoformat(m.get("last_verified",""))
        except ValueError: errors.append(f"{m.get('name')}: invalid last_verified")
        if bool(m.get("free_endpoint")) != (m.get("endpoint_status") == "Free Endpoint"): errors.append(f"{m.get('name')}: free_endpoint/status mismatch")
    if errors:
        print("\n".join(errors)); return 1
    print(f"Validated {len(data)} model records.")
    return 0
if __name__ == "__main__": sys.exit(main())
