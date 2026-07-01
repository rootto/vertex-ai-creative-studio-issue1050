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
    prompt: str, image_gcs: str | None, image_mime: str | None,
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
    prompt: str, r2v_images_json: str,
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
) -> tuple[str, str, str]:
    """Vertex AI model backend logic for Gemini Omni.

    Returns:
        tuple[str, str, str]: (gcs_uri, display_url, interaction_id)

    """
    logger.info(
        f"generate_omni_video called: prompt={prompt}, mode={mode}, aspect_ratio={aspect_ratio}, previous_interaction_id={previous_interaction_id}",
    )

    try:
        client = genai.Client()
    except Exception as e:
        logger.exception("Failed to initialize GenAI client")
        raise GenerationError(f"Failed to initialize GenAI client: {e}") from e

    input_data = _build_input_data(
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
            previous_interaction_id=previous_interaction_id,
            response_format=response_format,
        )
    except Exception as e:
        logger.exception("Error calling interactions.create")
        raise GenerationError(
            f"Error generating video from Gemini Omni API: {e}",
        ) from e

    # Extract output video
    if (
        not hasattr(response, "output_video")
        or not response.output_video
        or not response.output_video.data
    ):
        raise GenerationError("No video output generated from model interaction.")

    interaction_id = response.id
    raw_data = response.output_video.data

    try:
        # Base64 decode raw data if it is base64 encoded
        if isinstance(raw_data, str):
            raw_video_bytes = base64.b64decode(raw_data)
        else:
            # If it's already bytes, it might be base64-encoded bytes or raw video bytes.
            # Try to decode first. If it raises an exception, fallback.
            try:
                raw_video_bytes = base64.b64decode(raw_data)
            except (binascii.Error, ValueError, TypeError):
                raw_video_bytes = raw_data
    except Exception as e:
        logger.exception("Failed to decode video output data")
        raise GenerationError(f"Failed to decode video output data: {e}") from e

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

    return gcs_uri, display_url, interaction_id
