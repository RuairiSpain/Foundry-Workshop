# Lab 18 — Content Understanding

You'll extract structured fields from a receipt with Content
Understanding, validate the extraction, and add it to Lab 07's
knowledge base as a new source.

**Verified against:** `azure-ai-contentunderstanding` 1.2.0b3's schema-based
field extraction, as of writing this workshop. The real
`ContentUnderstandingClient` is a long-running-operation API
(`begin_analyze()`, returning a poller you wait on) — this lab's
`content_understanding_client.analyze()` simplifies that polling loop
to one synchronous call, the same simplification
`case-study/testing/foundry_mocks.py`'s `FakeContentUnderstandingClient`
documents.

## Prerequisites

- Lab 07 complete: `cascadia-foundry-iq` exists.

## Concept: Content Understanding vs. plain file search

Lab 06's file search finds and quotes text. It can't turn "Total:
$189.00" into a number you can compute with, or "Order: CO-10231" into
a field you can query by. Content Understanding extracts fields against
a schema you define — `order_id`, `customer_email`, `total_usd` — so the
output is structured data, not another block of text to search.

## Step 1: Define the extraction schema in the Portal

1. Open the Foundry Portal's **Content Understanding** view.
2. Create an analyzer named `cascadia-receipts` with the schema from
   `starter/content_understanding.py`'s `RECEIPT_SCHEMA`: `order_id`,
   `customer_email`, `total_usd`, `item_count`.
3. Upload `case-study/receipts-and-specs/receipt-CO-10231.txt` and run
   the analyzer.

**Expected output:** a structured result with `order_id: "CO-10231"`,
`customer_email: "maya@example.com"`, and `total_usd: 189.0`.

## Step 2: Implement the extraction and validation code

Open `starter/content_understanding.py`. Implement four functions:

1. `extract_receipt_fields()` — call
   `content_understanding_client.analyze()` with the file path and
   schema.
2. `validate_extraction()` — return the required fields that are
   missing or empty in the result.
3. `build_knowledge_base_source()` — wrap the extracted fields as a
   `{"type": "structured", "data": ...}` source.
4. `add_receipt_to_knowledge_base()` — validate first, raising
   `ValueError` naming the missing fields if incomplete, then add the
   source.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 7 passed.

## Step 3: Run it against your real project

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export FOUNDRY_IQ_KNOWLEDGE_BASE_ID="<your kb-... ID from Lab 07>"
python3 starter/content_understanding.py
```

**Expected output:** `Added receipt CO-10231 to the knowledge base.`

## Step 4: Ask a question only the new source can answer

In the Agents Playground, ask `cascadia-support` (from Lab 08):
`What did order CO-10231 total, and what's the return window?`

**Expected output:** an answer citing both `$189.00` (from the receipt
you just added) and the 60-day return window (from the original policy
document) — two different source types, one knowledge base.

## Where this fits

This is the last grounding-source lab — Labs 19 and 20 shift from "what
can an agent look up" to "what does an agent remember about a specific
customer across sessions," which a knowledge base doesn't do.
