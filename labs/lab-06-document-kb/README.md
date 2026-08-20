# Lab 06 — Document knowledge base

You'll upload two of Cascadia's policy documents, build a vector store
from them with file search, and compare a grounded answer against an
ungrounded one on the same question.

**Verified against:** Foundry Toolkit for VS Code, file search, as of
writing this workshop.

## Prerequisites

- Lab 03 complete.

## Step 1: Upload the documents in the Toolkit

1. In your project, open **Knowledge** → **Vector stores**.
2. Select **+ New vector store**, name it `cascadia-policy-kb`.
3. Upload `case-study/return-policy.md` and `case-study/store-manual.md`
   from the repo root.
4. Wait for both files to show **Indexed**.

## Step 2: Ask an ungrounded question in the Playground

1. Open **Model Playground** with your `cascadia-low-cost` deployment.
2. Ask: `Can I return a carabiner I already took out of its packaging?`

**Expected output:** a generic, hedging answer — the model has no
Cascadia-specific policy to draw on.

3. Attach `cascadia-policy-kb` as a tool and ask the same question
   again.

**Expected output:** a specific answer citing that climbing protection
is non-returnable once removed from packaging.

## Step 3: Implement the same comparison in code

Open `starter/knowledge_base.py`. Implement five functions:

1. `upload_documents()` — call `files_client.upload()` once per path.
   In `main()`, `files_client` is `AgentsClient.files` — file upload is
   an agents-client operation, not a project-client one.
2. `build_knowledge_base()` — collect the uploaded files' IDs and call
   `vector_stores_client.create()` (also `AgentsClient.vector_stores`).
3. `ask_grounded()` — call `chat_client.chat.completions.create()` with
   `tools=[{"type": "file_search"}]` and the vector store attached
   through `tool_resources`.
4. `ask_ungrounded()` — the same call with no tools.
5. `compare_grounding()` — call both and return a `GroundingComparison`.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 5 passed.

## Step 4: Run it against your real project

```bash
export LOW_COST_DEPLOYMENT=cascadia-low-cost
python3 starter/knowledge_base.py
```

**Expected output:** a `Grounded:` line and an `Ungrounded:` line, with
the grounded one citing the specific policy from step 2.

## Where this fits

Lab 07 replaces this vector store with a Foundry IQ knowledge base and
asks the same kind of comparison question, this time across multiple
data sources instead of two files. Lab 08's prompt agent attaches this
same knowledge base through Agent Builder instead of code.
