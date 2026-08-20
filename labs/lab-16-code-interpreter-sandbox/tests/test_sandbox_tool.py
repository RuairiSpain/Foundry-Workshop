"""Tests for solution/sandbox_tool.py.

main() is excluded from coverage — it's the same run_in_sandbox() call
already covered below, wrapped as a CLI entry point.

These tests spawn real subprocesses — nothing about the sandbox itself
is mocked, only the Foundry SDK calls in other labs are.
"""

import pytest

from solution.sandbox_tool import CODE_INTERPRETER_TOOL, SANDBOX_TOOL, build_pack_weight_agent, execute_tool, run_in_sandbox
from testing.foundry_mocks import FakeAgentsClient


def test_run_in_sandbox_captures_stdout():
    result = run_in_sandbox("print(1 + 1)")

    assert result.stdout.strip() == "2"
    assert result.succeeded is True


def test_run_in_sandbox_captures_a_failure():
    result = run_in_sandbox("raise ValueError('boom')")

    assert result.exit_code != 0
    assert "boom" in result.stderr
    assert result.succeeded is False


def test_run_in_sandbox_times_out_on_an_infinite_loop():
    result = run_in_sandbox("while True: pass", timeout=0.3)

    assert result.timed_out is True
    assert result.succeeded is False


def test_execute_tool_dispatches_to_the_sandbox():
    result = execute_tool("run_python_in_sandbox", {"code": "print(21 * 2)"})

    assert result == {"stdout": "42\n", "stderr": "", "succeeded": True}


def test_execute_tool_raises_for_an_unregistered_tool_name():
    with pytest.raises(ValueError, match="check_the_weather"):
        execute_tool("check_the_weather", {})


def test_build_pack_weight_agent_attaches_both_tools():
    agents_client = FakeAgentsClient()

    agent = build_pack_weight_agent(agents_client, model="cascadia-low-cost")

    assert agent.tools == [CODE_INTERPRETER_TOOL, SANDBOX_TOOL]
