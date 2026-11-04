#!/usr/bin/env python3
"""Compare the catalog with the live NVIDIA API and report (or apply) availability changes.

Usage:
    python scripts/update_models.py               # report drift
    python scripts/update_models.py --check       # report drift, exit 1 if any
    python scripts/update_models.py --apply       # also write status changes and removals to data/
    python scripts/update_models.py --probe       # also send a 1-token request to each active LLM
                                                  # (needs NVIDIA_API_KEY; uses your rate limit)

What it does:
  1. Fetches https://integrate.api.nvidia.com/v1/models (no key needed).
  2. Reports model IDs that are new upstream or have disappeared.
  3. Reads each model's build.nvidia.com page for deprecation dates and redirects.
  4. For new IDs, fetches the NVIDIA markdown model card (https://build.nvidia.com/<id>.md) and
     prints the stated parameter counts and context, for a human to verify and add.

--apply only changes availability fields (endpoint_status, free_endpoint, deprecation_date,
last_verified, redirect notes) and moves vanished IDs to data/removed.json. It never writes
parameter counts: those need a cited source and human review (see CONTRIBUTING.md).
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from catalog import API_CHAT_URL, API_MODELS_URL, BUILD_URL, MODELS, REMOVED, load_json, write_text

UA = {"User-Agent": "Mozilla/5.0 (compatible; nvidia-model-rankings-check)"}
TODAY = date.today().isoformat()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def http_get(url: str, headers: dict | None = None, follow: bool = True, timeout: int = 40):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    try:
        resp = (urllib.request.urlopen if follow else _opener.open)(req, timeout=timeout)
        return resp.status, resp.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as e:
        return e.code, "", e.headers.get("Location")


def api_ids() -> set[str]:
    status, body, _ = http_get(API_MODELS_URL)
    if status != 200:
        raise SystemExit(f"Could not fetch {API_MODELS_URL} (HTTP {status})")
    return {m["id"] for m in json.loads(body)["data"]}


def find_card(model_id: str, hint: str | None = None) -> tuple[str | None, str]:
    """Locate NVIDIA's markdown model card. Page slugs often differ from API ids (3.1 -> 3_1 or 3-1)."""
    candidates = [hint, model_id, model_id.replace(".", "_"), model_id.replace(".", "-")]
    for slug in dict.fromkeys(c for c in candidates if c):
        code, text, _ = http_get(f"{BUILD_URL}/{slug}.md")
        if code == 200 and text.startswith("---"):
            return slug, text
    return None, ""


def page_status(model_id: str, hint: str | None = None) -> dict:
    """Availability evidence: card presence, redirects and deprecation dates from the model page.

    A build.nvidia.com URL with no model behind it still returns HTTP 200 with a generic page, so
    the markdown card, not the HTTP status, is what proves that a model page exists.
    """
    slug, _ = find_card(model_id, hint)
    code, html, location = http_get(f"{BUILD_URL}/{slug or model_id}", follow=False)
    if code in (301, 302, 307, 308):
        target = location if (location or "").startswith("http") else f"{BUILD_URL}{location}"
        if target.rstrip("/").endswith("/experience-unavailable"):
            # Region-gated page (e.g. Meta multimodal models outside the US), not a deprecation.
            # Run this check from an unrestricted region; CI on GitHub-hosted runners is the reference.
            return {"slug": slug, "error": "page is region-restricted from this network"}
        return {"slug": slug, "redirect": target}
    if code != 200:
        return {"slug": slug, "error": f"HTTP {code}"}
    m = re.search(r"DEPRECATION\W+value\W+(\d{2})/(\d{2})/(\d{4})", html)
    return {"slug": slug, "deprecation_date": f"{m[3]}-{m[1]}-{m[2]}" if m else None}


def classify(st: dict) -> str:
    dep = st.get("deprecation_date")
    if st.get("redirect") or (dep is not None and dep <= TODAY):
        return "Deprecated"
    return "Free Endpoint" if st.get("slug") else "Unlisted"


def card_facts(model_id: str) -> dict:
    """Stated facts from NVIDIA's markdown model card, for human review."""
    slug, text = find_card(model_id)
    if not slug:
        return {"card": None}
    grab = lambda pat: (re.search(pat, text, re.I | re.M) or [None, None])[1]
    return {
        "card": f"{BUILD_URL}/{slug}.md",
        "description": grab(r'^description: "?(.*?)"?$'),
        "total": grab(r"\*\*(?:Total Parameters|Number of model parameters|Model Parameters)[^*]*:\*\*\s*(.+)"),
        "active": grab(r"\*\*Active Parameters[^*]*:\*\*\s*(.+)"),
        "hugging_face": grab(r"(https://huggingface\.co/[\w.-]+/[\w.-]+)"),
    }


