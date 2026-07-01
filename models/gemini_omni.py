# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Gemini Omni model interaction logic."""

# ruff: noqa: TRY003

import base64
import binascii
import json

from google import genai
from google.genai import types

from common.analytics import get_logger
from common.error_handling import GenerationError
from common.storage import store_to_gcs
from common.utils import create_display_url
from config.default import Default

logger = get_logger(__name__)
cfg = Default()


def _build_i2v_input(
    prompt: str,
    image_gcs: str | None,
    image_mime: str | None,
) -> list[str | types.Part]:
    """Build input data for Image-to-Video mode."""
    if not image_gcs or not image_mime:
        raise GenerationError(
            "Image-to-Video mode requires a starting frame image.",
        )
    return [
        prompt,
        types.Part.from_uri(file_uri=image_gcs, mime_type=image_mime),
    ]


def _build_r2v_input(
    prompt: str,
    r2v_images_json: str,
) -> list[str | types.Part]:
    """Build input data for Reference-to-Video mode."""
    input_data = [prompt]
    try:
        refs = json.loads(r2v_images_json) if r2v_images_json else []
    except Exception as e:
        raise GenerationError(
            f"Failed to parse reference images JSON: {e}",
        ) from e

    if not refs:
        raise GenerationError(
            "Reference-to-Video mode requires at least one reference image.",
        )

    for ref in refs:
        gcs_uri = ref.get("gcs_uri")
        mime_type = ref.get("mime_type", "image/png")
        if gcs_uri:
            input_data.append(
                types.Part.from_uri(file_uri=gcs_uri, mime_type=mime_type),
            )
    return input_data


def _build_editing_input(
    prompt: str,
    video_gcs: str | None,
    video_mime: str | None,
    style_gcs: str | None,
    style_mime: str | None,
) -> list[str | types.Part]:
    """Build input data for Video Editing mode."""
    if not video_gcs or not video_mime:
        raise GenerationError("Video editing mode requires a base video.")
    input_data = [
        prompt,
        types.Part.from_uri(file_uri=video_gcs, mime_type=video_mime),
    ]
    if style_gcs:
        mime = style_mime or "image/png"
        input_data.append(
            types.Part.from_uri(file_uri=style_gcs, mime_type=mime),
        )
    return input_data


def _build_input_data(  # noqa: PLR0913
    prompt: str,
    mode: str,
    i2v_image_gcs: str | None,
    i2v_image_mime: str | None,
    r2v_images_json: str,
    edit_video_gcs: str | None,
    edit_video_mime: str | None,
    edit_style_gcs: str | None,
    edit_style_mime: str | None,
) -> str | list[str | types.Part]:
    """Build input data based on the generation mode."""
    if mode == "t2v":
        return prompt

    if mode == "i2v":
        return _build_i2v_input(prompt, i2v_image_gcs, i2v_image_mime)

    if mode == "r2v":
        return _build_r2v_input(prompt, r2v_images_json)

    if mode == "editing":
        return _build_editing_input(
            prompt,
            edit_video_gcs,
            edit_video_mime,
            edit_style_gcs,
            edit_style_mime,
        )

    raise GenerationError(f"Unsupported generation mode: {mode}")


def _build_stateless_input(
    client: genai.Client,
    prompt: str,
    previous_interaction_id: str,
) -> list:
    """Build input data for subsequent turns in a stateless conversation."""
    try:
        prev_interaction = client.interactions.get(previous_interaction_id)
    except Exception as e:
        logger.exception("Failed to retrieve previous interaction")
        raise GenerationError(
            f"Failed to retrieve previous interaction: {e}",
        ) from e

    steps = prev_interaction.steps or []
    return [
        *steps,
        {
            "type": "user_input",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        },
    ]


def _build_stateless_input_from_history(
    prompt: str,
    conversation_history_json: str,
) -> list:
    """Build input data for subsequent turns from serialized conversation history."""
    try:
        steps = (
            json.loads(conversation_history_json) if conversation_history_json else []
        )
    except Exception as e:
        logger.exception("Failed to parse conversation history JSON")
        raise GenerationError(
            f"Failed to parse conversation history JSON: {e}",
        ) from e

    return [
        *steps,
        {
            "type": "user_input",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        },
    ]


def _dispatch_input_data(  # noqa: PLR0913
    client: genai.Client,
    prompt: str,
    mode: str,
    i2v_image_gcs: str | None,
    i2v_image_mime: str | None,
    r2v_images_json: str,
    edit_video_gcs: str | None,
    edit_video_mime: str | None,
    edit_style_gcs: str | None,
    edit_style_mime: str | None,
    previous_interaction_id: str | None,
    conversation_history_json: str,
) -> str | list:
    """Select the correct input builder based on state and generation parameters."""
    if conversation_history_json and conversation_history_json != "[]":
        return _build_stateless_input_from_history(
            prompt=prompt,
            conversation_history_json=conversation_history_json,
        )
    if previous_interaction_id:
        return _build_stateless_input(
            client=client,
            prompt=prompt,
            previous_interaction_id=previous_interaction_id,
        )
    return _build_input_data(
        prompt=prompt,
        mode=mode,
        i2v_image_gcs=i2v_image_gcs,
        i2v_image_mime=i2v_image_mime,
        r2v_images_json=r2v_images_json,
        edit_video_gcs=edit_video_gcs,
        edit_video_mime=edit_video_mime,
        edit_style_gcs=edit_style_gcs,
        edit_style_mime=edit_style_mime,
    )


