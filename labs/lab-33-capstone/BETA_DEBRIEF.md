# Beta debrief — Lab 33 Capstone

## What the simulated attendee did

Worked through `starter/governed_ecosystem.py` from the README and the
starter file's docstrings only (reusing Lab 22's manager/specialist
pattern and Lab 23's `GitHubCopilotAgent` usage, both prior-lab code a
real attendee would already have written).

- `build_governed_workflow()` — matched the solution's shape exactly:
  manager plus four named specialists, optional `GitHubCopilotAgent`
  store-ops participant, `MagenticBuilder(...).build()`.
- `build_fleet_manifest()` — matched the solution's shape exactly.
- `summarize_release_readiness()` — matched the solution's shape
  exactly.
- `evaluate_release_gates()` — for the three violation-list reasons,
  the starter docstring gives an explicit required prefix ("Content
  Safety: ", "Network: ", "Governance: "), so those were easy to get
  right. For the eval-score reason, the docstring only said "a
  below-threshold eval score" with no required wording. A natural
  first attempt wrote `f"Eval score {eval_score} is below threshold
  {eval_threshold}"` — plain English matching the docstring's own
  terminology ("eval score").

## Where it diverged

`LAB_TARGET=starter python3 -m pytest tests/ -v` failed one test:

```
test_evaluate_release_gates_blocks_on_a_low_eval_score
assert any("Evaluation score" in reason for reason in result.blocking_reasons)
```

The test requires the literal substring `"Evaluation score"`
(capital-E, the word "Evaluation" spelled out) — not "Eval score",
which is what both the starter docstring's prose and the rest of the
module's naming (`eval_score`, `eval_threshold`, Lab 27 called it "the
eval gate") would lead a reasonable attendee to write. Every other
reason kind in the same function has its exact required text spelled
out in the docstring; this one didn't, so this is a real README/starter
gap, not a misreading. Comparing to `solution/governed_ecosystem.py`
confirmed the solution itself hard-codes `f"Evaluation score {eval_score}
is below the required threshold {eval_threshold}"` — so the fix belongs
in the starter's docstring, not the test or solution.

## Fix applied

Reworded `evaluate_release_gates()`'s docstring in
`starter/governed_ecosystem.py` to spell out the required phrasing the
same way the other three reason kinds already do:

> if `eval_score` is below `eval_threshold`, one reason starting with
> "Evaluation score" (e.g. f"Evaluation score {eval_score} is below the
> required threshold {eval_threshold}")

Re-ran `LAB_TARGET=starter python3 -m pytest tests/ -v` with an
implementation matching the corrected docstring: all 11 tests passed.
Restored `starter/governed_ecosystem.py`'s function bodies to
`raise NotImplementedError` / TODO stubs afterward — only the docstring
wording changed versus the original starter file. `solution/` and
`tests/` were not modified.
