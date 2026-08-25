# DeepSeek cost/latency benchmark — quick start

A minimal script that sends the same 10 prompts directly to three
Foundry model deployments and records latency and token usage. No
agents, tools, or retrieval — just direct calls, timed.

## Setup

```bash
cd deepseek
pip install -r requirements.txt
```

Then open `benchmark.py` and fill in:

- `ENDPOINT` — your Foundry project's inference endpoint
- `API_KEY` — an API key for that project
- `MODELS` — the exact deployment names in your project (not catalog
  model IDs — confirm these in the Foundry Portal under Deployments)

## Run

```bash
python3 benchmark.py
```

This calls every model against every prompt in `prompts.jsonl` once,
printing each request's latency as it goes, then writes:

- **`results.csv`** — one row per (model, prompt): latency, prompt
  tokens, completion tokens, total tokens.
- **`summary.csv`** — one row per model: request count and averaged
  latency/tokens. Easier to hand to a customer than the raw results.

## Using Entra ID instead of an API key

The script above uses an API key for simplicity. If your Foundry
project uses managed identity or Azure CLI credentials instead, ask
and a version using `DefaultAzureCredential` can be swapped in —
it's a one-line change to how the client is constructed.

## Notes

- `results.csv` and `summary.csv` are overwritten on every run.
- Every prompt uses the same `max_tokens` (see `MAX_TOKENS` in
  `benchmark.py`) so token counts stay comparable across models.
- This is intentionally minimal — no retries, streaming, or cost
  estimation. Ask if you want any of those added back in.
