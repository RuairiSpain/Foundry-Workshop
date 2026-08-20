# Lab 03 — Deploy a low-cost model

You'll deploy a small model into your own project, then write a script
that compares it against the hub's shared router on the same prompt.

**Verified against:** Foundry Toolkit for VS Code, Model Playground, as
of writing this workshop.

## Prerequisites

- Lab 01 or Lab 02 complete: your project exists under the hub, and
  `FOUNDRY_PROJECT_ENDPOINT` is set.

## Step 1: Deploy a low-cost model

1. In the Foundry Toolkit, open your project.
2. Select **Model catalog**.
3. Search for a small, low-cost chat model — for example, a `-mini`
   variant.
4. Select **Deploy**, and name the deployment `cascadia-low-cost`.
5. Wait for the deployment to show **Succeeded**.

Deploying into your own project, rather than using a hub-shared
deployment, is deliberate here — this is your one hands-on deployment
rep. Lab 04's router stays hub-shared, since it's the more expensive,
quota-sensitive resource.

## Step 2: Compare it in the Playground

1. Open **Model Playground**.
2. Select **Compare**.
3. Set the left pane to your new `cascadia-low-cost` deployment.
4. Set the right pane to the hub's `cascadia-router` deployment.
5. Send: `In one sentence, what does Cascadia Outfitters sell?`

**Expected output:** two replies, side by side. Note the response time
and length difference — you'll measure this in code next.

6. Select **View Code** on either pane and skim the generated Python.
   `starter/compare_models.py` is that same call shape, refactored so
   you write it once and reuse it in Labs 04 and 05.

## Step 3: Implement the comparison script

Open `starter/compare_models.py`. Implement two functions:

1. `_call_model()` — call `chat_client.chat.completions.create()` with
   the given deployment name and a one-message prompt, then build a
   `ModelReply` from the response.
2. `run_comparison()` — get the OpenAI-shaped client from
   `client.get_openai_client()`, call `_call_model()` once per
   deployment, and return a `ComparisonResult`.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 4 passed.

## Step 4: Run it against your real deployments

```bash
export LOW_COST_DEPLOYMENT=cascadia-low-cost
export ROUTER_DEPLOYMENT=cascadia-router
python3 starter/compare_models.py
```

**Expected output:** two reply lines with token counts, followed by a
`Token difference:` line.

## Where this fits

The `client.get_openai_client()` call you just wrote is the one piece
of SDK plumbing every later lab reuses. Lab 04 replaces
the second deployment with the router's dynamic routing behavior. Lab 05
adds inference parameters and prompt caching to this same call shape.
