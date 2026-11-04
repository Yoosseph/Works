# Sources

Every record in `data/models.json` links to its own NVIDIA page (`nvidia_url`), its parameter source (`parameter_source`) and the availability source (`endpoint_source`). These are the source families used, in order of preference:

1. **[NVIDIA API model list](https://integrate.api.nvidia.com/v1/models)**: the authoritative list of model IDs addressable with an NVIDIA API key. No key is needed to read it.
2. **NVIDIA model pages and cards**: `https://build.nvidia.com/<slug>` and the markdown card at `https://build.nvidia.com/<slug>.md`. These provide deprecation dates, stated total and active parameters, and context length.
3. **Official Hugging Face model repositories**: exact parameter counts from the safetensors metadata (`https://huggingface.co/api/models/<repo>`) and context length from `config.json`. Only the developer's own organization is used, such as `meta-llama`, `mistralai`, `nvidia` or `google`.
4. **Developer model cards, technical reports and announcements**, when the above are silent.

Third-party blogs, leaderboards and aggregator sites are not used as sources for any number.

A source link establishes provenance. It does not imply that a model is still hosted or free; the `endpoint_status` field and [the methodology](methodology.md) cover that.
