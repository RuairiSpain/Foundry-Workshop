"""Tests for solution/fine_tuning.py.

main() is excluded from coverage — real SDK wiring, a live fine-tuning
job, and a CLI entry point, exercised manually.
"""

import pytest

from testing.foundry_mocks import FakeFineTuningJobsAPI, FakeOpenAIClient

from solution.fine_tuning import (
    BaselineComparison,
    FineTuningJobFailedError,
    build_fine_tuning_dataset,
    compare_against_baseline,
    poll_until_complete,
    score_groundedness,
    submit_fine_tuning_job,
    summarize_comparison,
)


def test_build_fine_tuning_dataset_converts_examples_to_chat_records():
    examples = [{"question": "What is your return window?", "answer": "60 days."}]

    dataset = build_fine_tuning_dataset(examples)

    assert dataset == [
        {
            "messages": [
                {"role": "user", "content": "What is your return window?"},
                {"role": "assistant", "content": "60 days."},
            ]
        }
    ]


def test_build_fine_tuning_dataset_handles_multiple_examples():
    examples = [
        {"question": "Q1", "answer": "A1"},
        {"question": "Q2", "answer": "A2"},
    ]

    dataset = build_fine_tuning_dataset(examples)

    assert len(dataset) == 2
    assert dataset[1]["messages"][0]["content"] == "Q2"


def test_submit_fine_tuning_job_creates_a_job():
    fine_tuning_jobs = FakeFineTuningJobsAPI()

    job = submit_fine_tuning_job(
        fine_tuning_jobs, model="cascadia-low-cost", training_file="file-0001", suffix="cascadia-returns"
    )

    assert job.model == "cascadia-low-cost"
    assert job.status == "queued"


def test_poll_until_complete_returns_the_job_once_it_succeeds():
    fine_tuning_jobs = FakeFineTuningJobsAPI()
    job = fine_tuning_jobs.create(model="cascadia-low-cost", training_file="file-0001", suffix="s")
    fine_tuning_jobs.script_status_sequence(job.id, ["running", "running", "succeeded"])

    completed = poll_until_complete(fine_tuning_jobs, job.id, max_polls=5)

    assert completed.status == "succeeded"
    assert completed.fine_tuned_model == "cascadia-low-cost-ft-s"


def test_poll_until_complete_raises_on_a_failed_job():
    fine_tuning_jobs = FakeFineTuningJobsAPI()
    job = fine_tuning_jobs.create(model="cascadia-low-cost", training_file="file-0001", suffix="s")
    fine_tuning_jobs.script_status_sequence(job.id, ["running", "failed"])

    with pytest.raises(FineTuningJobFailedError, match=job.id):
        poll_until_complete(fine_tuning_jobs, job.id, max_polls=5)


def test_poll_until_complete_raises_timeout_error_when_it_never_finishes():
    fine_tuning_jobs = FakeFineTuningJobsAPI()
    job = fine_tuning_jobs.create(model="cascadia-low-cost", training_file="file-0001", suffix="s")
    fine_tuning_jobs.script_status_sequence(job.id, ["running", "running", "running"])

    with pytest.raises(TimeoutError, match=job.id):
        poll_until_complete(fine_tuning_jobs, job.id, max_polls=3)


def test_poll_until_complete_sleeps_between_polls_when_an_interval_is_given(monkeypatch):
    fine_tuning_jobs = FakeFineTuningJobsAPI()
    job = fine_tuning_jobs.create(model="cascadia-low-cost", training_file="file-0001", suffix="s")
    fine_tuning_jobs.script_status_sequence(job.id, ["running", "succeeded"])
    sleeps = []
    monkeypatch.setattr("solution.fine_tuning.time.sleep", lambda seconds: sleeps.append(seconds))

    poll_until_complete(fine_tuning_jobs, job.id, max_polls=5, poll_interval_seconds=0.5)

    assert sleeps == [0.5]


def test_score_groundedness_with_no_requirements_is_a_full_score():
    assert score_groundedness("anything at all", must_contain=[]) == 1.0


def test_score_groundedness_counts_matching_phrases():
    score = score_groundedness("Returns are accepted within 60 days.", must_contain=["60 days", "non-returnable"])

    assert score == 0.5


def test_compare_against_baseline_scores_both_deployments_per_question():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("Returns are accepted within 60 days.")  # fine-tuned reply
    chat_client.queue_reply("I'm not sure about our return policy.")  # router reply

    results = compare_against_baseline(
        chat_client,
        [{"question": "What is your return window?", "must_contain": ["60 days"]}],
        fine_tuned_deployment="cascadia-low-cost-ft-returns",
        router_deployment="cascadia-router",
    )

    assert results == [
        BaselineComparison(
            question="What is your return window?",
            fine_tuned_reply="Returns are accepted within 60 days.",
            router_reply="I'm not sure about our return policy.",
            fine_tuned_groundedness=1.0,
            router_groundedness=0.0,
        )
    ]
    assert results[0].fine_tuned_wins is True
    assert chat_client.calls[0]["model"] == "cascadia-low-cost-ft-returns"
    assert chat_client.calls[1]["model"] == "cascadia-router"


def test_summarize_comparison_counts_wins_losses_and_ties():
    results = [
        BaselineComparison("q1", "a", "b", fine_tuned_groundedness=1.0, router_groundedness=0.0),
        BaselineComparison("q2", "a", "b", fine_tuned_groundedness=0.0, router_groundedness=1.0),
        BaselineComparison("q3", "a", "b", fine_tuned_groundedness=0.5, router_groundedness=0.5),
    ]

    summary = summarize_comparison(results)

    assert summary == {"fine_tuned_wins": 1, "router_wins": 1, "ties": 1}
