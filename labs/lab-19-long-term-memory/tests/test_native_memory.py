"""Tests for solution/native_memory.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

from solution.native_memory import ask_with_memory, recall_preferences, remember_preference
from testing.foundry_mocks import FakeAgentsClient, FakeMemoryClient


def test_remember_and_recall_round_trip():
    memory_client = FakeMemoryClient()

    remember_preference(memory_client, "maya@example.com", "Prefers boots in women's size 8.")

    assert recall_preferences(memory_client, "maya@example.com") == ["Prefers boots in women's size 8."]


def test_recall_returns_empty_list_for_an_unknown_user():
    memory_client = FakeMemoryClient()

    assert recall_preferences(memory_client, "nobody@example.com") == []


def test_ask_with_memory_injects_remembered_facts_into_a_new_thread():
    agents_client = FakeAgentsClient()
    memory_client = FakeMemoryClient()
    agent = agents_client.create_agent(model="cascadia-low-cost", name="cascadia-support", instructions="help")
    remember_preference(memory_client, "maya@example.com", "Prefers boots in women's size 8.")
    agents_client.script_final_reply(agent.id, "Based on your size 8 preference, order the women's 8.")

    reply = ask_with_memory(agents_client, memory_client, agent.id, "maya@example.com", "What boot size?")

    assert reply == "Based on your size 8 preference, order the women's 8."
    thread_id = agents_client.last_thread_id
    messages = agents_client.messages.list(thread_id)
    assert messages[0].role == "user"
    assert "size 8" in messages[0].content
    assert "What boot size?" in messages[0].content


def test_ask_with_memory_sends_the_bare_question_with_no_facts():
    agents_client = FakeAgentsClient()
    memory_client = FakeMemoryClient()
    agent = agents_client.create_agent(model="cascadia-low-cost", name="cascadia-support", instructions="help")
    agents_client.script_final_reply(agent.id, "What size do you usually wear?")

    ask_with_memory(agents_client, memory_client, agent.id, "nobody@example.com", "What boot size?")

    thread_id = agents_client.last_thread_id
    messages = agents_client.messages.list(thread_id)
    assert messages[0].role == "user"
    assert messages[0].content == "What boot size?"


def test_a_fact_remembered_in_one_thread_reaches_a_second_unrelated_thread():
    agents_client = FakeAgentsClient()
    memory_client = FakeMemoryClient()
    agent = agents_client.create_agent(model="cascadia-low-cost", name="cascadia-support", instructions="help")
    remember_preference(memory_client, "maya@example.com", "Prefers boots in women's size 8.")

    agents_client.script_final_reply(agent.id, "Size 8, as you mentioned before.")
    first_reply = ask_with_memory(agents_client, memory_client, agent.id, "maya@example.com", "What size again?")

    agents_client.script_final_reply(agent.id, "Still size 8.")
    second_reply = ask_with_memory(agents_client, memory_client, agent.id, "maya@example.com", "Remind me?")

    assert "8" in first_reply
    assert "8" in second_reply
    assert agents_client.thread_count == 2
