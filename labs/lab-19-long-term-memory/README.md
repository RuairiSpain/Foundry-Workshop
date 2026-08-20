# Lab 19 — Long-term memory

You'll turn on Foundry's native long-term agent memory for the support
assistant, so a fact Maya mentions in one conversation is still known in
a completely separate one.

**Verified against:** Foundry Agent Service native memory (preview), as
of writing this workshop.

## Prerequisites

- Lab 08 complete: `cascadia-support` exists.

## Concept: memory vs. thread state

Lab 09's threads gave an agent state within one conversation — turn 2
could refer back to turn 1 because they shared a thread. Long-term
memory is different: it persists facts *across* threads, tied to a
user rather than a conversation. A brand-new thread, with zero prior
messages, can still know a fact from last week.

## Step 1: Enable memory in the Portal

1. Open `cascadia-support` in the Foundry Portal.
2. Under **Memory**, enable long-term memory for the agent.
3. In the Agents Playground, start a thread and say: `I wear women's
   size 8 boots.`
4. Start a **new** thread (not a new message in the same one) and ask:
   `What boot size should I order?`

**Expected output:** the agent answers "size 8" in the new thread,
without you repeating it — memory carried the fact across, thread state
alone couldn't have.

## Step 2: Implement the same flow in code

Open `starter/native_memory.py`. Implement three functions:

1. `remember_preference()` — call `memory_client.remember()`.
2. `recall_preferences()` — call `memory_client.recall()` and return it.
3. `ask_with_memory()` — create a thread, recall facts and fold them
   into the user's message if any exist (a thread message is only
   `user` or `assistant` — there's no `system` role to carry them
   separately), process a run, and return the reply.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 5 passed.

## Step 3: Run it against your real project

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export PROMPT_AGENT_ID="<your agent ID from Lab 08>"
python3 starter/native_memory.py
```

**Expected output:** a reply recommending the women's size 8 boot,
grounded in the fact you just remembered rather than in anything the
question itself said.

## Where this fits

Lab 20 swaps this managed memory store for your own Cosmos DB container,
when you need direct control over where and how long customer facts are
kept — data residency and retention are yours to set, not Foundry's.
