"""Builds a multimodal message from a damaged-gear photo and asks a
vision model to assess it, so Maya's return request gets triaged
without a human looking at the photo first.
"""

from __future__ import annotations

import base64
import dataclasses
import mimetypes
from pathlib import Path

DAMAGED_GEAR_DIR = Path(__file__).resolve().parents[3] / "case-study" / "damaged-gear-photos"
SAMPLE_PHOTO = DAMAGED_GEAR_DIR / "tent-pole-break.png"


def encode_image_base64(path: Path) -> str:
    """Reads an image file and returns its base64-encoded contents."""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def build_image_data_url(path: Path) -> str:
    """Builds a `data:` URL from an image file's contents and MIME type."""
    mime_type, _ = mimetypes.guess_type(path.name)
    mime_type = mime_type or "application/octet-stream"
    return f"data:{mime_type};base64,{encode_image_base64(path)}"


def build_vision_message(image_path: Path, *, question: str) -> dict:
    """Builds a multimodal user message: text plus an inline image.

    The `content` list shape — not a plain string — is what tells the
    model there's an image attached. A text-only message would only
    describe the picture in words, never look at it.
    """
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": build_image_data_url(image_path)}},
        ],
    }


@dataclasses.dataclass
class DamageAssessment:
    image_path: Path
    assessment: str


def assess_damaged_item(chat_client, image_path: Path, *, deployment_name: str, question: str) -> DamageAssessment:
    """Sends one damaged-gear photo to a vision-capable deployment."""
    message = build_vision_message(image_path, question=question)
    response = chat_client.complete(model=deployment_name, messages=[message])
    return DamageAssessment(image_path=image_path, assessment=response.choices[0].message.content)


def main() -> None:  # pragma: no cover - real SDK wiring and CLI entry point, exercised manually
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    chat_client = client.inference.get_chat_completions_client()
    deployment_name = os.environ.get("VISION_DEPLOYMENT", "cascadia-vision")

    assessment = assess_damaged_item(
        chat_client,
        SAMPLE_PHOTO,
        deployment_name=deployment_name,
        question="Describe the damage in this photo and suggest a return category.",
    )
    print(assessment.assessment)


if __name__ == "__main__":  # pragma: no cover
    main()
