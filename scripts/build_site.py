#!/usr/bin/env python3
"""Build the public GitHub Pages catalog in _site using only the standard library."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from catalog import (CATEGORIES, MODELS, REMOVED, REPO_URL, ROOT, SITE_URL,
                     fmt_context, fmt_params, load_json, rank, write_text)
from generate_readme import render_csv

TITLE = "NVIDIA Model Rankings: Free NIM API Models by Size"
DESCRIPTION = (
    "Compare NVIDIA NIM API models by parameter count, context window and endpoint status. "
    "Find model IDs, cited sources, and free JSON and CSV downloads."
)


def anchor(label: str, url: str) -> str:
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def model_table(models: list[dict], caption: str, ranked: bool = False) -> str:
    headers = (["Rank"] if ranked else []) + [
        "Model / API ID", "Developer", "Total parameters", "Active parameters",
        "Architecture", "Context tokens", "Type", "Status", "Verified", "Sources",
    ]
    rows = []
    for position, model in enumerate(models, 1):
        cells = ([str(position)] if ranked else []) + [
            f'<strong>{escape(model["name"])}</strong><code>{escape(model["id"])}</code>',
            escape(model["developer"]), fmt_params(model["total_parameters"]),
            fmt_params(model["active_parameters"]), escape(model["architecture"]),
            fmt_context(model["context_length"]), escape(", ".join(model["model_type"]) or CATEGORIES[model["category"]]),
            escape(model["endpoint_status"] + (f' · {model["deprecation_date"]}' if model.get("deprecation_date") else "")),
            escape(model["last_verified"]),
            anchor("NVIDIA", model["nvidia_url"]) + (
                " · " + anchor("Parameters", model["parameter_source"]) if model.get("parameter_source") else ""
            ),
        ]
        rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    return (f'<div class="table-scroll" role="region" aria-label="{escape(caption)}" tabindex="0">'
            f'<table><caption>{escape(caption)}</caption><thead><tr>'
            + "".join(f'<th scope="col">{heading}</th>' for heading in headers)
            + "</tr></thead><tbody>" + "\n".join(rows) + "</tbody></table></div>")


def dataset_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "@id": SITE_URL + "#dataset",
        "name": "NVIDIA Model Rankings",
        "description": DESCRIPTION,
        "url": SITE_URL,
        "sameAs": REPO_URL,
        "license": REPO_URL + "/blob/main/LICENSE",
        "creator": {"@type": "Person", "name": "Yoosseph", "url": "https://github.com/Yoosseph"},
        "isAccessibleForFree": True,
        "keywords": ["NVIDIA NIM", "NVIDIA API models", "LLM parameter count", "model catalog", "context window"],
        "variableMeasured": ["Total parameters", "Active parameters", "Context length", "Endpoint status"],
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": media_type,
             "contentUrl": SITE_URL + "data/models." + extension}
            for extension, media_type in [("json", "application/json"), ("csv", "text/csv")]
        ],
    }


def render_page(models: list[dict], removed: list[dict]) -> str:
    active = rank([m for m in models if m["category"] == "llm" and m["endpoint_status"] == "Free Endpoint"])
    deprecated = rank([m for m in models if m["category"] == "llm" and m["endpoint_status"] == "Deprecated"])
    unlisted = rank([m for m in models if m["category"] == "llm" and m["endpoint_status"] == "Unlisted"])
    others = sorted([m for m in models if m["category"] != "llm"], key=lambda m: (m["category"], m["name"].lower()))
    dates = sorted({m["last_verified"] for m in models})
    verified = "–".join(dict.fromkeys([dates[0], dates[-1]])) if dates else "Not yet verified"
    known = [m for m in active if m["total_parameters"] is not None]
    largest = (f'{escape(known[0]["name"])} ({fmt_params(known[0]["total_parameters"])} total parameters)'
               if known else "No active model has a verified parameter count")
    removed_rows = "\n".join(
        f'<tr><td>{escape(m["name"])}</td><td><code>{escape(m["id"])}</code></td>'
        f'<td>{escape(m.get("deprecation_date") or "Not published")}</td>'
        f'<td>{escape(m["not_listed_since"])}</td></tr>' for m in removed
    )
    # Escape '<' so a future data field cannot terminate the JSON-LD script element.
    schema = json.dumps(dataset_schema(), ensure_ascii=False, indent=2).replace("<", "\\u003c")
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(TITLE)}</title>
  <meta name="description" content="{escape(DESCRIPTION)}">
  <link rel="canonical" href="{SITE_URL}">
  <meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="NVIDIA Model Rankings">
  <meta property="og:title" content="{escape(TITLE)}">
  <meta property="og:description" content="{escape(DESCRIPTION)}">
  <meta property="og:url" content="{SITE_URL}">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{escape(TITLE)}">
  <meta name="twitter:description" content="{escape(DESCRIPTION)}">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="assets/site.css">
  <link rel="sitemap" type="application/xml" href="{SITE_URL}sitemap.xml">
  <script type="application/ld+json">{schema}</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><a class="brand" href="{SITE_URL}">NVIDIA Model Rankings</a>
  <nav aria-label="Main navigation"><a href="#rankings">Rankings</a><a href="#dataset">Downloads</a>
  <a href="#methodology">Methodology</a><a href="{REPO_URL}">GitHub ↗</a></nav>
</header>
<main id="main">
  <section class="hero" aria-labelledby="title">
    <p class="eyebrow">Independent · Source-backed · Open data</p>
    <h1 id="title">NVIDIA NIM API models,<br>ranked by parameter count.</h1>
    <p class="intro">Compare models from <a href="https://build.nvidia.com/models">build.nvidia.com</a>
    by total and active parameters, context window and endpoint status. Find the API model ID and original sources for each entry.</p>
    <p class="actions"><a class="button" href="#rankings">Explore the rankings ↓</a><a href="#dataset">Get the dataset</a></p>
    <dl class="stats"><div><dt>Models in the snapshot</dt><dd>{len(models)}</dd></div>
    <div><dt>Active language &amp; vision models</dt><dd>{len(active)}</dd></div>
    <div><dt>Record verification dates</dt><dd class="date">{verified}</dd></div></dl>
    <p class="note">Free API access means NVIDIA's rate-limited trial for prototyping. Availability and quotas can change.
    Rankings measure model size, not accuracy, speed or coding performance.</p>
  </section>
  <section id="rankings" aria-labelledby="rankings-title">
    <p class="eyebrow">The catalog</p><h2 id="rankings-title">Free NVIDIA NIM API models by size</h2>
    <p>Largest active model with a disclosed count: <strong>{largest}</strong></p>
    <p>Ranked by total parameters, largest first; unknown counts are last. Active parameters describe the weights used per token.
    Context windows come from model cards and may exceed NVIDIA's hosted limit. Use your browser's Find command to locate a model or developer.</p>
    {model_table(active, "Active language and multimodal models", ranked=True)}
  </section>
  <section id="availability" aria-labelledby="availability-title">
    <h2 id="availability-title">Deprecated, unverified and removed models</h2>
    <p>Being listed by the API does not guarantee that an endpoint still answers. These entries are excluded from the active rankings.</p>
    <h3>Deprecated models still listed by the API</h3>
    <p>NVIDIA's page shows a past deprecation date or redirects to an unavailable or successor page. Calls may fail.</p>
    {model_table(deprecated, "Deprecated language and multimodal models")}
    <h3>Listed without a published model page</h3>
    <p>The API still lists these IDs, but a current NVIDIA model page or card could not be confirmed. Treat availability as unverified.</p>
    {model_table(unlisted, "Language and multimodal models with unverified availability")}
    <h3>Recently removed models</h3>
    <p>These IDs were absent from the API when checked. An unpublished deprecation date means the removal reason is not confirmed.</p>
    <div class="table-scroll" role="region" aria-label="Removed model history" tabindex="0"><table>
    <caption>Removed model history</caption><thead><tr><th scope="col">Model</th><th scope="col">Former API ID</th>
    <th scope="col">NVIDIA deprecation date</th><th scope="col">Absent when checked</th></tr></thead><tbody>{removed_rows}</tbody></table></div>
  </section>
  <section id="other-models" aria-labelledby="other-title">
    <h2 id="other-title">Embedding, safety and other models</h2>
    <p>These models are tracked separately because their sizes do not meaningfully compare with generative language models.</p>
    {model_table(others, "Non-LLM models and their endpoint status")}
  </section>
  <section id="dataset" aria-labelledby="dataset-title" class="panel">
    <p class="eyebrow">Open data</p><h2 id="dataset-title">Download NVIDIA Model Rankings</h2>
    <p>{escape(DESCRIPTION)} The JSON preserves exact integer counts, source URLs, notes and verification dates.
    CSV contains the same catalog for spreadsheets and analysis.</p>
    <ul><li><a href="data/models.json" download>Download model catalog as JSON</a></li>
    <li><a href="data/models.csv" download>Download model catalog as CSV</a></li>
    <li><a href="data/removed.json" download>Download removed model history as JSON</a></li></ul>
    <p>Maintained by <a href="https://github.com/Yoosseph">Yoosseph</a> and contributors.
    Dataset and scripts: <a href="{REPO_URL}/blob/main/LICENSE">MIT license</a>.
    <a href="{REPO_URL}/blob/main/CONTRIBUTING.md">Suggest a sourced correction</a>.</p>
  </section>
  <section id="methodology" aria-labelledby="methodology-title">
    <h2 id="methodology-title">How the rankings are verified</h2>
    <ul><li><strong>Availability:</strong> compare API IDs against
    <a href="https://integrate.api.nvidia.com/v1/models">NVIDIA's official model list</a>, then check NVIDIA pages for deprecations and redirects.
    Regional restrictions can make a page check inconclusive.</li>
    <li><strong>Parameters:</strong> prefer exact counts from official unquantized Hugging Face checkpoints, otherwise use figures stated by NVIDIA or the developer.
    Counts are never inferred from model names. Displayed counts are rounded to three significant figures; N/A means unknown.</li>
    <li><strong>Context:</strong> use the maximum documented token window. The hosted endpoint can have a shorter limit.</li>
    <li><strong>Freshness:</strong> updates are maintainer-reviewed, not scheduled. Every model has its own verification date.</li></ul>
    <p>Read the <a href="{REPO_URL}/blob/main/docs/methodology.md">full methodology</a> and
    <a href="{REPO_URL}/blob/main/docs/sources.md">source policy</a>.
    The site and README are generated from the same versioned dataset.</p>
  </section>
  <section id="faq" aria-labelledby="faq-title">
    <h2 id="faq-title">Frequently asked questions</h2>
    <h3>Is the NVIDIA NIM API free?</h3><p>A free NVIDIA Developer Program account provides trial access for prototyping.
    It is rate-limited, not unlimited production access. Check the current terms at <a href="https://build.nvidia.com/">NVIDIA's API catalog</a>.</p>
    <h3>Which is the largest NVIDIA API model?</h3><p>In this snapshot, the largest active model with a disclosed total parameter count is {largest}.
    See the per-model verification dates before relying on current availability.</p>
    <h3>Does a larger model perform better?</h3><p>Not necessarily. Model size is not a benchmark score.
    Evaluate quality, latency and context needs on your own workload.</p>
    <h3>What are total and active parameters?</h3><p>Total parameters count the complete model. Mixture-of-Experts models use only part of those weights for each token;
    that subset is reported as active parameters. The ranking uses the total.</p>
    <h3>Where can I find the API model ID?</h3><p>The ID appears beneath each model name and in the JSON and CSV downloads.
    Copy it exactly. The <a href="{REPO_URL}#quick-start-call-a-model-with-a-free-nvidia-api-key">GitHub quick start</a>
    shows how to call an endpoint.</p>
  </section>
</main>
<footer><p>NVIDIA Model Rankings is an independent community project, not affiliated with or endorsed by NVIDIA.
Model names and trademarks belong to their respective owners.</p>
<p><a href="{REPO_URL}">Source on GitHub</a> · <a href="sitemap.xml">Sitemap</a></p></footer>
</body>
</html>
'''


def outputs() -> dict[Path, str]:
    models, removed = load_json(MODELS), load_json(REMOVED)
    files = {
        Path("index.html"): render_page(models, removed),
        Path("sitemap.xml"): ('<?xml version="1.0" encoding="UTF-8"?>\n'
                              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                              f'<url><loc>{SITE_URL}</loc></url></urlset>\n'),
        Path("data/models.json"): MODELS.read_text(encoding="utf-8"),
        Path("data/models.csv"): render_csv(models),
        Path("data/removed.json"): REMOVED.read_text(encoding="utf-8"),
        Path(".nojekyll"): "",
        Path("404.html"): ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                           '<meta name="viewport" content="width=device-width, initial-scale=1">'
                           '<meta name="robots" content="noindex"><title>Page not found | NVIDIA Model Rankings</title>'
                           f'<link rel="stylesheet" href="{SITE_URL}assets/site.css"></head>'
                           f'<body><main><h1>Page not found</h1><p>{anchor("Browse NVIDIA model rankings", SITE_URL)}</p>'
                           '</main></body></html>\n'),
    }
    for asset in (ROOT / "site" / "assets").iterdir():
        if asset.is_file():
            files[Path("assets") / asset.name] = asset.read_text(encoding="utf-8")
    return files


def build(destination: Path = ROOT / "_site") -> None:
    for relative, text in outputs().items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        write_text(path, text)


if __name__ == "__main__":
    build()
    print("Built _site for GitHub Pages.")
