# Beta debrief — Lab 21 (MAF fundamentals)

## What the simulated attendee did

Implemented all three functions using only the README's Step 1 list and the
starter file's docstrings/TODOs, referring back to Lab 12's starter (an
earlier, already-completed lab) for the `Agent(...)` call shape as the
README explicitly directs ("the same `Agent` construction as Lab 12").

- `build_agent_loop()` — `Agent(client, name=..., instructions=..., tools=[suggest_gear_for_trail])`.
- `build_workflow()` — `SequentialBuilder(participants=[build_agent_loop(client)]).build()`.
- `build_harness_agent()` — `create_harness_agent(client, name=..., agent_instructions=..., tools=[suggest_gear_for_trail], disable_web_search=True)`.

## Where it diverged

`LAB_TARGET=starter python3 -m pytest tests/ -v` failed 3 of 7 on the first
pass, all on the same shape of assertion — an exact hardcoded agent name:

```
assert agent.name == "cascadia-trip-planner"          # build_agent_loop
assert agent_executors[0].agent.name == "cascadia-trip-planner"   # build_workflow
assert agent.name == "cascadia-trip-planner-harness"  # build_harness_agent
```

For `build_agent_loop`, this is recoverable: the README says "the same
`Agent` construction as Lab 12," and a real attendee who did Lab 12 has
their own working `cascadia-trip-planner` name sitting right there to
reuse. That's a fair inference, not a guess.

For `build_harness_agent`, it isn't recoverable the same way. Lab 12 never
built a harness agent, so there's no prior artifact to copy a name from,
and neither the README's Step 1 bullet ("call `create_harness_agent()`
with a name, `agent_instructions`, the same tool, and
`disable_web_search=True`") nor the starter's TODO comment gives any hint
that the name must be exactly `"cascadia-trip-planner-harness"`. A novice
would have to fail the test once, read `AssertionError: assert 'TripPlanner'
== 'cascadia-trip-planner-harness'` in the pytest output, and copy the
literal string out of the diff — debugging via the test's failure message
rather than the lab materials.

This breaks the pattern the rest of the curriculum follows (see Labs 19
and 20): TODOs elsewhere in this repo spell out exact literal values
(role strings, order params, dict keys) precisely so the attendee never
needs to reverse-engineer a required string from a test failure.

## Judgment

Real gap, worth a small README/starter fix — not a design flaw in the
solution itself (`solution/maf_layers.py` already reads cleanly and
behavior matched what I built once the names were fixed).

## Fix applied

- `README.md` Step 1: named both required agent names explicitly —
  `"cascadia-trip-planner"` for `build_agent_loop()` (reusing Lab 12's
  name) and `"cascadia-trip-planner-harness"` for `build_harness_agent()`.
- `starter/maf_layers.py`: updated the `build_harness_agent` TODO comment
  to state the exact name string, matching how `build_agent_loop`'s TODO
  already points back to Lab 12's name. No implementation logic was added
  to the starter — both functions still raise `NotImplementedError`.
