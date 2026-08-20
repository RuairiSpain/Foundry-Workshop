# Beta debrief — Lab 25 (A2A)

## What the simulated attendee did

Implemented `estimate_shipping_eta()` in `starter/swiftship_server.py`
exactly per the README/docstring: raise `ValueError` for an unknown
zone, return the same zone's ETA for a same-zone shipment, and the
`"national"` ETA otherwise. All 4 `test_swiftship_server.py` tests
passed on the first try — no issues here.

In `starter/trip_planner_client.py`, implemented `build_swiftship_client()`
as an `A2AAgent(name="swiftship", url=url, description=...)`, then
`build_trip_planner_with_swiftship()` as `Agent(client, tools=[swiftship.as_tool()])`
with a generic instructions string ("Answer trip-planning questions.") —
the README's Step 2 says nothing about what the instructions should
contain, only that the function should "build the SwiftShip client,
then return a Trip Planner `Agent` with `tools=[swiftship.as_tool()]`."

## Where it diverged

`test_build_trip_planner_with_swiftship_instructions_mention_delegating`
failed:

```
AssertionError: assert 'delegate' in 'answer trip-planning questions.'
```

The test requires the Trip Planner's `instructions` string to contain
the word "delegate" (case-insensitive). Nothing in the README or the
starter docstring says the instructions need to mention delegation —
Step 2 only calls out the two functions to implement and the
`tools=[swiftship.as_tool()]` requirement. A first-time attendee
reading only the README has no way to know this test exists or what
substring it checks for; the fix is easy once you see the pytest
failure, but it's a guess-the-test moment, not a follow-the-doc one.

## Judgment

This is a real README gap, not attendee error. `.as_tool()` alone
correctly wires the tool, but MAF agents don't use tools they aren't
told about — the pedagogically correct behavior is for the README to
say so explicitly, and that's also what the test is actually checking
for (that the lab teaches "tell the agent to delegate," not just
"attach the tool").

## Fix applied

- `README.md` Step 2: added a sentence telling the attendee to give
  the Trip Planner `instructions` that explicitly say to delegate
  shipping-ETA questions to the `swiftship` tool.
- `starter/trip_planner_client.py`: extended the TODO comment on
  `build_trip_planner_with_swiftship()` to mention the same
  requirement (comment/docstring wording only — the `raise
  NotImplementedError` stub was restored unchanged).
- No changes to `solution/` or `tests/` — the solution's instructions
  string already satisfies the test; only the README/starter were
  under-specifying it.

## Coverage

Not applicable — `solution/` and `tests/` were not modified for this
lab.
