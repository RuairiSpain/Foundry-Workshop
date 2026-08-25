# Lab 02 — Provision by code

This lab is an alternate path to Lab 01: the same outcome — your own
project under the instructor's hub — done with the Azure CLI and a
notebook instead of the Toolkit UI. Use it if your organization's policy
blocks extension-driven resource creation, or if you'd rather see the
commands directly.

**Verified against:** Azure CLI 2.75, as of writing this workshop.

## Prerequisites

- Azure CLI installed (`az version` should print 2.70 or later).
- The same **Azure AI Developer** grant on the hub resource group that
  Lab 01 requires.
- Jupyter installed (included in `requirements.txt`).

## Step 1: Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Implement the command builders

Open `starter/provisioning.py`. Implement two functions:

1. `build_project_create_command()` — return the argument list for
   `az cognitiveservices account project create`, targeting the
   instructor's existing hub. Don't include an `account create` step —
   the hub already exists.
2. `parse_project_endpoint()` — parse the JSON from
   `az ... project show` and return `properties.endpoint`. Re-raise
   `KeyError` with the raw payload attached if the field is missing.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 5 passed.

## Step 3: Run the notebook

```bash
jupyter notebook starter/provision_project.ipynb
```

Set `ATTENDEE_ID`, `ACCOUNT_NAME`, and `RESOURCE_GROUP` in the first code
cell to the values your instructor gave you, then run each cell in
order.

**Expected output after the "create your project" cell:** a JSON object
with `"name": "proj-<your-attendee-id>"`.

**Expected output after the "read back your endpoint" cell:** a line
starting with `FOUNDRY_PROJECT_ENDPOINT=`.

## Step 4: Verify the connection

Follow the notebook's last cell: export the endpoint, then run Lab 01's
`verify_setup.py` against it. Reusing that script instead of writing a
new one is deliberate — Lab 01 and Lab 02 produce the same kind of
project, so they share the same verification step.

**Expected output:** `Connected. Hub replied: 'ready'`

## Where this fits

You now have two ways to reach the same starting point Lab 01 leaves you
at. Every lab from here on assumes that starting point — it doesn't
matter which of the two labs got you there.
