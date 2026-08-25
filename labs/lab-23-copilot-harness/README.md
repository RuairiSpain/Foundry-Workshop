# Lab 23 — The GitHub Copilot harness

**Optional — requires GitHub Copilot SDK access** on top of your Azure
and Foundry access. Ask your instructor if you're not sure whether
you have it; if you don't, read through this lab and skip the hands-on
steps, or watch it as an instructor demo.

You'll build a store-ops agent on the GitHub Copilot SDK's agent
implementation instead of MAF's own — swapping the harness layer from
Lab 21 for a different one — and implement a propose-then-approve flow
so it can edit config files without ever writing one unreviewed.

**Verified against:** `agent-framework` 1.14.0's `agent_framework.github`
module, as of writing this workshop.

## Prerequisites

- Lab 21 complete.
- GitHub Copilot SDK access.

## Concept: a different harness, not just different settings

Lab 21's harness came from `create_harness_agent()`, layered on MAF's
own `Agent`. `GitHubCopilotAgent` is a different implementation
entirely — the same harness *idea* (a loop with tools, approval, and
context management), built by GitHub instead of by MAF. Both are valid
harnesses; which one you pick depends on what you're editing. A
coding-grade harness — built to review diffs and gate file writes — is
a better fit for a config-editing agent than a general-purpose one.

## Step 1: Implement the agent and the approval flow

Open `starter/store_ops_agent.py`. Implement three functions:

1. `build_store_ops_agent()` — a `GitHubCopilotAgent` built from
   `STORE_OPS_INSTRUCTIONS`, named `cascadia-store-ops`.
2. `propose_config_edit()` — read the file's current text if it exists
   (otherwise `""`), and return a `ConfigEditProposal`. Never write.
3. `apply_config_edit()` — raise `PermissionError` if `approved` is
   `False`. Otherwise write the proposed content and return a
   confirmation string.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 7 passed.

## Step 2: Run it against the real store-hours config

```bash
python3 starter/store_ops_agent.py
```

**Expected output:** a diff preview printed to the terminal, then a
prompt: `Approve this edit? [y/N]`. Answer `n` and confirm
`case-study/store-ops-configs/store-hours.yaml` is unchanged. Run it
again and answer `y` — now it's written.

## Step 3: Compare against Lab 21's harness

Both harnesses solve "agent with more capability than a plain loop."
Neither is strictly better — Lab 21's `create_harness_agent()` is
MAF-native and works with any MAF-supported model backend; this lab's
`GitHubCopilotAgent` is purpose-built around the coding and file-editing
loop GitHub Copilot already runs in production. Pick based on the task,
not out of habit.

## Where this fits

Lab 33's capstone treats the store-ops agent as one more specialist a
Magentic manager can delegate to, the same way Lab 22 delegated to the
order and trip-planner agents — a different harness doesn't change how
it composes into the rest of the system.
