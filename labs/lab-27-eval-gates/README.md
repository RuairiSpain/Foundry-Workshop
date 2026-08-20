# Lab 27 — Evaluation gates in CI/CD

You'll wire Lab 15's evaluation approach into a release gate: a new
agent version only gets published and canaried if it doesn't regress
against the version already live.

**Verified against:** Foundry Portal evaluation and Agent Applications,
as of writing this workshop.

## Prerequisites

- Lab 15 and Lab 26 complete.

## Step 1: Implement the gate

Open `starter/eval_gate.py`. Implement four functions:

1. `score_reply()` — same logic as Lab 14/15.
2. `evaluate_deployment()` — call the model once per dataset item, and
   return the average score.
3. `run_evaluation_gate()` — score both the baseline and the candidate
   deployment, and return a `GateResult`.
4. `publish_if_gate_passes()` — run the gate. If it fails, raise
   `RegressionError` with both scores in the message. If it passes,
   publish the new version and canary it at 10%.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 7 passed. Two tests confirm the gate does its job
both ways: it publishes on a pass, and it raises — leaving the
application at exactly one version — on a regression.

## Step 2: Run the gate against your real deployments

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export AGENT_APPLICATION_ID="<your app-... ID from Lab 26>"
export CANDIDATE_AGENT_ID="<a second cascadia-support agent with an edited prompt>"
export CANDIDATE_DEPLOYMENT=cascadia-low-cost
python3 starter/eval_gate.py
```

**Expected output on a pass:** `Published and canaried version 2.`

**Expected output on a regression:** a `RegressionError` naming both
scores, and no new version published — check the Portal to confirm the
application still shows only version 1.

## Step 3: Wire it into a pipeline step

In your CI system (GitHub Actions, Azure Pipelines, whatever your team
uses), add a step that runs this script after any change to an agent's
instructions or tools, before a human ever reviews a canary rollout.
A failing step should block the merge or deployment the same way a
failing test suite would — `RegressionError` is designed to propagate
as a non-zero exit code for exactly this.

## Where this fits

Lab 28 finds agents that are slow, expensive, or failing across the
whole fleet — the operational half of what this lab's gate only checks
at publish time.
