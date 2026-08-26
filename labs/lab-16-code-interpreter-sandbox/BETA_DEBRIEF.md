# Beta debrief — Lab 16: Code Interpreter and open-source sandbox

## What the simulated attendee did

Implemented all three TODOs directly from the README's Step 2 instructions
and the starter docstrings:

- `run_in_sandbox()`: `subprocess.run([sys.executable, "-c", code],
  capture_output=True, text=True, timeout=timeout)`, with a
  `subprocess.TimeoutExpired` catch returning `timed_out=True`.
- `execute_tool()`: dispatched `"run_python_in_sandbox"` to
  `run_in_sandbox()`, otherwise raised `ValueError`.
- `build_pack_weight_agent()`: `agents_client.create_agent()` with
  `tools=[CODE_INTERPRETER_TOOL, SANDBOX_TOOL]`.

Ran `LAB_TARGET=starter python3 -m pytest tests/ -v` (6 passed, matches
README) and then `python3 starter/sandbox_tool.py` for Step 3.

## Result vs. solution

Behavior matches the reference solution. One cosmetic difference: on a
timeout, the solution preserves `exc.stdout`/`exc.stderr` from the
partially-run process (`SandboxResult(stdout=exc.stdout or "", ...)`), and
my from-README attempt returns empty strings instead. The tests only
assert `timed_out is True` and `succeeded is False` on that path, so
both pass — this difference isn't visible to the grading harness, and
the README/docstring TODO doesn't ask for exc.stdout handling
specifically ("Catch subprocess.TimeoutExpired and return a timed-out
result"). Leaving this as a stylistic solution detail, not a defect.

## Divergence found

Step 3's expected output is wrong:

> **Expected output:** `Sandbox stdout: 7.2` and `Succeeded: True`.

`main()` runs `print(sum([3.2, 1.1, 0.9, 2.0]))` in the subprocess. In
real Python floating-point arithmetic this is not exactly `7.2`:

```
>>> sum([3.2, 1.1, 0.9, 2.0])
7.200000000000001
```

Running `python3 starter/sandbox_tool.py` (with the TODOs filled in, same
code as `solution/`) prints `Sandbox stdout: 7.200000000000001`, not
`7.2`. This is deterministic, not "your exact numbers will vary" — every
attendee who completes the lab correctly sees `7.200000000000001` and
would reasonably suspect their sandbox implementation is subtly broken
when it isn't.

## Judgment and fix applied

Genuine README bug (unlike Step 3 of Lab 14, which explicitly warns
numbers vary, this step gives a single expected value with no such
caveat). Fixed `README.md`'s Step 3 to state the real output value and
note that it's floating-point behavior, not a bug to chase.

Did not touch `solution/sandbox_tool.py` or the test file — no
grading-visible bug, and the sum-as-is is fine pedagogically (it's the
same arithmetic Code Interpreter is asked to do in Step 1, so keeping the
inputs identical is intentional).

`starter/sandbox_tool.py` was restored to its original TODO-stub form
after this fix.
