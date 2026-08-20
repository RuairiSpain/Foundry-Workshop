# Lab 33 — Capstone: the governed multi-agent ecosystem

You'll compose the whole workshop into one operated system: the
Magentic fleet from Lab 22 — extended with Lab 23's store-ops
specialist if you have it — behind one release gate that combines
Lab 27's evaluation check, Lab 29's Content Safety policy, Lab 30's
network validation, and Lab 32's governance policy into a single
go/no-go decision.

**Verified against:** `agent-framework` 1.14.0's `MagenticBuilder`
surface, as of writing this workshop.

## Prerequisites

- All prior labs complete. Labs 23, 31, and 32 are optional — this lab
  works either way (see Step 1).

## Concept: operating a system, not building one more agent

Every prior lab proved one mechanism works: a workflow pattern, a
publish flow, an eval gate, a safety policy, a locked-down network, a
governance check. None of them, alone, tells you whether the *whole
fleet* is safe to put in front of a customer today. That's what a
release gate is for — one decision, made from every check's result at
once, the same way a real CI/CD pipeline (Lab 27) wouldn't publish on
a passing eval score alone if the network was still wide open.

## Step 1: Build the full fleet

Open `starter/governed_ecosystem.py`. Implement four functions:

1. `build_governed_workflow()` — the Magentic workflow: manager plus
   four core specialists, plus Lab 23's store-ops specialist when
   `include_store_ops` is True.
2. `build_fleet_manifest()` — the component list, with `optional=True`
   on store-ops and the Teams channel.
3. `evaluate_release_gates()` — one `ReleaseGateResult` from four
   inputs: eval score vs. threshold, Content Safety violations,
   network problems, governance violations.
4. `summarize_release_readiness()` — the operator-facing summary.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 11 passed. If you don't have GitHub Copilot SDK
access (Lab 23), that's fine — `include_store_ops` defaults to False,
and every test still passes without it.

## Step 2: Watch a blocked release get every reason at once

Read `test_evaluate_release_gates_collects_every_reason_at_once`.
Notice it fails an eval score, a Content Safety check, a network
check, and a governance check simultaneously, and asserts all four
reasons come back — not just the first one `evaluate_release_gates()`
happens to check. Fixing one problem and re-running should reveal the
next one immediately, not one release cycle later.

## Step 3: Run the fleet for real

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export HAS_GITHUB_COPILOT_SDK="true"   # or "false" if you skipped Lab 23
export EVAL_SCORE="0.92"               # from a real Lab 27 batch run, once you have one
python3 starter/governed_ecosystem.py
```

**Expected output:** the readiness summary, then — if cleared — the
Magentic workflow's answer to a trip-planning question, the same shape
Lab 22 produced from a smaller fleet.

## Step 4: Put it behind everything else you built

This script is deliberately still a script, not a deployed system. In
your remaining time:

- Publish the workflow as an Agent Application (Lab 26) and gate the
  publish step on `evaluate_release_gates()` in a CI/CD pipeline
  (Lab 27).
- Put it behind the shared AI Gateway (Lab 30) and confirm
  `validate_network_config()` reports no problems before you call
  `evaluate_release_gates()`.
- Register it in Agent 365 (Lab 32, if you have it) and feed
  `evaluate_governance_policy()`'s violations straight into this
  script's `governance_violations` argument.
- If you built the Teams channel (Lab 31), add
  `include_teams_channel=True` to `build_fleet_manifest()` and confirm
  `authenticate_teams_request()` still runs before any of this.

## Where this fits

Nowhere — this is the end of the roadmap. Every concept the curriculum
introduced, from Lab 01's first model deployment to Lab 32's
governance policy, is a component or a gate in the system this lab
just assembled.
