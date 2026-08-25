"""Minimal cost/latency benchmark across direct Foundry model deployments.

Fill in ENDPOINT, API_KEY, and MODELS below for your own Foundry
project, then:

    python3 benchmark.py

Writes one row per (model, prompt) to results.csv, and one row per
model — averaged — to summary.csv.

Uses Foundry's unified Model Inference API (azure-ai-inference), which
talks to Azure OpenAI and non-OpenAI catalog models like DeepSeek
through the same client and endpoint — just swap MODELS for whichever
deployment names exist in your project.
"""

import csv
import json
import time

from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

# --- Fill these in for your Foundry project --------------------------------
ENDPOINT = "https://<your-project>.services.ai.azure.com"
API_KEY = "<your-api-key>"
MODELS = [
    "deepseek-v4-flash-3107",
    "gpt-5-sol",
    "gpt-5-mini",
]
# -----------------------------------------------------------------------------

PROMPTS_FILE = "prompts.jsonl"
RESULTS_FILE = "results.csv"
SUMMARY_FILE = "summary.csv"
MAX_TOKENS = 300


def load_prompts(path):
    prompts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                prompts.append(json.loads(line))
    return prompts


def run_benchmark():
    client = ChatCompletionsClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))
    prompts = load_prompts(PROMPTS_FILE)
    rows = []

    for model in MODELS:
        for prompt in prompts:
            start = time.perf_counter()
            response = client.complete(
                model=model,
                messages=[{"role": "user", "content": prompt["prompt"]}],
                max_tokens=MAX_TOKENS,
            )
            latency_ms = (time.perf_counter() - start) * 1000
            usage = response.usage

            row = {
                "model": model,
                "prompt_id": prompt["prompt_id"],
                "latency_ms": round(latency_ms, 1),
                "prompt_tokens": usage.prompt_tokens if usage else None,
                "completion_tokens": usage.completion_tokens if usage else None,
                "total_tokens": usage.total_tokens if usage else None,
            }
            rows.append(row)
            print(f"{model:24s} {prompt['prompt_id']:10s} {latency_ms:8.1f} ms")

    write_csv(RESULTS_FILE, rows)
    write_summary(rows)


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {path} ({len(rows)} rows)")


def write_summary(rows):
    """Average latency and average tokens per model — makes results.csv
    much easier to show a customer at a glance.
    """
    by_model = {}
    for row in rows:
        by_model.setdefault(row["model"], []).append(row)

    summary_rows = []
    for model, model_rows in by_model.items():
        count = len(model_rows)
        summary_rows.append(
            {
                "model": model,
                "requests": count,
                "avg_latency_ms": round(sum(r["latency_ms"] for r in model_rows) / count, 1),
                "avg_prompt_tokens": round(sum(r["prompt_tokens"] or 0 for r in model_rows) / count, 1),
                "avg_completion_tokens": round(sum(r["completion_tokens"] or 0 for r in model_rows) / count, 1),
                "avg_total_tokens": round(sum(r["total_tokens"] or 0 for r in model_rows) / count, 1),
            }
        )

    write_csv(SUMMARY_FILE, summary_rows)


if __name__ == "__main__":
    run_benchmark()
