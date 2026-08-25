# Appendix A — Fine-tuning

**Time-permitting.** This is the one lab outside the 33-lab roadmap —
do it if your cohort finishes early, or skip it without leaving a gap
in Module 7's governance story.

You'll fine-tune your low-cost deployment (Lab 03) on a handful of
Cascadia-specific examples, then compare it against the shared router
baseline on the same groundedness scoring Lab 15 introduced.

**Verified against:** `openai` 2.54.0's `client.fine_tuning.jobs`, as of
writing this workshop. Azure OpenAI exposes fine-tuning through the
same OpenAI-compatible endpoint every earlier lab already uses for chat
completions (`client.get_openai_client()`), not a Foundry-specific
client. Whether fine-tuning is enabled for your project is a capability
question for your instructor, not an SDK-shape one.

## Prerequisites

- Labs 03 and 15 complete.

## Concept: fine-tuning is a comparison, not just a training run

A fine-tuned model is only worth deploying if it beats the baseline it
replaces — the router your attendee's project already has, from Lab
04. This lab pairs every fine-tuning step with the comparison that
justifies it: the same prompt, scored the same way, on both models.
Skip the comparison and you've only proven the training job finished,
not that it did anything useful.

## Step 1: Implement the training and comparison logic

Open `starter/fine_tuning.py`. Implement six functions:

1. `build_fine_tuning_dataset()` — question/answer pairs into chat
   fine-tuning records.
2. `submit_fine_tuning_job()` — submit against an uploaded training
   file.
3. `poll_until_complete()` — poll until `succeeded` or `failed`.
4. `score_groundedness()` — Lab 15's scoring, reused as the fair
   yardstick for both models.
5. `compare_against_baseline()` — score the fine-tuned deployment and
   the router on the same dataset.
6. `summarize_comparison()` — wins, losses, and ties.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 11 passed.

## Step 2: Confirm the poll loop actually stops

Read `test_poll_until_complete_raises_timeout_error_when_it_never_finishes`.
A fine-tuning job in the real service can run for hours — a poll loop
with no upper bound would hang a CI pipeline (Lab 27) indefinitely if a
job ever got stuck. `max_polls` is why this lab's loop can't do that.

## Step 3: Fine-tune your real deployment

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
python3 starter/fine_tuning.py
```

**Expected output:** the job's status prints as it polls, then
`Fine-tuned model ready: <name>`, then the win/loss/tie summary against
the router. Read the two full replies for any question the router won
— that's the real signal for whether more training examples would
help, not just the score.

## Where this fits

If your fine-tuned model wins the comparison, it's a candidate
deployment for one of Lab 33's specialists — publish it the same way
Lab 26 published any other version, gated by Lab 27's eval check on
this exact comparison.
