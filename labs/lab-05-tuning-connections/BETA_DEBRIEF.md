# Beta debrief — Lab 05 (Tuning model connections)

## What the simulated attendee did

Implemented all four functions from the README + starter TODOs alone,
without reading `solution/tuning.py` first:

1. `build_completion_kwargs()` — built the dict, included `seed` only
   when not `None`. Matched the solution exactly.
2. `call_with_params()` — built kwargs, called
   `chat_client.chat.completions.create()`, and built a `TunedReply`.
   First attempt read `response.usage.cached_tokens` for the
   `cached_tokens` field — the natural guess, since that's the exact
   name of the `TunedReply` field being populated.
3. `sweep_temperature()` and `check_prompt_caching()` — matched the
   solution exactly on the first attempt.

## Where it diverged

Running `LAB_TARGET=starter python3 -m pytest tests/ -v` failed 5 of 7
tests with:

```
AttributeError: 'FakeUsage' object has no attribute 'cached_tokens'
```

Neither the README nor the starter file's docstrings/TODOs say where
`cached_tokens` actually lives on the response object. The real
location — `response.usage.prompt_tokens_details.cached_tokens` — only
appears in `testing/foundry_mocks.py`'s module docstring and in a
docstring on the *solution* function itself, neither of which an
attendee reads before implementing. `usage.cached_tokens` (flat) is the
far more discoverable guess given the `TunedReply.cached_tokens` field
name, and it's wrong.

Recovering required opening `testing/foundry_mocks.py` to read
`FakeUsage`'s actual shape — a debugging step a novice could plausibly
take (the fixture is right there in the repo and the test file already
imports from it), but one the README gives no hint is necessary. This
is a real README/starter gap, not implementation difficulty.

Separately, README Step 1 item 2 says to "call `chat_client.complete()`",
but the actual method — used consistently by every other lab in this
module (03, 04) and by the starter file's own TODO comment two lines
below — is `chat_client.chat.completions.create()`. `chat_client` (the
`openai.OpenAI`-shaped object) has no `.complete()` method at all. An
attendee following the README's prose literally over the starter's TODO
comment would hit an `AttributeError` immediately.

## Judgment

Both are genuine README/starter gaps worth fixing:

- The `chat_client.complete()` line is an outright wrong method name —
  inconsistent with this same lab's own starter file and every prior
  lab.
- The `cached_tokens` location is a real "how would you even know"
  gap: it's not derivable from Lab 03/04 (which never touch `usage` at
  all beyond `total_tokens`), and the one place it's documented
  (`testing/foundry_mocks.py`'s docstring) isn't referenced from the
  README or starter file.

No bug in `solution/tuning.py` itself — its behavior is correct and
matches a good-faith README-driven implementation once the two gaps
above are resolved.

## Fix applied

- README Step 1, item 2: replaced "call `chat_client.complete()`" with
  "call `chat_client.chat.completions.create()`", matching the actual
  method and the starter file's own TODO comment.
- `starter/tuning.py`'s `call_with_params()` TODO comment: added a line
  naming the exact field path for cached tokens —
  `response.usage.prompt_tokens_details.cached_tokens` (not
  `response.usage.cached_tokens`) — so attendees don't have to
  reverse-engineer it from the test fixtures.
- No changes to `solution/tuning.py` or `tests/test_tuning.py`.
