# Lab 14 — Prompt optimization

You'll run a deliberately weak system prompt through the Prompt
Optimizer, then score both versions against the same three questions to
measure the difference instead of eyeballing it.

**Verified against:** Foundry Toolkit for VS Code, Prompt Optimizer, as
of writing this workshop.

## Prerequisites

- Lab 03 complete.

## Step 1: Run the optimizer

1. Open **Model Playground** with your `cascadia-low-cost` deployment.
2. Set the system prompt to `WEAK_SYSTEM_PROMPT` from
   `starter/prompt_scoring.py`: `You are a helpful assistant for a
   store.`
3. Select **Optimize prompt**.
4. Read the optimizer's suggested rewrite, and copy it.

**Expected output:** a rewritten prompt naming Cascadia Outfitters
specifically, with instructions to cite policy facts rather than
generalize.

## Step 2: Implement the scoring functions

Open `starter/prompt_scoring.py`. Implement three functions:

1. `score_reply()` — return the fraction of `must_contain` phrases
   found in `reply`, case-insensitively. An empty `must_contain` list
   scores 1.0.
2. `score_system_prompt()` — call `chat_client.complete()` once per
   question, with a system message and a user message, and score each
   reply.
3. `compare_prompts()` — call `score_system_prompt()` for both prompts
   and return a `PromptComparison`.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 7 passed.

## Step 3: Run the real comparison

```bash
export OPTIMIZED_SYSTEM_PROMPT="<paste the optimizer's output from step 1>"
python3 starter/prompt_scoring.py
```

**Expected output:**

```
Weak prompt average score:      0.33
Optimized prompt average score: 1.00
Improved: True
```

Your exact numbers will vary — the weak prompt won't always score 0.33 —
but the optimized prompt should score meaningfully higher across all
three questions.

## Where this fits

Lab 15 turns this same before/after idea into a proper eval dataset with
groundedness, relevance, and safety metrics, instead of the simple
phrase-matching score you wrote here. Lab 27 wires that eval into a
CI/CD gate that blocks a regression from shipping at all.
