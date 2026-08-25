# DeepSeek cost/latency benchmark

A deliberately thin benchmark comparing cost and latency across three
direct Foundry model deployments — DeepSeek-v4-flash-3107 and two
Azure OpenAI deployments (GPT-5 Sol, GPT-5 Mini by default). One Python
client, a fixed JSONL prompt set, no agents, tools, grounding, or
knowledge sources.

The design records per-request telemetry in the client and treats
Azure Monitor as an independent validation/aggregate source, rather
than expecting platform logs alone to map every metric back to a
specific prompt — see [Foundry logging](#1-foundry-logging) below for
why.

## 1. Foundry logging

**What Foundry records automatically.** Azure Monitor automatically
collects aggregated metrics for Foundry model deployments with no
extra configuration. Depending on the model and deployment type, these
can include request counts, processed prompt tokens, generated
completion tokens, time to response, time to last byte, time to first
byte, time between tokens, and tokens per second.

For Azure OpenAI deployments specifically, Microsoft recommends the
Azure OpenAI-specific latency metrics over the generic Cognitive
Services `Latency` metric, which it documents as potentially
misleading for Azure OpenAI workloads:

- `AzureOpenAITimeToResponse`
- `AzureOpenAITTLTInMS`
- `AzureOpenAINormalizedTTFTInMS`
- `AzureOpenAINormalizedTBTInMS`
- `Processed Prompt Tokens`
- `Generated Completion Tokens`

**What requires configuration.** Querying resource *logs* through Log
Analytics needs a diagnostic setting on the Foundry resource, sending
the supported log categories and `AllMetrics` to a Log Analytics
workspace. You'll need: a Log Analytics workspace; a diagnostic
setting on the Foundry resource with `AllMetrics` and the supported
inference/request-response log categories enabled; **Monitoring
Reader** to query metrics; **Log Analytics Reader** to query the
workspace; and **Monitoring Contributor** (or equivalent) to configure
the diagnostic setting in the first place.

**The important limitation.** Azure Monitor metrics are primarily
deployment-level, time-series aggregates. They validate total token
consumption and service-side latency *by model deployment* well, but
they are not a reliable way to map one specific prompt ID to one
specific invocation.

That's why the benchmark client captures, per request: prompt ID,
model deployment name, the service's response request ID, input/
output/cached/reasoning/total tokens from the SDK response, client-
observed latency, time to first token (streaming), UTC start/
completion timestamps, HTTP status, retry count, error detail, and a
benchmark run ID (spec 2.7's full schema — see [Per-request
record](#per-request-record-outputrequestsjsonl) below).

**Design decision this benchmark follows throughout:** the SDK
response is the authoritative *per-request* token record; Azure
Monitor is the authoritative *platform-level* aggregate. The two are
reconciled by model, deployment, region, and time window — never
forced to agree (see [Reconciliation](#reconciliation) below).

## Scope

Direct model inference only. No Foundry Agent Service, Prompt Flow,
tools, function calling, web search, RAG, Azure AI Search, files,
knowledge sources, conversation history, persistent threads, model
routing, or APIM. APIM can be layered on as a separate test later —
including it in the baseline would mix network/policy-processing
latency into the numbers this benchmark is trying to isolate.

## Layout

```
deepseek/
├── config/
│   ├── models.yaml       # deployment names — confirm these against your project
│   └── pricing.yaml      # versioned, editable cost table (placeholder prices — see below)
├── data/
│   └── prompts.jsonl     # 18 synthetic, self-contained prompts
├── src/
│   ├── models.py          # typed config/record dataclasses
│   ├── client_factory.py  # auth + per-deployment SDK client construction
│   ├── inference_client.py# one physical attempt: streaming/non-streaming, timing
│   ├── benchmark_runner.py# warm-up, ordering, retries, concurrency, resume, JSONL writer
│   ├── pricing.py         # cost estimation from pricing.yaml
│   ├── telemetry.py       # OpenTelemetry spans -> Application Insights
│   ├── azure_monitor.py   # platform-level metric query + reconciliation input
│   ├── aggregation.py     # percentiles, summary rows, reconciliation rows, CSV writers
│   └── cli.py              # validate-config / dry-run / run / reconcile
├── output/                # requests.jsonl, results.csv, model_summary.csv, reconciliation.csv
└── tests/                  # mocked-SDK unit tests; no network calls
```

## Setup

```bash
cd deepseek
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in AZURE_FOUNDRY_ENDPOINT at minimum
```

### Confirm your deployment names

`config/models.yaml`'s `deployment_name` values are placeholders.
**Confirm the exact deployment names in your Foundry project** (Portal
→ Deployments) before running — the deployment name used by the API
can differ from the catalog model ID, and the benchmark fails fast
with a clear error (`DeploymentResolutionError`) rather than silently
falling back to a different deployment if a name doesn't resolve.

### Authentication

`DefaultAzureCredential` (Entra ID) is the default and preferred path —
it covers both managed identity (running in Azure) and Azure CLI
credentials (local development) automatically, trying each in turn.
API keys are supported only as an explicit opt-in fallback:
`AZURE_FOUNDRY_USE_API_KEY=true` plus `AZURE_FOUNDRY_API_KEY=<key>`. No
credentials are stored in source control or in `data/prompts.jsonl`.

## Running it

```bash
# 1. Validate configuration and the prompt dataset — no network calls.
python3 -m src.cli validate-config

# 2. See what a run would do — no network calls.
python3 -m src.cli dry-run --repeats 5 --warm-up 3

# 3. Run it. Sequential (concurrency=1) is the latency-measurement mode.
python3 -m src.cli run --repeats 5 --warm-up 3 --azure-monitor

# Restrict to one model/category/difficulty:
python3 -m src.cli run --model deepseek-v4-flash --category classification

# A separate throughput test (not mixed with the latency numbers above):
python3 -m src.cli run --concurrency 8 --run-id throughput-test-001

# Resume an interrupted run — already-recorded (model, prompt_id, repeat)
# combinations are skipped, not re-attempted:
python3 -m src.cli run --resume --run-id <the same run-id>

# Reconcile an already-completed run against Azure Monitor separately:
python3 -m src.cli reconcile --run-id <run-id>
```

Every `run` writes to `output/requests.jsonl` (append-only,
flushed per record so an interrupted run never loses a completed one),
then `output/model_summary.csv` and `output/results.csv`. `--azure-
monitor` (or the standalone `reconcile` command) additionally writes
`output/reconciliation.csv`.

### Recommended baseline

```
temperature: 0, top_p: 1, max_output_tokens: 500 (capped per-prompt), stream: true, seed: 42
warm-up: 3 per model (excluded from results)
repeats: 5 per prompt/model
concurrency: 1 (sequential — the default latency test)
cooldown: 500–1000 ms between requests
max retries: 3, exponential backoff with jitter
```

Some deployments (reasoning models especially) reject a fixed
temperature/top_p/seed with a 400. The benchmark does **not** silently
retry without the rejected parameter — the first rejection shows up as
a normal failed record (`error_type="unsupported_parameter"`). Flip
the matching `supports_temperature`/`supports_top_p`/`supports_seed`
flag in `config/models.yaml` once you've seen that, so every later run
records the omission explicitly (spec 2.5: "record unsupported
parameters rather than silently changing them").

## Latency definitions

| Field | Meaning |
|---|---|
| `client_latency_ms` | Before the SDK call → receipt of the final response. |
| `time_to_first_token_ms` | Before the SDK call → first streamed content token. **`null` for non-streaming** — never backfilled from total latency. |
| `generation_time_ms` | First streamed content token → the last one. `null` for non-streaming. |
| `service_time_to_response_ms` / `service_time_to_last_byte_ms` / `normalized_ttft_ms` / `normalized_tbt_ms` | Azure Monitor's own metrics — a platform-side cross-check, not derived from the client timings above. |

## Per-request record (`output/requests.jsonl`)

One append-only JSON line per attempt, matching the full schema in the
original spec: `benchmark_run_id`, `prompt_id`, `category`,
`difficulty`, `model`, `deployment_name`, `provider`, `region`,
`repeat`, `streaming`, `started_at_utc`, `completed_at_utc`,
`request_id`, `client_request_id`, `http_status`, `retry_count`,
`input_tokens`, `cached_input_tokens`, `output_tokens`,
`reasoning_tokens`, `total_tokens`, `client_latency_ms`,
`time_to_first_token_ms`, `generation_time_ms`,
`output_tokens_per_second`, `finish_reason`, `estimated_input_cost`,
`estimated_output_cost`, `estimated_total_cost`, `response_sha256`,
`response_text`, `error_type`, `error_message`.

`response_text` storage is configurable (`--no-response-text` on
`run`). The prompts are synthetic, so storing responses by default is
safe for demos; use `--no-response-text` for any run against
customer-shaped data. `response_sha256` is always kept even when the
text is redacted, so two runs' outputs can be compared for equality
without the content itself ever being stored.

## Cost estimation

`config/pricing.yaml` is a versioned, human-edited price table, kept
out of the code on purpose. **The shipped prices are placeholders**
(`source: manual-placeholder`) — replace them with verified numbers
(`manual-verified` or `retrieved`) before treating any cost output as
real. Cached input tokens are billed at the cheaper
`cached_input_price_per_million` rate; everything else at the standard
input rate.

Azure Cost Management shows actual post-consumption charges, but
Microsoft documents an approximate five-hour delay before model
consumption appears there. This benchmark never waits on it — SDK
token counts + the price table give an *immediate estimate*; Cost
Management is the later, separate billing-reconciliation step.

## Reconciliation

After a run, `--azure-monitor` (or `reconcile`) queries Azure Monitor
over a padded window around the run and compares SDK-summed
`input_tokens`/`output_tokens` totals against Azure Monitor's
`Processed Prompt Tokens`/`Generated Completion Tokens`. A gap is
**reported, never forced to agree** — differences over 1% get a
"possible causes" note (warm-up traffic in the window, retries adding
physical requests, other callers on the same deployment, aggregation-
boundary misalignment, a provider exposing different usage fields,
cached tokens represented differently, or a delayed/unavailable
metric). A metric Azure Monitor can't return is marked *unavailable*,
never treated as zero.

For Azure OpenAI deployments, the query uses Microsoft's documented
metric names (see [Foundry logging](#1-foundry-logging) above) —
**confirm the exact spelling in your own resource's Metrics blade**
before trusting the output; this project has no live Foundry resource
to verify them against. For DeepSeek (and any non-Azure-OpenAI
provider), no metric names are assumed at all — the client enumerates
`list_metric_definitions()` first and only queries what the resource
actually exposes, per spec 2.9.

**A real, checkable finding from building this:** `azure-monitor-
query` 2.0.0 (the actual current release on PyPI) no longer ships
`MetricsQueryClient` — only `LogsQueryClient` remains in that package.
Metrics querying moved to a new, separate package,
`azure-monitor-querymetrics` 1.0.0, which needs a *regional* metrics
endpoint rather than a plain resource ID. `src/azure_monitor.py` uses
`azure-mgmt-monitor`'s ARM-based `MonitorManagementClient` instead —
one package, no region lookup, the same underlying REST API the
retired client used to wrap. See that module's docstring.

## Testing

```bash
cd deepseek
python3 -m pytest tests/ -v --cov=src --cov-report=term-missing
```

All SDK and Azure Monitor calls are mocked — the suite makes zero
network calls and needs no credentials. Coverage is intentionally
below 100%: `cli.py`'s `run`/`reconcile` commands and pieces of
`telemetry.py`/`client_factory.py` wire together real Azure SDK
clients and the Application Insights exporter, which only make sense
exercised against a live endpoint — the modules they call into
(`benchmark_runner`, `aggregation`, `azure_monitor`, `inference_client`,
`pricing`) carry the unit-tested logic and are covered thoroughly.

## What this benchmark deliberately doesn't do

Model routing, RAG, tools, agents, persistent threads, or APIM — see
[Scope](#scope). It's a direct-inference cost/latency comparison, not
a capability evaluation.