def probe(model_id: str, key: str) -> str:
    body = json.dumps({"model": model_id, "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}).encode()
    req = urllib.request.Request(API_CHAT_URL, data=body, headers={**UA, "Authorization": f"Bearer {key}",
                                                                 "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=60)
        return "ok"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return type(e).__name__


def main(argv: list[str]) -> int:
    check, apply, do_probe = "--check" in argv, "--apply" in argv, "--probe" in argv
    models, removed = load_json(MODELS), load_json(REMOVED)
    by_id = {m["id"]: m for m in models}
    live = api_ids()
    new, gone = sorted(live - by_id.keys()), sorted(by_id.keys() - live)
    drift = bool(new or gone)

    print(f"NVIDIA API lists {len(live)} models; catalog has {len(models)}.")
    known = sorted(live & by_id.keys())
    hint = lambda mid: by_id[mid]["nvidia_url"].removeprefix(f"{BUILD_URL}/")
    with ThreadPoolExecutor(8) as ex:
        pages = dict(zip(known, ex.map(lambda mid: page_status(mid, hint(mid)), known)))
        cards = dict(zip(new, ex.map(card_facts, new)))

    changes = []
    for mid, st in pages.items():
        m = by_id[mid]
        if "error" in st:
            print(f"  ? {mid}: page check failed ({st['error']})")
            continue
        dep, want = st.get("deprecation_date"), classify(st)
        if want != m["endpoint_status"] or dep != m.get("deprecation_date"):
            changes.append((m, want, dep, st))
        elif dep and dep > TODAY:
            print(f"  ! {mid}: deprecation scheduled for {dep}")

    for m, want, dep, st in changes:
        print(f"  ~ {m['id']}: {m['endpoint_status']} -> {want}" + (f" (deprecation {dep})" if dep else "")
              + (f" (redirects to {st['redirect']})" if st.get("redirect") else ""))
    for mid in gone:
        print(f"  - {mid}: no longer listed by the API")
    for mid in new:
        c = cards[mid]
        print(f"  + {mid}: NEW. Card: {c.get('card') or 'not found'}")
        for k in ("description", "total", "active", "hugging_face"):
            if c.get(k):
                print(f"      {k}: {c[k].strip()[:160]}")
    drift = drift or bool(changes)

    if do_probe:
        key = os.environ.get("NVIDIA_API_KEY")
        if not key:
            print("--probe needs NVIDIA_API_KEY in the environment.")
            return 2
        targets = [m["id"] for m in models if m["category"] == "llm" and m["id"] in live]
        with ThreadPoolExecutor(4) as ex:
            for mid, res in zip(targets, ex.map(lambda i: probe(i, key), targets)):
                if res != "ok":
                    print(f"  x {mid}: probe {res} (catalog status: {by_id[mid]['endpoint_status']})")
        print(f"Probed {len(targets)} LLM endpoints.")

    if apply:
        for m, want, dep, st in changes:
            m.update(endpoint_status=want, free_endpoint=want == "Free Endpoint", deprecation_date=dep)
            if st.get("slug"):
                m["nvidia_url"] = f"{BUILD_URL}/{st['slug']}"
            redirect = st.get("redirect")
            if redirect and redirect not in (m.get("notes") or ""):
                m["notes"] = ((m.get("notes") or "") + f" Catalog page now redirects to {redirect}.").strip()
        for m in models:
            if m["id"] in live and m["id"] in pages and "error" not in pages[m["id"]]:
                m["last_verified"] = TODAY
        for mid in gone:
            m = by_id[mid]
            removed.insert(0, {"id": mid, "name": m["name"], "deprecation_date": m.get("deprecation_date"), "not_listed_since": TODAY})
        models = [m for m in models if m["id"] not in gone]
        write_text(MODELS, json.dumps(models, indent=2, ensure_ascii=False) + "\n")
        write_text(REMOVED, json.dumps(removed, indent=2, ensure_ascii=False) + "\n")
        print("Applied availability changes. New models must be added by hand; then run generate_readme.py and validate_data.py.")

    if not drift:
        print("Catalog matches the live NVIDIA API.")
    return 1 if (check and drift) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
