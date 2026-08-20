# Beta debrief — Lab 13: Web-grounded agent

## What the simulated attendee did

Implemented both `build_concierge_agent()` and `ask_concierge()` directly
from the README's Step 1 instructions and the starter file's docstrings:

- `build_concierge_agent()`: called `agents_client.create_agent()` with
  `model`, a `name`, `instructions`, `tools=[build_web_search_tool(...),
  KNOWLEDGE_BASE_TOOL, TOOLBOX_TOOL]`, and
  `tool_resources=_tool_resources(knowledge_base_id)`.
- `ask_concierge()`: created a thread, added a user message, called
  `runs.create_and_process()`, and returned
  `messages.list(thread.id, order="asc")[-1].content`.

Ran `LAB_TARGET=starter python3 -m pytest tests/ -v` as instructed.

## Result vs. solution

Behavior matches the reference solution exactly — same API calls, same
argument shapes, same tool list and `tool_resources`. Only cosmetic
differences (agent `name` string, `instructions` wording), which the
grading tests correctly don't check.

## Divergence found

The tests passed, but the README's "Expected output" was wrong: it says

> **Expected output:** 4 passed.

`tests/test_concierge_agent.py` actually has 5 test functions, and the
real run reports `5 passed`. A real attendee who counts test names in the
`-v` output against the README's stated number would see a mismatch on
their very first lab step and could reasonably wonder if something is
broken, even though nothing is.

## Judgment and fix applied

This is a genuine README bug (stale count, likely left over from an
earlier revision of the test file), not a starter/solution issue. Fixed
`README.md`'s Step 1 to say "5 passed", matching the actual test file.

No other issues found. `starter/concierge_agent.py` was restored to its
original TODO-stub form after this fix.
