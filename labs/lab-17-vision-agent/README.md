# Lab 17 — Vision-enabled agent

You'll build a multimodal message from a damaged-gear photo and send it
to a vision-capable deployment, so a return request gets triaged from
the photo directly instead of a written description of it.

**Verified against:** `azure-ai-projects` 1.0.0b12, multimodal chat
completions, as of writing this workshop.

## Prerequisites

- Lab 03 complete.
- A vision-capable model deployed as `cascadia-vision` (ask your
  instructor if this isn't already on the hub).

## Concept: how an image gets into a chat message

Every prior lab's messages used `content` as a plain string. A
multimodal message uses a list instead — one part for text, one part
for the image, as a `data:` URL with the image base64-encoded inline.
That list shape is what tells the model to actually look at the image,
not just read a description of it.

## Step 1: Implement the message builder

Open `starter/vision_return_triage.py`. Implement four functions:

1. `encode_image_base64()` — read the file's bytes and base64-encode
   them.
2. `build_image_data_url()` — guess the MIME type from the filename,
   falling back to `application/octet-stream`, and build the
   `data:mime;base64,...` URL.
3. `build_vision_message()` — a `user` message with a text part and an
   image part.
4. `assess_damaged_item()` — build the message, call
   `chat_client.complete()`, and return a `DamageAssessment`.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 6 passed.

## Step 2: Run it against the real sample photo

```bash
export VISION_DEPLOYMENT=cascadia-vision
python3 starter/vision_return_triage.py
```

**Expected output:** a description of visible damage and a suggested
return category. The sample photo
(`case-study/damaged-gear-photos/tent-pole-break.png`) is a small
synthetic image, not a real photo — good enough to prove the multimodal
call works, not to test image understanding quality.

## Step 3: Try it in the Playground with a real photo

1. Open **Model Playground** with `cascadia-vision`.
2. Attach any photo of damaged gear (or a stand-in object).
3. Ask the same question as step 2.

**Expected output:** a specific description referencing what's actually
in your photo, not a generic answer — confirming the model is looking at
the image, not guessing from the question text alone.

## Where this fits

Lab 18's Content Understanding lab processes a different kind of image —
receipts and spec sheets — for structured field extraction rather than
a free-text assessment like this one.
