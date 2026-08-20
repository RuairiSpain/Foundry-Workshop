"""Wraps a self-hosted, subprocess-isolated code sandbox as a custom
tool, and contrasts it with Foundry's managed Code Interpreter.

This sandbox is deliberately minimal — a timeout-bound subprocess, not a
container. A production self-hosted sandbox would add real isolation (a
container, a restricted user, no network) on top of the same idea; see
README.md for what to add before trusting it with real traffic.
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys

CODE_INTERPRETER_TOOL = {"type": "code_interpreter"}

SANDBOX_TOOL = {
    "type": "function",
    "function": {
        "name": "run_python_in_sandbox",
        "description": "Run a short Python snippet and return its stdout. No file or network access.",
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python source to execute."}},
            "required": ["code"],
        },
    },
}


@dataclasses.dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool

    @property
    def succeeded(self) -> bool:
        return not self.timed_out and self.exit_code == 0


def run_in_sandbox(code: str, *, timeout: float = 5.0) -> SandboxResult:
    """Runs `code` in a separate Python process with a hard timeout.

    A subprocess, not exec()/eval() in this process, is the minimum
    viable isolation: a crash or infinite loop in the snippet can't take
    down the calling process, and the timeout guarantees control returns
    either way.
    """
    try:
        completed = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return SandboxResult(stdout=exc.stdout or "", stderr=exc.stderr or "", exit_code=-1, timed_out=True)
    return SandboxResult(
        stdout=completed.stdout, stderr=completed.stderr, exit_code=completed.returncode, timed_out=False
    )


def execute_tool(tool_name: str, args: dict) -> dict:
    """Dispatches the sandbox tool call to run_in_sandbox()."""
    if tool_name == "run_python_in_sandbox":
        result = run_in_sandbox(args["code"])
        return {"stdout": result.stdout, "stderr": result.stderr, "succeeded": result.succeeded}
    raise ValueError(f"Unknown tool: {tool_name}")


def build_pack_weight_agent(agents_client, *, model: str):
    """Builds an agent with both Code Interpreter and the sandbox tool,
    so the same "compute this trip's pack weight" question can be asked
    of each and compared.
    """
    return agents_client.create_agent(
        model=model,
        name="cascadia-pack-calculator",
        instructions=(
            "You help hikers compute total pack weight. Use a tool to run "
            "the arithmetic — never do the math yourself."
        ),
        tools=[CODE_INTERPRETER_TOOL, SANDBOX_TOOL],
    )


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    result = run_in_sandbox("print(sum([3.2, 1.1, 0.9, 2.0]))")
    print(f"Sandbox stdout: {result.stdout.strip()}")
    print(f"Succeeded: {result.succeeded}")


if __name__ == "__main__":  # pragma: no cover
    main()
