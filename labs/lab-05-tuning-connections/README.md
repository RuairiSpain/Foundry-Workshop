# Lab 05 — Tuning model connections

You'll add inference parameters to the call shape from Labs 03 and 04,
sweep temperature to see its effect, and check whether prompt caching
kicked in on a repeated call.

**Verified against:** `azure-ai-projects` 1.0.0b12, as of writing this
workshop.

## Prerequisites

- Lab 03 complete: your `cascadia-low-cost` deployment exists.

## Step 1: Implement the tuning functions

Open `starter/tuning.py`. Implement four functions:

1. `build_completion_kwargs()` — return a dict with `temperature`,
   `top_p`, and `max_tokens`. Add `seed` only when it's not `None`.
2. `call_with_params()` — build kwargs with `build_completion_kwargs()`,
   call `chat_client.chat.completions.create()`, and return a
   `TunedReply`. The cached-token count lives at
   `response.usage.prompt_tokens_details.cached_tokens`, not
   `response.usage.cached_tokens`.
3. `sweep_temperature()` — call `call_with_params()` once per value in
   `temperatures`.
4. `check_prompt_caching()` — call `call_with_params()` twice with the
   same prompt, and return a `CacheReport` from both replies'
   `cached_tokens`.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 7 passed.

## Step 2: Run the temperature sweep against your real deployment

```bash
export LOW_COST_DEPLOYMENT=cascadia-low-cost
python3 starter/tuning.py
```

**Expected output:** three `temperature=<value>: <reply>` lines. The
`temperature=0.0` reply should look close to deterministic if you run
the script twice in a row; the `temperature=1.4` reply should vary more.

## Step 3: Read the caching result

Same run as step 2 prints a final line:

```
Cache hit on second call: True
```

If it prints `False`, the prompt was short enough, or different enough
between calls, that there was nothing worth caching — prompt caching
only engages above a minimum prompt length. Try it again with a longer,
identical prompt.

## Step 4: Set a project-scoped token limit

1. Open the Foundry Portal's **Control plane** for your project.
2. Under **Limits**, set a tokens-per-minute cap on your
   `cascadia-low-cost` deployment.
3. Re-run `starter/tuning.py` in a tight loop (a shell `for` loop calling
   it 10 times) until a call fails.

**Expected output:** a `429`-style rate-limit error on one of the later
calls, once your cap is exceeded.

This is the same control that protects the hub's shared router from one
attendee's heavy Lab 22 run later in the workshop — you're setting it on
your own deployment first, where a mistake only affects you.

## Where this fits

Lab 30 sets project-scoped token limits again, this time at the AI
Gateway in front of the hub, with a rate-limit policy per attendee
instead of a single cap you set for yourself.
