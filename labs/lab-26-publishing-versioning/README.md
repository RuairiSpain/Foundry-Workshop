# Lab 26 — Publishing and versioning

You'll publish `cascadia-support` as a Foundry Agent Application, watch
a second version snapshot automatically, split traffic between the two,
and roll back.

**Verified against:** Foundry Portal, Agent Applications, as of writing
this workshop.

## Prerequisites

- Lab 08 complete: `cascadia-support` exists.

## Step 1: Publish the first version in the Portal

1. Open `cascadia-support` in the Foundry Portal.
2. Select **Publish** → **New Agent Application**.
3. Name it `cascadia-support-app`.

**Expected output:** an Agent Application with one version, receiving
100% of traffic.

## Step 2: Implement the same flow in code

Open `starter/publishing.py`. Implement four functions:

1. `publish_first_version()` — call
   `agent_applications_client.create()`.
2. `publish_new_version()` — call
   `agent_applications_client.publish_version()`.
3. `canary_traffic_split()` — build a split dict giving the stable
   version `100 - canary_percent` and the canary version
   `canary_percent`, and call `set_traffic_split()`.
4. `rollback_to_version()` — call `agent_applications_client.rollback(app_id, to_version=version)`.
   The client's keyword is `to_version`, not `version` — don't assume it
   matches this function's own parameter name.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 6 passed.

## Step 3: Publish a change and canary it for real

1. Edit `cascadia-support`'s instructions slightly in the Portal.
2. Run `starter/publishing.py` against your real project:

```bash
export FOUNDRY_PROJECT_ENDPOINT="<your project endpoint>"
export PROMPT_AGENT_ID="<your agent ID>"
python3 starter/publishing.py
```

**Expected output:**

```
Published cascadia-support-app as app-0001, version 1.
Version 2 live at 10% traffic.
```

3. In the Portal, confirm the Agent Application shows two versions,
   with version 2 at 10% traffic and version 1 still serving the rest.

## Step 4: Roll back

If version 2 looked wrong, `rollback_to_version()` sends 100% of
traffic straight back to version 1 — no redeploy, since both versions
already exist.

## Where this fits

Lab 27 wires `canary_traffic_split()`'s constraints into a CI/CD gate:
a version that fails evaluation never gets traffic in the first place,
instead of you catching it after a canary rollout.
