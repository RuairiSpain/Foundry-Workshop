# Lab 04 — Model router

You'll connect to the hub's shared model router and send it a batch of
questions that vary in difficulty, then read which underlying model
handled each one.

**Verified against:** Microsoft Foundry model router (GA), as of writing
this workshop.

## Prerequisites

- Lab 03 complete.
- The hub's `cascadia-router` deployment exists — your instructor set
  this up; you don't deploy it yourself.

## Step 1: Find the router in the Portal

1. Open the Foundry Portal for the hub project.
2. Under **Deployments**, find `cascadia-router`.
3. Open its **Details** pane and note the list of underlying models it
   can route to.

You're looking at a deployment your instructor owns, not one of yours —
this is the shared, quota-sensitive resource from Lab 03's README.

## Step 2: Implement the triage script

Open `starter/router_triage.py`. Implement three functions:

1. `route_question()` — call `chat_client.chat.completions.create()` with
   `model=router_deployment`, then build a `RoutedReply` from the
   response. Read the underlying model from `response.model` — it's not
   the same string as `router_deployment`.
2. `route_all()` — get the OpenAI-shaped client from
   `client.get_openai_client()`, then call `route_question()` once per
   question.
3. `summarize_routing()` — count how many questions each underlying
   model handled.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 5 passed.

## Step 3: Run it against the real router

```bash
export ROUTER_DEPLOYMENT=cascadia-router
python3 starter/router_triage.py
```

**Expected output:** one `[<model>] <question>...` line per question,
followed by a summary dict. The easy return-window question and the
long multi-part policy question should show different underlying
models — if they don't, move to step 4 before assuming something's
wrong.

## Step 4: Read the routing decision in the trace

1. Open the Foundry Portal's **Tracing** view for your project.
2. Find the three requests you just sent.
3. Open the hardest question's trace and find the routing decision — it
   names the underlying model and, on recent router versions, a short
   reason for the choice.

**Expected output:** a trace entry showing the router selected a
different model for the long question than for the two short ones.

## Where this fits

Lab 05 tunes the same `complete()` call with inference parameters and
prompt caching. Lab 30 comes back to this router as the thing the AI
Gateway sits in front of, with per-attendee token limits on top of it.
