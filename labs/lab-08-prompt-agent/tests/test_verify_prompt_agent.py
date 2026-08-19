"""Tests for solution/verify_prompt_agent.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

import pytest

from solution.verify_prompt_agent import AgentCheckError, ask_agent, check_grounded_reply
from testing.foundry_mocks import FakeAgentsClient


def _seed_agent(agents_client, final_reply: str):
    agent = agents_client.create_agent(model="cascadia-low-cost", name="cascadia-support", instructions="be helpful")
    agents_client.script_final_reply(agent.id, final_reply)
    return agent


def test_ask_agent_returns_the_final_reply():
    agents_client = FakeAgentsClient()
    agent = _seed_agent(agents_client, "You have 60 days to return unused gear.")

    reply = ask_agent(agents_client, agent.id, "What is your return window?")

    assert reply == "You have 60 days to return unused gear."


def test_ask_agent_uses_a_fresh_thread_each_call():
    agents_client = FakeAgentsClient()
    agent = _seed_agent(agents_client, "reply")

    ask_agent(agents_client, agent.id, "question one")
    ask_agent(agents_client, agent.id, "question two")

    assert agents_client.thread_count == 2


def test_check_grounded_reply_passes_when_the_phrase_is_present():
    agents_client = FakeAgentsClient()
    agent = _seed_agent(agents_client, "You have 60 days to return unused gear.")

    reply = check_grounded_reply(agents_client, agent.id, "What is your return window?", must_contain="60 days")

    assert reply == "You have 60 days to return unused gear."


def test_check_grounded_reply_matches_case_insensitively():
    agents_client = FakeAgentsClient()
    agent = _seed_agent(agents_client, "You have Sixty (60 Days) to return items.")

    check_grounded_reply(agents_client, agent.id, "question", must_contain="60 DAYS")


def test_check_grounded_reply_raises_with_a_hint_when_the_phrase_is_missing():
    agents_client = FakeAgentsClient()
    agent = _seed_agent(agents_client, "I'm not sure about our return policy.")

    with pytest.raises(AgentCheckError, match="Agent Builder"):
        check_grounded_reply(agents_client, agent.id, "What is your return window?", must_contain="60 days")
