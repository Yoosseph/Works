# Methodology

## Scope

NVIDIA Model Rankings tracks every model ID returned by NVIDIA's hosted API model list, `https://integrate.api.nvidia.com/v1/models`. Those are the models you can address with an NVIDIA API key from [build.nvidia.com](https://build.nvidia.com/models). The catalog is independent and curated. It does not guarantee availability and is not maintained by NVIDIA.

Records have a `category`. Only `llm` records (language, vision-language and other generative models) are ranked. Safety, reward, embedding, document-parsing and detection models are listed separately, because comparing their sizes with generative LLMs is misleading.

## Endpoint status

Status is derived from evidence, never from a model's name or popularity:

| Status | Evidence |
|---|---|
| `Free Endpoint` | Listed by `/v1/models`, has a published NVIDIA model card (`https://build.nvidia.com/<slug>.md`), and its model page shows no deprecation date in the past. |
| `Deprecated` | Listed by `/v1/models`, but the model page shows a deprecation date on or before `last_verified`, or redirects to `experience-unavailable` or a successor model. |
| `Unlisted` | Listed by `/v1/models`, but NVIDIA no longer publishes a model page or card for it. |

`free_endpoint` is `true` only for `Free Endpoint`. Free means a free NVIDIA Developer Program API key can be used for prototyping. Access is a rate-limited trial under the NVIDIA API Trial Terms of Service, not unlimited production access.

Two pitfalls this method avoids:

- `build.nvidia.com/<anything>` returns HTTP 200 with a generic page even for model IDs that do not exist. The markdown model card, not the HTTP status, proves that a page exists.
- Page slugs often differ from API IDs. For example, `nvidia/llama-3.1-nemotron-70b-instruct` lives at `nvidia/llama-3_1-nemotron-70b-instruct`. `nvidia_url` stores the real page.

Models that drop out of `/v1/models` move to `data/removed.json`, with NVIDIA's deprecation date where one was published.

## Parameters and ranking

- `total_parameters`: parameters in the complete model, including vision or audio encoders when they ship in the checkpoint.
- `active_parameters`: parameters used per token. For sparse MoE and hybrid MoE models this is the developer's stated figure. Dense models use their total. `null` means not stated.
- `parameter_basis`:
  - `checkpoint`: the exact count Hugging Face reports for the official **unquantized** (BF16, FP16 or FP32) safetensors checkpoint.
  - `stated`: the figure on the NVIDIA model card or the developer's model card. It is used when no unquantized checkpoint is public, or when weights are stored in packed quantized formats (INT4, MXFP4, NVFP4, FP8), where Hugging Face's element count is not a parameter count.
- **Counts are never inferred from model names.** Mixtral-8x22B has 141B parameters, not 8 × 22 = 176B, and Nemotron 3 Ultra "550B" has a 560.5B BF16 checkpoint.

Ranking sorts by `total_parameters`, descending. Unknown counts sort last. README figures are rounded to three significant figures. The JSON holds the integers.

## Context length

`context_length` is the maximum context in tokens stated by the NVIDIA model card, the developer's model card, or the checkpoint's `config.json`, in that order of preference. NVIDIA's hosted endpoint may serve a shorter window. `null` means the value was not verified.

## Keeping it current

`python scripts/update_models.py --check` compares the dataset with the live API. It reports new IDs (with facts pulled from their NVIDIA card), vanished IDs and status changes. `--apply` writes availability changes only. `--probe` sends a one-token request to each LLM using `NVIDIA_API_KEY`, for direct confirmation. Parameter counts are always added by hand with a cited source.

`last_verified` is the date the record's claims were last checked against the cited sources.
