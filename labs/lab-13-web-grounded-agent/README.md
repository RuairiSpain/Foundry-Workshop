# Lab 13 — Web-grounded agent

You'll build Cascadia's trail concierge: one agent with three grounding
sources at once — live web search, the Foundry IQ knowledge base, and
the Lab 11 loyalty tool from the Toolbox.

**Verified against:** Foundry Toolkit for VS Code, web search tool, as
of writing this workshop.

## Prerequisites

- Lab 07 complete: `cascadia-foundry-iq` exists.
- Lab 11 complete: `cascadia-loyalty` is registered in the Toolbox.

## Step 1: Implement the agent

Open `starter/concierge_agent.py`. Implement two functions:

1. `build_concierge_agent()` — call `agents_client.create_agent()` with
   all three tools (`WEB_SEARCH_TOOL`, `KNOWLEDGE_BASE_TOOL`,
   `TOOLBOX_TOOL`, already defined in the file) and the knowledge base
   attached through `tool_resources`.
2. `ask_concierge()` — create a thread, add a user message, process a
   run, and return the last message's content. The same shape as Lab
   08's `ask_agent()`, written fresh here since each lab stays
   self-contained.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 4 passed.

## Step 2: Run it against your real project

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export FOUNDRY_IQ_KNOWLEDGE_BASE_ID="<your kb-... ID from Lab 07>"
python3 starter/concierge_agent.py
```

**Expected output:** a reply about current conditions on Skyline
Divide — the model had to reach for web search, since trail conditions
aren't in the knowledge base or the loyalty tool.

## Step 3: Watch tool selection in the trace

1. Open the Foundry Portal's **Tracing** view for the run.
2. Find the trace and open its tool-call sequence.

**Expected output:** exactly one tool call, to web search — the model
chose not to call the knowledge base or loyalty tools for this
question, because neither one could answer it.

3. Ask a second question that needs two tools at once: `What's my
   loyalty balance, and is the return policy the same for
   maya@example.com?` Re-check the trace.

**Expected output:** two tool calls this time — loyalty lookup and
knowledge base retrieval — in the same run.

## Where this fits

This is the most capable single agent in the workshop — the last lab
that makes an agent stronger by adding another tool to it. Module 6
picks up a harder question instead: when should this be several agents
working together, rather than one agent with more tools?
