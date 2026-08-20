"""Tests for solution/prompt_scoring.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

from solution.prompt_scoring import compare_prompts, score_reply, score_system_prompt
from testing.foundry_mocks import FakeChatCompletionsClient


def test_score_reply_with_no_required_phrases_is_a_perfect_score():
    assert score_reply("anything at all", must_contain=[]) == 1.0


def test_score_reply_counts_matching_phrases_case_insensitively():
    score = score_reply("You have 60 Days to return it.", must_contain=["60 days"])

    assert score == 1.0


def test_score_reply_gives_partial_credit():
    score = score_reply("I'm not sure about the return window.", must_contain=["60 days", "non-returnable"])

    assert score == 0.0

    score = score_reply("You have 60 days, and some items are non-returnable.", must_contain=["60 days", "non-returnable"])

    assert score == 1.0


def test_score_system_prompt_sends_a_system_and_user_message_per_question():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("You have 60 days.")

    score_system_prompt(
        chat_client,
        "Be helpful.",
        deployment_name="cascadia-low-cost",
        questions=[{"question": "What is your return window?", "must_contain": ["60 days"]}],
    )

    call = chat_client.calls[0]
    assert call["messages"] == [
        {"role": "system", "content": "Be helpful."},
        {"role": "user", "content": "What is your return window?"},
    ]


def test_score_system_prompt_averages_across_questions():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("You have 60 days.")
    chat_client.queue_reply("I don't know about carabiners.")

    score = score_system_prompt(
        chat_client,
        "Be helpful.",
        deployment_name="cascadia-low-cost",
        questions=[
            {"question": "Return window?", "must_contain": ["60 days"]},
            {"question": "Carabiner return?", "must_contain": ["non-returnable"]},
        ],
    )

    assert score.per_question_scores == [1.0, 0.0]
    assert score.average_score == 0.5


def test_compare_prompts_reports_improvement():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("I'm not sure.")  # weak prompt's reply
    chat_client.queue_reply("You have 60 days to return unused gear.")  # optimized prompt's reply

    comparison = compare_prompts(
        chat_client,
        weak_prompt="Be helpful.",
        optimized_prompt="You are Cascadia's support agent. Cite the return policy exactly.",
        deployment_name="cascadia-low-cost",
        questions=[{"question": "Return window?", "must_contain": ["60 days"]}],
    )

    assert comparison.weak.average_score == 0.0
    assert comparison.optimized.average_score == 1.0
    assert comparison.improved is True


def test_compare_prompts_reports_no_improvement_when_scores_tie():
    chat_client = FakeChatCompletionsClient()
    chat_client.queue_reply("You have 60 days.")
    chat_client.queue_reply("You have 60 days.")

    comparison = compare_prompts(
        chat_client,
        weak_prompt="Be helpful.",
        optimized_prompt="Be helpful, precisely.",
        deployment_name="cascadia-low-cost",
        questions=[{"question": "Return window?", "must_contain": ["60 days"]}],
    )

    assert comparison.improved is False
