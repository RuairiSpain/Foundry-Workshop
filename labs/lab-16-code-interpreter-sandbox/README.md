# Lab 16 — Code Interpreter and open-source sandbox

You'll use Foundry's managed Code Interpreter for a pack-weight
calculation, then wrap your own subprocess-isolated sandbox as a custom
tool and compare the two.

**Verified against:** Python 3.11 `subprocess`, no external sandbox
dependency, as of writing this workshop.

## Prerequisites

- Lab 09 complete.

## Step 1: Try the managed Code Interpreter

1. Open **Model Playground** with your `cascadia-low-cost` deployment.
2. Enable the **Code Interpreter** tool.
3. Ask: `A tent weighs 3.2 kg, boots weigh 1.1 kg, a stove weighs 0.9
   kg, and a rain shell weighs 0.4 kg. What's the total pack weight?`

**Expected output:** a reply with `5.6` kg, and a visible code block
showing the arithmetic Code Interpreter ran to get there.

## Step 2: Implement your own sandbox

Open `starter/sandbox_tool.py`. Implement three functions:

1. `run_in_sandbox()` — run `code` with `subprocess.run()`, capturing
   stdout and stderr, with a hard timeout. Catch
   `subprocess.TimeoutExpired` and return a timed-out result instead of
   letting the exception propagate.
2. `execute_tool()` — dispatch `"run_python_in_sandbox"` to
   `run_in_sandbox()`.
3. `build_pack_weight_agent()` — an agent with both
   `CODE_INTERPRETER_TOOL` and `SANDBOX_TOOL` attached.

Run the tests to check your work:

```bash
LAB_TARGET=starter python3 -m pytest tests/ -v
```

**Expected output:** 6 passed. Two of these tests spawn a real
subprocess — nothing here is mocked, since the sandbox is your own code,
not a Foundry SDK call.

## Step 3: Run it directly

```bash
python3 starter/sandbox_tool.py
```

**Expected output:** `Sandbox stdout: 7.200000000000001` and
`Succeeded: True` — floating-point addition, not a bug in your code.

## Step 4: Know what this sandbox doesn't do

This is the minimum viable isolation — a timeout and a separate
process — not production security. It still runs on the same machine,
with the same filesystem and network access as everything else. A real
self-hosted sandbox adds, at minimum: a container or VM boundary, a
restricted user, no network access, and a memory limit. Foundry's
managed Code Interpreter gives you that isolation for free; this lab's
sandbox trades it for full control over the runtime and its
dependencies.

## Where this fits

Lab 21 revisits tool design again in Microsoft Agent Framework, where a
plain Python function becomes a tool automatically — no `SANDBOX_TOOL`
dict to write by hand.
