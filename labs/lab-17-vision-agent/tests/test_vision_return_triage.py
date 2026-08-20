"""Tests for solution/vision_return_triage.py.

main() is excluded from coverage — real SDK wiring and a CLI entry
point, exercised manually, not under test.
"""

import base64

from solution.vision_return_triage import (
    SAMPLE_PHOTO,
    assess_damaged_item,
    build_image_data_url,
    build_vision_message,
    encode_image_base64,
)
from testing.foundry_mocks import FakeOpenAIClient


def test_encode_image_base64_round_trips_the_real_bytes():
    encoded = encode_image_base64(SAMPLE_PHOTO)

    assert base64.b64decode(encoded) == SAMPLE_PHOTO.read_bytes()


def test_build_image_data_url_uses_the_correct_mime_type():
    url = build_image_data_url(SAMPLE_PHOTO)

    assert url.startswith("data:image/png;base64,")


def test_build_image_data_url_falls_back_for_an_unknown_extension(tmp_path):
    unknown_file = tmp_path / "gear.unknownext"
    unknown_file.write_bytes(b"not really an image")

    url = build_image_data_url(unknown_file)

    assert url.startswith("data:application/octet-stream;base64,")


def test_build_vision_message_has_a_text_part_and_an_image_part():
    message = build_vision_message(SAMPLE_PHOTO, question="What's broken?")

    assert message["role"] == "user"
    assert message["content"][0] == {"type": "text", "text": "What's broken?"}
    assert message["content"][1]["type"] == "image_url"
    assert message["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_assess_damaged_item_returns_the_models_assessment():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("A broken tent pole. Covered under the worn-gear guarantee.")

    assessment = assess_damaged_item(
        chat_client, SAMPLE_PHOTO, deployment_name="cascadia-vision", question="What's broken?"
    )

    assert assessment.image_path == SAMPLE_PHOTO
    assert "broken tent pole" in assessment.assessment


def test_assess_damaged_item_sends_the_multimodal_message():
    chat_client = FakeOpenAIClient()
    chat_client.queue_reply("assessment")

    assess_damaged_item(chat_client, SAMPLE_PHOTO, deployment_name="cascadia-vision", question="What's broken?")

    sent_message = chat_client.calls[0]["messages"][0]
    assert sent_message["content"][1]["type"] == "image_url"
