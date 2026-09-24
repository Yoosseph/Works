# Contributing

Thanks for helping keep the catalog accurate.

## Adding or updating a model

1. Find a model-specific NVIDIA page on `build.nvidia.com`.
2. Verify total and active parameters from an official developer source or model card. Never infer counts from a name.
3. Add one record to `data/models.json` with numeric parameter values, both source URLs, and the current ISO date in `last_verified`.
4. Set `free_endpoint` to `true` only when the NVIDIA page currently supports the definition in [methodology.md](docs/methodology.md).
5. Run `python scripts/validate_data.py` and `python scripts/generate_readme.py`.
6. Include the generated README and explain any source discrepancy in the pull request.

Do not add API keys, scraped credentials, paid-service dependencies, or claims that cannot be cited. Availability changes quickly, so conservative `Unknown` values are preferable to guesses.
