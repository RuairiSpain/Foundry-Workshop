# Beta debrief — Lab 17: Vision-enabled agent

## What the simulated attendee did

Implemented all four TODOs from the README's Step 1 and the starter
file's docstrings:

- `encode_image_base64()`: `base64.b64encode(path.read_bytes()).decode("ascii")`.
- `build_image_data_url()`: `mimetypes.guess_type()` with a fallback to
  `"application/octet-stream"`, building `f"data:{mime_type};base64,{encoded}"`.
- `build_vision_message()`: a `user` message with a text part and an
  `image_url` part.
- `assess_damaged_item()`: built the message, called
  `chat_client.chat.completions.create(model=deployment_name,
  messages=[message])`, and returned a `DamageAssessment`.

Ran `LAB_TARGET=starter python3 -m pytest tests/ -v` (6 passed, matches
README).

## Result vs. solution

Behavior matches the reference solution exactly.

## Divergence found

The README's Step 1 instructions for `assess_damaged_item()` say:

> `assess_damaged_item()` — build the message, call
> `chat_client.complete()`, and return a `DamageAssessment`.

But `chat_client` here is what `AIProjectClient.get_openai_client()`
returns — an OpenAI-shaped client (`FakeOpenAIClient` in tests, the real
`openai.OpenAI` client in production) — which has no `.complete()`
method at all. The starter file's own docstring/TODO comment on
`assess_damaged_item()` already says the right thing
(`chat_client.chat.completions.create()`), and that's the call every
earlier lab in this workshop uses through the same client (Labs 05, 14,
15). An attendee who trusts the README bullet literally over the
starter's own TODO comment would write `chat_client.complete(...)`,
which raises `AttributeError: 'FakeOpenAIClient' object has no attribute
'complete'` the moment `tests/test_assess_damaged_item_*` run — a
confusing failure with no clue in the traceback pointing back to the
README as the source of the bad guess.

This looks like a leftover reference to the separate
`azure-ai-inference` `ChatCompletionsClient.complete()` API (a different,
non-OpenAI-shaped Azure SDK client this workshop doesn't use), stale from
an earlier draft of this lab.

## Judgment and fix applied

Genuine README bug — self-contradicts the starter file it's describing.
Fixed `README.md`'s Step 1, bullet 4, to say
`chat_client.chat.completions.create()`, matching the starter's TODO
comment, the test suite, and the reference solution.

`starter/vision_return_triage.py` was restored to its original TODO-stub
form after this fix.
