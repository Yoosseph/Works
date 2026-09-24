# Methodology

## Scope

The catalog tracks language, multimodal, and generative models listed on NVIDIA's model ecosystem, especially model-specific pages on `build.nvidia.com`. It is a curated reference, not an availability guarantee or an NVIDIA-maintained list.

## Free endpoint definition

`Free Endpoint` means the model's NVIDIA page showed hosted API access available without a paid NVIDIA service at the time recorded in `last_verified`. A free API key may still require an account, have quotas, rate limits, expiration, geography restrictions, or changing terms. The label is never inferred from a model name or from the existence of a downloadable checkpoint.

## Parameters and ranking

`total_parameters` is the published count for the complete model. `active_parameters` is the count used per token for a sparse MoE model. MoE models are sorted by total parameters, never active parameters. Dense models use the total count as active when the source treats all parameters as used; otherwise active is `null`. Unknown values remain `null` and sort last.

Parameter counts are numeric integers in JSON. Display formatting (for example, `671B`) is generated and must not be manually edited in README tables.

## Context length

Context length records the maximum context stated by the cited model documentation, in tokens. NVIDIA serving configurations can impose a smaller limit. `null` means the value was not sufficiently verified.

## Exclusions

Embedding, reranking, speech, image-generation, and other non-LLM models should be kept in a separate dataset section because comparing their parameter counts with generative LLMs is misleading. This initial catalog contains only generative and multimodal LLM records.

## Sources and verification

Sources are prioritized as follows: model-specific NVIDIA pages, NVIDIA API/NIM documentation, official developer documentation, official Hugging Face cards, official repositories, and papers. Each record needs both a parameter source and an endpoint source. `last_verified` is the date the maintainer last checked the cited claims, not the publication date.

The catalog should be reviewed monthly and whenever NVIDIA changes its model catalog. `scripts/update_models.py` deliberately does not scrape pages: brittle scraping could silently turn unavailable or unknown data into false claims.