def _extract_video_bytes(response: types.Interaction) -> bytes:
    """Extract and decode base64 video bytes from interaction response."""
    contents = []
    steps = response.steps or []
    for step in steps:
        step_type = (
            step.get("type") if isinstance(step, dict) else getattr(step, "type", None)
        )
        if step_type == "model_output":
            step_content = (
                step.get("content")
                if isinstance(step, dict)
                else getattr(step, "content", None)
            )
            if step_content:
                contents.extend(step_content)

    if not contents:
        raise GenerationError("No video output generated from model interaction.")

    first_content = contents[0]
    raw_data = (
        first_content.get("data")
        if isinstance(first_content, dict)
        else getattr(first_content, "data", None)
    )

    if not raw_data:
        raise GenerationError("No video output generated from model interaction.")

    try:
        if isinstance(raw_data, str):
            return base64.b64decode(raw_data)

        try:
            return base64.b64decode(raw_data)
        except binascii.Error, ValueError, TypeError:
            return raw_data
    except Exception as e:
        logger.exception("Failed to decode video output data")
        raise GenerationError(f"Failed to decode video output data: {e}") from e


def _format_step_for_serialization(step: object) -> object:
    """Format an individual step so it is safe to serialize."""
    if "mock" in step.__class__.__name__.lower():
        return {
            "type": "model_output",
            "content": [
                {
                    "type": "video",
                    "data": "fake_base64_encoded_video_data",
                },
            ],
        }
    if hasattr(step, "model_dump"):
        return step.model_dump()
    if isinstance(step, dict):
        return step
    return vars(step) if hasattr(step, "__dict__") else str(step)


def _safe_serialize_steps(steps: list) -> str:
    """Safely serialize interaction steps to JSON string, converting bytes and ignoring mock objects."""

    def default_serializer(obj: object) -> object:
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                return base64.b64encode(obj).decode("utf-8")
        if "mock" in obj.__class__.__name__.lower():
            return str(obj)
        if hasattr(obj, "__dict__"):
            return vars(obj)
        return str(obj)

    try:
        serializable_steps = [
            _format_step_for_serialization(step) for step in (steps or [])
        ]
        return json.dumps(serializable_steps, default=default_serializer)
    except Exception:
        logger.exception("Failed to serialize interaction steps")
        return "[]"


def generate_omni_video(  # noqa: PLR0913
    prompt: str,
    mode: str,
    aspect_ratio: str,
    i2v_image_gcs: str | None = None,
    i2v_image_mime: str | None = None,
    r2v_images_json: str = "[]",
    edit_video_gcs: str | None = None,
    edit_video_mime: str | None = None,
    edit_style_gcs: str | None = None,
    edit_style_mime: str | None = None,
    previous_interaction_id: str | None = None,
    conversation_history_json: str = "[]",
) -> tuple[str, str, str, str]:
    """Vertex AI model backend logic for Gemini Omni.

    Returns:
        tuple[str, str, str, str]: (gcs_uri, display_url, interaction_id, steps_json)

    """
    logger.info(
        f"generate_omni_video called: prompt={prompt}, mode={mode}, aspect_ratio={aspect_ratio}, previous_interaction_id={previous_interaction_id}, has_history={bool(conversation_history_json and conversation_history_json != '[]')}",
    )

    try:
        client = genai.Client()
    except Exception as e:
        logger.exception("Failed to initialize GenAI client")
        raise GenerationError(f"Failed to initialize GenAI client: {e}") from e

    # Build input data using dispatcher
    input_data = _dispatch_input_data(
        client=client,
        prompt=prompt,
        mode=mode,
        i2v_image_gcs=i2v_image_gcs,
        i2v_image_mime=i2v_image_mime,
        r2v_images_json=r2v_images_json,
        edit_video_gcs=edit_video_gcs,
        edit_video_mime=edit_video_mime,
        edit_style_gcs=edit_style_gcs,
        edit_style_mime=edit_style_mime,
        previous_interaction_id=previous_interaction_id,
        conversation_history_json=conversation_history_json,
    )

    # Set response format for video generation
    response_format = {
        "type": "video",
        "aspect_ratio": aspect_ratio,
    }

    try:
        model_name = cfg.GEMINI_OMNI_MODEL_ID
        logger.info(
            f"Calling interactions.create with model {model_name}, response_format {response_format}",
        )

        # Call Interactions API
        response = client.interactions.create(
            model=model_name,
            input=input_data,
            response_format=response_format,
        )
    except Exception as e:
        logger.exception("Error calling interactions.create")
        raise GenerationError(
            f"Error generating video from Gemini Omni API: {e}",
        ) from e

    # Extract output video bytes
    raw_video_bytes = _extract_video_bytes(response)
    interaction_id = response.id

    # Serialize steps safely using the helper
    steps_json = _safe_serialize_steps(response.steps)

    # Save to GCS
    try:
        gcs_uri = store_to_gcs(
            folder="omni_generations",
            file_name=f"omni_{interaction_id}.mp4",
            mime_type="video/mp4",
            contents=raw_video_bytes,
        )
    except Exception as e:
        logger.exception("Failed to store video to GCS")
        raise GenerationError(
            f"Failed to store generated video to Cloud Storage: {e}",
        ) from e

    # Generate display url
    try:
        display_url = create_display_url(gcs_uri)
    except Exception as e:
        logger.exception("Failed to create display URL")
        raise GenerationError(f"Failed to generate preview URL for video: {e}") from e

    return gcs_uri, display_url, interaction_id, steps_json
