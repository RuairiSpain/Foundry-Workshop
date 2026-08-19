# Lab 08 — Prompt agent

You'll build Cascadia's first agent — a no-code, fully managed prompt
agent — in Agent Builder, attach Lab 07's knowledge base to it, and
verify it with a script.

**Verified against:** Foundry Toolkit for VS Code, Agent Builder, as of
writing this workshop.

## Prerequisites

- Lab 07 complete: `cascadia-foundry-iq` exists.

## Step 1: Build the agent in Agent Builder

1. In the Foundry Toolkit, open **Agent Builder**.
2. Select **New agent** → **Prompt agent**.
3. Name it `cascadia-support`.
4. Set instructions:

   ```
   You are Cascadia Outfitters' customer support assistant. Answer
   questions about returns, store policy, and products using the
   attached knowledge base. If you don't know, say so — don't guess.
   ```

5. Under **Knowledge**, attach `cascadia-foundry-iq`.
6. Select **Save**.

## Step 2: Test it in the Agents Playground

1. Open the **Agents Playground** for `cascadia-support`.
2. Ask: `What is your return window?`

**Expected output:** an answer mentioning 60 days, citing the return
policy.

3. Copy the agent's ID from the Playground's **Details** panel — you'll
   need it in step 4.

## Step 3: Implement the verification script

Open `starter/verify_prompt_agent.py`. Implement two functions:

1. `ask_agent()` — create a thread, add a user message, process a run,
   and return the last message's content.
2. `check_grounded_reply()` — call `ask_agent()`, and raise
   `AgentCheckError` with a hint if the reply doesn't mention the
   expected phrase, case-insensitively.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 5 passed.

## Step 4: Run it against your real agent

```bash
export PROMPT_AGENT_ID="<paste the agent ID from step 2>"
python3 starter/verify_prompt_agent.py
```

**Expected output:**

```
Agent replied: You have 60 days to return unused gear...
```

## Where this fits

`ask_agent()`'s create-thread → message → run → read-messages sequence
is the same one Lab 09's classic agent uses, extended with function
tools and multi-turn state. Lab 13's web-grounded agent builds on this
same prompt agent, adding the web search tool alongside the knowledge
base.
