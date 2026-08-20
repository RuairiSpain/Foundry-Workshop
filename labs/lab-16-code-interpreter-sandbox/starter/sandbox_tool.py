"""Wraps a self-hosted, subprocess-isolated code sandbox as a custom
tool, and contrasts it with Foundry's managed Code Interpreter.
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
    """Runs `code` in a separate Python process with a hard timeout."""
    # TODO(lab-16): call subprocess.run() with [sys.executable, "-c", code],
    # capture_output=True, text=True, timeout=timeout. Catch
    # subprocess.TimeoutExpired and return a SandboxResult with
    # timed_out=True. Otherwise return a SandboxResult from the
    # completed process's stdout, stderr, and returncode.
    raise NotImplementedError("run_in_sandbox is not implemented yet")


def execute_tool(tool_name: str, args: dict) -> dict:
    """Dispatches the sandbox tool call to run_in_sandbox()."""
    # TODO(lab-16): if tool_name == "run_python_in_sandbox", call
    # run_in_sandbox(args["code"]) and return a dict with stdout, stderr,
    # and succeeded. Otherwise raise ValueError.
    raise NotImplementedError("execute_tool is not implemented yet")


def build_pack_weight_agent(agents_client, *, model: str):
    """Builds an agent with both Code Interpreter and the sandbox tool."""
    # TODO(lab-16): call agents_client.create_agent() with model, a name,
    # instructions, and tools=[CODE_INTERPRETER_TOOL, SANDBOX_TOOL].
    raise NotImplementedError("build_pack_weight_agent is not implemented yet")


def main() -> None:
    result = run_in_sandbox("print(sum([3.2, 1.1, 0.9, 2.0]))")
    print(f"Sandbox stdout: {result.stdout.strip()}")
    print(f"Succeeded: {result.succeeded}")


if __name__ == "__main__":
    main()
