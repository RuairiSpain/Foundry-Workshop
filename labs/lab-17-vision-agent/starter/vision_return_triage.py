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
    # TODO(lab-17): read path's bytes and base64-encode them, returning
    # an ASCII string (not bytes).
    raise NotImplementedError("encode_image_base64 is not implemented yet")


def build_image_data_url(path: Path) -> str:
    """Builds a `data:` URL from an image file's contents and MIME type."""
    # TODO(lab-17): guess the MIME type from path.name with
    # mimetypes.guess_type(), falling back to "application/octet-stream".
    # Return f"data:{mime_type};base64,{encoded}".
    raise NotImplementedError("build_image_data_url is not implemented yet")


def build_vision_message(image_path: Path, *, question: str) -> dict:
    """Builds a multimodal user message: text plus an inline image."""
    # TODO(lab-17): return a message with role "user" and a content list
    # of two parts: {"type": "text", "text": question} and
    # {"type": "image_url", "image_url": {"url": build_image_data_url(image_path)}}.
    raise NotImplementedError("build_vision_message is not implemented yet")


@dataclasses.dataclass
class DamageAssessment:
    image_path: Path
    assessment: str


def assess_damaged_item(chat_client, image_path: Path, *, deployment_name: str, question: str) -> DamageAssessment:
    """Sends one damaged-gear photo to a vision-capable deployment."""
    # TODO(lab-17): build the message with build_vision_message(), call
    # chat_client.chat.completions.create() with it, and return a DamageAssessment.
    raise NotImplementedError("assess_damaged_item is not implemented yet")


def main() -> None:
    import os

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    chat_client = client.get_openai_client()
    deployment_name = os.environ.get("VISION_DEPLOYMENT", "cascadia-vision")

    assessment = assess_damaged_item(
        chat_client,
        SAMPLE_PHOTO,
        deployment_name=deployment_name,
        question="Describe the damage in this photo and suggest a return category.",
    )
    print(assessment.assessment)


if __name__ == "__main__":
    main()
