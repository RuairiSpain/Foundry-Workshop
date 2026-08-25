# Lab 07 — Foundry IQ knowledge base

You'll build a Foundry IQ knowledge base spanning Cascadia's policy
documents and its product catalog, then compare its answer against Lab
06's single-source file search on a question that needs both.

**Verified against:** Foundry IQ knowledge bases (GA) and Foundry IQ
Serverless (public preview), as of writing this workshop. Neither has a
stable typed Python SDK yet — a real call goes through
`AIProjectClient.send_request()` against the REST surface, which
`create_knowledge_base()`'s `knowledge_bases_client` argument stands in
for. File upload and vector store creation, by contrast, are the real,
typed `azure-ai-agents` 1.1.0 `AgentsClient`.

## Prerequisites

- Lab 06 complete: you know the file-search call shape this lab
  compares against.

## Step 1: Create the knowledge base in the Portal

1. Open the Foundry Portal for your project.
2. Under **Knowledge**, select **+ New knowledge base**.
3. Name it `cascadia-foundry-iq`.
4. Add two sources:
   - The two files from Lab 06 (`return-policy.md`, `store-manual.md`).
   - `case-study/product-catalog.csv` as a structured source.
5. Wait for the status to show **Ready**.

This is the difference from Lab 06 in one step: file search only ever
indexes files. Foundry IQ unifies file and structured sources behind one
retrieval endpoint.

## Step 2: Ask the multi-source question in the Playground

Ask: `What's the price of the 2-person trail tent, and can I return it
within 60 days if it doesn't fit my pack?`

**Expected output:** an answer with both the price (from the catalog)
and the return window (from the policy doc). File search alone, from
Lab 06, can only answer the return-window half.

## Step 3: Implement the comparison in code

Open `starter/foundry_iq.py`. Implement three functions:

1. `build_sources()` — combine uploaded files and structured paths into
   one source list.
2. `ask_knowledge_base()` — call `chat_client.chat.completions.create()`
   with `tools=[{"type": "knowledge_base"}]` and the knowledge base
   attached through `tool_resources`.
3. `compare_retrieval()` — call `ask_file_search()` and
   `ask_knowledge_base()`, and return a `RetrievalComparison`.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 5 passed.

## Step 4: Run it against your real project

```bash
export LOW_COST_DEPLOYMENT=cascadia-low-cost
python3 starter/foundry_iq.py
```

**Expected output:** two lines. The `File search:` line is missing the
price. The `Foundry IQ:` line has both the price and the return window.

## Where this fits

Lab 08's prompt agent attaches this knowledge base the same way it
attached Lab 06's vector store — through Agent Builder, no code needed.
Lab 18 comes back to this knowledge base and adds Content Understanding
output as a third source.
