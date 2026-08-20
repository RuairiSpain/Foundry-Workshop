# Lab 12 beta debrief

## What the simulated attendee did

Implemented `suggest_gear_for_trail()` from the docstring/TODO alone —
clean, matched the solution's behavior (different wording, same
required substrings, which is all the tests check).

For `build_trip_planner_agent()`, wrote instructions in the same style
used by the solutions of Labs 08, 09, and 10 — natural prose that
refers to "the tool" or "the gear-lookup tool" generically, without
spelling out the tool's exact Python function name. For example:

```
"You are Cascadia Outfitters' trip-planning assistant. When asked about "
"gear for a trail, use the gear-lookup tool to ground your recommendation "
"in the trail database instead of guessing."
```

## Where it diverged

`test_build_trip_planner_agent_instructions_mention_the_tool` asserts
`"suggest_gear_for_trail" in agent.default_options["instructions"]` —
the literal function name, verbatim, must appear in the instructions
string. The README's Step 1 only said "instructions telling it to
ground gear recommendations in the tool's output," which doesn't hint
that the literal identifier needs to appear. Every prior lab's solution
(08, 09, 10) refers to its tools generically in agent instructions
("Use the tools to look up real order data") and none of those tests
check for a literal tool name — so an attendee generalizing from that
precedent has no signal this lab is different.

The failure was easy to diagnose from the pytest assertion (it prints
the exact instructions string and what's missing), so this didn't
cause a real stall — one fix closed it. But it's a legitimate
README gap: nothing in Step 1 tells the attendee this lab's tests
enforce naming the tool literally, unlike every earlier lab.

## Judgment and fix applied

This warrants a debrief: a reasonable README-driven implementation,
consistent with the pattern established by three earlier labs, fails a
test the README gives no reason to expect. Fixed `README.md` Step 1 to
say explicitly: name the `suggest_gear_for_trail` tool by its exact
function name somewhere in the instructions text, and note why (it's
what tells the model which tool to call, and it's how the tests verify
wiring without a live model call).

No solution or test change was needed — the solution's own instructions
already name the tool this way; only the README was under-specified.

## Final state

`starter/trip_planner_agent.py` was restored to its original TODO-stub
form (no implementation logic retained). Only `README.md` was edited.
No changes were made to `solution/` or `tests/`, so no coverage re-run
was required for this lab.
