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

import base64
import io
import json
import time

import shortuuid
from google import genai
from google.genai import types

from common.analytics import get_logger
from common.error_handling import GenerationError
from common.storage import download_from_gcs, store_to_gcs
from common.utils import create_display_url
from config.default import Default

config = Default()
logger = get_logger(__name__)


def _get_field(obj, field_name):
    """Retrieve field value from either a dictionary or an object."""
    if isinstance(obj, dict):
        return obj.get(field_name)
    return getattr(obj, field_name, None)


def get_omni_client() -> genai.Client:
    """Initialize the google-genai Client configured for Gemini Omni API."""
    return genai.Client(
        vertexai=True,
        project=config.PROJECT_ID,
        location="global",
        http_options=types.HttpOptions(headers={"Api-Revision": "2026-05-20"}),
    )


def generate_omni_video(
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
) -> tuple[str, str]:
    """Generate or edit a video using Gemini Omni Flash interactions API.

    Returns:
        tuple[str, str]: (gcs_uri, display_url) of the generated video.

    """
    client = get_omni_client()
    input_parts = []

    try:
        # 1. Build input parts based on mode
        if mode == "t2v":
            input_parts.append({"type": "text", "text": prompt})

        elif mode == "i2v":
            if not i2v_image_gcs or not i2v_image_mime:
                raise GenerationError(
                    "Image input is required for Image-to-Video mode.",
                )
            logger.info(f"Downloading starting frame image from GCS: {i2v_image_gcs}")
            img_bytes = download_from_gcs(i2v_image_gcs)
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
            input_parts.append(
                {
                    "type": "image",
                    "data": img_base64,
                    "mime_type": i2v_image_mime,
                },
            )
            input_parts.append({"type": "text", "text": prompt})

        elif mode == "r2v":
            refs = json.loads(r2v_images_json)
            if not refs:
                raise GenerationError(
                    "At least one reference image is required for Reference-to-Video mode.",
                )
            logger.info(f"Processing {len(refs)} reference images.")
            for ref in refs:
                gcs_uri = ref["gcs_uri"]
                mime_type = ref["mime_type"]
                img_bytes = download_from_gcs(gcs_uri)
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                input_parts.append(
                    {
                        "type": "image",
                        "data": img_base64,
                        "mime_type": mime_type,
                    },
                )
            input_parts.append({"type": "text", "text": prompt})

        elif mode == "editing":
            if not edit_video_gcs or not edit_video_mime:
                raise GenerationError("Base video is required for Video Editing mode.")

            logger.info(f"Downloading base video from GCS: {edit_video_gcs}")
            video_bytes = download_from_gcs(edit_video_gcs)
            logger.info("Uploading base video to Gemini Files API...")
            video_file = client.files.upload(
                file=io.BytesIO(video_bytes),
                config={"mime_type": edit_video_mime},
            )
            # Wait for file processing
            while video_file.state.name == "PROCESSING":
                logger.info("Base video processing on Files API... sleeping 2s.")
                time.sleep(2)
                video_file = client.files.get(name=video_file.name)
            if video_file.state.name == "FAILED":
                raise GenerationError(
                    "Base video upload processing failed on Files API.",
                )

            input_parts.append({"type": "document", "uri": video_file.uri})

            # Optional reference style image
            if edit_style_gcs and edit_style_mime:
                logger.info(
                    f"Downloading optional style image from GCS: {edit_style_gcs}",
                )
                style_bytes = download_from_gcs(edit_style_gcs)
                style_base64 = base64.b64encode(style_bytes).decode("utf-8")
                input_parts.append(
                    {
                        "type": "image",
                        "data": style_base64,
                        "mime_type": edit_style_mime,
                    },
                )
            input_parts.append({"type": "text", "text": prompt})

        else:
            raise GenerationError(f"Unsupported Omni generation mode: {mode}")

        # 2. Setup response format
        response_format = {
            "type": "video",
            "aspect_ratio": aspect_ratio,
        }

        logger.info(
            f"Calling interactions.create with mode={mode}, aspect_ratio={aspect_ratio}",
        )
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=input_parts,
            response_format=response_format,
        )

        # 3. Process outputs
        steps = _get_field(interaction, "steps") or []
        video_part = None
        for step in reversed(steps):
            step_type = _get_field(step, "type")
            step_content = _get_field(step, "content")
            if step_type == "model_output" and step_content:
                for part in reversed(step_content):
                    part_type = _get_field(part, "type")
                    if part_type == "video":
                        video_part = part
                        break
            if video_part:
                break

        if not video_part:
            raise GenerationError(
                "No video returned from the Gemini Omni model response.",
            )

        logger.info("Omni output video retrieved successfully. Storing to GCS...")

        file_name = f"omni_{shortuuid.uuid()}.mp4"

        # Check if the data is inline base64 or stored as a GCS URI (e.g. delivery="uri")
        video_b64 = _get_field(video_part, "data")
        video_uri = _get_field(video_part, "uri")
        if not video_b64 and video_uri:
            logger.info(f"Downloading from response URI: {video_uri}")
            video_bytes = client.files.download(file=video_uri)
            video_b64 = base64.b64encode(video_bytes).decode("utf-8")

        if not video_b64:
            raise GenerationError(
                "Failed to retrieve video bytes from interaction output.",
            )

        # Save to genmedia video GCS bucket
        mime_type = _get_field(video_part, "mime_type") or "video/mp4"
        gcs_uri = store_to_gcs(
            folder="omni",
            file_name=file_name,
            mime_type=mime_type,
            contents=video_b64,
            decode=True,
            bucket_name=config.VIDEO_BUCKET,
        )
        display_url = create_display_url(gcs_uri)
        logger.info(f"Stored Omni output to {gcs_uri}. Display URL: {display_url}")
        return gcs_uri, display_url

    except Exception as e:
        logger.exception("Error during Gemini Omni video generation")
        if isinstance(e, GenerationError):
            raise
        raise GenerationError(f"Omni generation failed: {e}") from e
