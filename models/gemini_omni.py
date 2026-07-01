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
"""Gemini Omni model interaction logic stub for UI testing."""

from common.analytics import get_logger

logger = get_logger(__name__)


def generate_omni_video(  # noqa: PLR0913
    prompt: str,
    mode: str,
    aspect_ratio: str,
    i2v_image_gcs: str | None = None,  # noqa: ARG001
    i2v_image_mime: str | None = None,  # noqa: ARG001
    r2v_images_json: str = "[]",  # noqa: ARG001
    edit_video_gcs: str | None = None,  # noqa: ARG001
    edit_video_mime: str | None = None,  # noqa: ARG001
    edit_style_gcs: str | None = None,  # noqa: ARG001
    edit_style_mime: str | None = None,  # noqa: ARG001
    previous_interaction_id: str | None = None,
) -> tuple[str, str, str]:
    """Mock stub for Omni video generation to support rapid UI prototyping.

    Returns:
        tuple[str, str, str]: (gcs_uri, display_url, interaction_id)

    """
    logger.info(
        f"Mock generate_omni_video called: prompt={prompt}, mode={mode}, aspect_ratio={aspect_ratio}, previous_interaction_id={previous_interaction_id}",
    )

    # Return a static public sample video for layout/UI previewing
    mock_video_url = (
        "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
    )
    mock_gcs_uri = "gs://mock-bucket/mock-omni.mp4"
    mock_interaction_id = "mock_interaction_" + (
        "refinement" if previous_interaction_id else "initial"
    )

    return mock_gcs_uri, mock_video_url, mock_interaction_id
