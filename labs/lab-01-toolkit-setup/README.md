# Lab 01 — Meet the Toolkit

You'll install the Foundry Toolkit extension, sign in to Azure, and
create your own Foundry project under the instructor's shared hub. You
finish by writing a script that proves your project can reach the hub's
shared model.

**Verified against:** Foundry Toolkit for VS Code (`ms-windows-ai-studio.windows-ai-studio`),
`azure-ai-projects` 2.3.0, as of writing this workshop. If an
extension screen looks different from this README, the extension has
likely shipped an update — ask your instructor.

## Prerequisites

- VS Code installed.
- An Azure AD account with **Azure AI Developer** granted on the
  instructor's hub resource group. Ask your instructor if you don't have
  this yet — Lab 01 doesn't work without it.
- Python 3.11 or later.

## Step 1: Install the Foundry Toolkit extension

1. Open VS Code.
2. Open the Extensions view (`Ctrl+Shift+X` / `Cmd+Shift+X`).
3. Search for **Foundry Toolkit** and select **Install**.

When the install finishes, a new Foundry icon appears in the VS Code
activity bar.

## Step 2: Sign in to Azure

1. Select the Azure icon in the VS Code activity bar.
2. Select **Sign in to Azure...** and complete the browser sign-in flow.
3. In the Azure Resources view, confirm your subscription is listed.

If your subscription doesn't appear, select **Select Subscriptions** and
enable it.

## Step 3: Create your project under the hub

1. Select the Foundry icon in the activity bar.
2. In **My Resources**, select **+ Create Project**.
3. When asked for a resource group, select **use an existing one** and
   choose the resource group your instructor gave you — this is the hub
   resource group, not a new one.
4. Name your project `proj-<your-attendee-id>` — ask your instructor for
   your attendee ID if you don't have it.
5. Select **Create**.

Creation takes under a minute, since you're attaching to an existing
hub instead of provisioning one. When it finishes, your project appears
under **My Resources**.

## Step 4: Get your project's endpoint

1. In **My Resources**, select your new project.
2. Open the **Overview** page.
3. Copy the **Project endpoint** value.

## Step 5: Set up the verification script

1. Open a terminal in this lab's folder.
2. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Export your project endpoint from step 4:

   ```bash
   export FOUNDRY_PROJECT_ENDPOINT="<paste the endpoint here>"
   ```

## Step 6: Implement the connectivity check

Open `starter/verify_setup.py`. Implement `check_connection()`:

1. Get the OpenAI-shaped client with `client.get_openai_client()` —
   Foundry's chat completions go through the `openai.OpenAI` client
   shape, not a Foundry-specific one.
2. Send one message asking the model to reply with the word "ready",
   using the `deployment_name` argument as the model, via
   `chat_client.chat.completions.create()`.
3. If the call fails, raise `SetupCheckError` with a hint, using
   `raise ... from exc` so the original error is still visible.
4. Return the reply text.

Run the tests to check your work:

```bash
python3 -m pytest tests/ -v
```

**Expected output:** 3 passed.

## Step 7: Run it against your real project

```bash
python3 starter/verify_setup.py
```

**Expected output:**

```
Connected. Hub replied: 'ready'
```

If you see a `SetupCheckError` instead, re-read its message — it names
the two most common causes: a missing hub deployment, or an RBAC grant
that hasn't propagated yet. Wait two minutes and try again before asking
your instructor.

## Where this fits

Every later lab assumes your project exists and can reach the hub. Lab
02 shows the same setup done from the CLI instead of the Toolkit. Lab 03
has you deploy a model into this same project for the first time.
