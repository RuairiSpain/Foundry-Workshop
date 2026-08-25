# Lab 29 — Responsible AI, policy, and guardrails

You'll run Content Safety checks, enforce a project-wide policy on the
results, and probe an agent with adversarial prompts the way the AI Red
Teaming Agent does — as a routine check, not a one-off audit.

**Verified against:** Azure AI Content Safety severity scale (0–7), as
of writing this workshop.

## Prerequisites

- Lab 09 complete.

## Step 1: Implement the policy check

Open `starter/responsible_ai.py`. Implement two functions:

1. `check_content_safety()` — call
   `content_safety_client.analyze_text()`.
2. `enforce_policy()` — default to checking every category when
   `blocked_categories` is `None`. Raise `PolicyViolationError` naming
   any category at or above `threshold`.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output (partial):** the two policy tests should pass first —
one confirming every category is checked by default, one confirming an
explicit `blocked_categories` list narrows that.

## Step 2: Implement the red-team probes

Implement two more functions:

3. `run_red_team_probe()` — send each probe's prompt, and flag a
   `ProbeResult` as `leaked` if any of its `forbidden_phrases` appear in
   the reply.
4. `find_leaks()` — filter to the leaked results.

**Expected output:** 8 passed.

## Step 3: Apply Content Safety filters in the Portal

1. Open your project's **Content Safety** settings.
2. Enable filters on `cascadia-support`, with the default severity
   thresholds.
3. In the Agents Playground, try one of `RED_TEAM_PROBES`' prompts.

**Expected output:** the filter blocks the request before the model
generates a reply — compare this against Lab 15's approach, where the
*reply* was scored after the fact. Content Safety filters can stop
things before generation, not just flag them afterward.

## Step 4: Run the red-team probes for real

```bash
export LOW_COST_DEPLOYMENT=cascadia-low-cost
python3 starter/responsible_ai.py
```

**Expected output:** `0/2 probes leaked something they shouldn't have.`
If either probe leaks, that's a real finding — fix the agent's
instructions before moving on, the same way you'd fix a failing test.

## Step 5: Run the AI Red Teaming Agent

1. In the Foundry Portal, open **Evaluation** → **AI Red Teaming Agent**.
2. Point it at `cascadia-support` and run a scan.

**Expected output:** a report covering far more adversarial prompts
than this lab's fixed two-probe set — the automated version of what you
just did by hand.

## Where this fits

Lab 30's AI Gateway adds a layer of enforcement in front of every model
call, not just this agent's — a policy check here proves the agent
behaves; the gateway proves nothing can reach the model without going
through that check at all.
