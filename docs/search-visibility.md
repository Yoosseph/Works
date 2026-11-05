# Search visibility and publishing

The repository and public catalog serve different reading needs:

- [GitHub repository](https://github.com/Yoosseph/nvidia-model-rankings): source data, API examples, contribution history and methodology.
- [Public model catalog](https://yoosseph.github.io/nvidia-model-rankings/): a static, mobile-friendly comparison table and downloadable dataset.

Both are generated from `data/models.json`. Update facts there, regenerate the README, then validate. Do not add unsupported claims, keyword lists or artificial verification dates to attract search traffic.

## Build and check

```bash
python scripts/generate_readme.py
python scripts/validate_data.py
python -m unittest discover -s tests
python scripts/build_site.py
python -m http.server 8000 --directory _site
```

Open `http://localhost:8000/` to preview. `_site/` is a generated artifact and is not committed. The builder uses only Python's standard library; it publishes the catalog, download files and assets, not the rest of the repository.

## GitHub Pages

In repository **Settings → Pages → Build and deployment**, select **GitHub Actions**. The `Publish model rankings` workflow validates and builds on changes to the relevant files on `main`, then deploys the artifact. It can also be run manually from `main`. Pull requests build and test without publishing. There is no scheduled catalog refresh.

The production URL lives in `scripts/catalog.py` as `SITE_URL`. If the repository is moved or a custom domain is configured, update it before deploying so canonical URLs, social metadata, dataset download URLs and the sitemap agree.

## Search metadata

The page includes a descriptive title and description, a self-referencing canonical URL, Open Graph and Twitter summary metadata, semantic headings and a `Dataset` JSON-LD object with creator, license and download formats. Every model is present in the initial HTML; no JavaScript or API call is needed to read the catalog. The generated 404 page uses `noindex`.

The [sitemap](https://yoosseph.github.io/nvidia-model-rankings/sitemap.xml) lists the canonical catalog page. It omits `lastmod` rather than pretending a build timestamp is a content update. Dataset verification dates remain visible per model.

A project site cannot control the host-level `https://yoosseph.github.io/robots.txt`. A file at `/nvidia-model-rankings/robots.txt` would not control crawling, so the builder does not generate one. If a user-level Pages site exists, ensure its root robots rules allow this project path. GitHub controls crawler policy and metadata for `github.com` repository pages; HTML meta tags in a README cannot change them.

## GitHub discovery

Keep the repository About description accurate and concise, with the public catalog as its Website. Use relevant topics such as `nvidia`, `nvidia-nim`, `nvidia-api`, `free-llm-api`, `llm`, `model-catalog`, `mixture-of-experts` and `dataset`. Topics are configured on GitHub, not in a local file. Avoid unrelated popular topics and claims that parameter rankings are quality benchmarks.

## Google Search Console

After publishing, the site owner can add a URL-prefix property for `https://yoosseph.github.io/nvidia-model-rankings/`, complete Google's ownership verification, submit `sitemap.xml`, and inspect the homepage URL. If Google provides an HTML verification file or meta tag, preserve that exact value in the build sources so deployment retains it. Ownership verification requires access to the owner's Google account; a repository change cannot complete it.

Check indexing and actual query traffic in Search Console after Google has crawled the site. Metadata and sitemaps help discovery; they do not guarantee indexing, rich results or a particular ranking.

## References

- [Google's search guide for developers](https://developers.google.com/search/docs/fundamentals/get-started-developers)
- [Google's dataset structured data documentation](https://developers.google.com/search/docs/appearance/structured-data/dataset)
- [Google's robots.txt scope and placement rules](https://developers.google.com/search/docs/crawling-indexing/robots/create-robots-txt)
- [GitHub repository topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)
- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
