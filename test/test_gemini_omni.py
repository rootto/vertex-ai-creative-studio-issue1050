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

"""Unit tests for Gemini Omni model backend."""

# ruff: noqa: S101, ANN001, ANN201, ARG001, PLR2004

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.error_handling import GenerationError
from models.gemini_omni import generate_omni_video


@pytest.fixture
def mock_genai_client():
    """Mock the GenAI Client."""
    with patch("models.gemini_omni.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_store_to_gcs():
    """Mock GCS storage helper."""
    with patch("models.gemini_omni.store_to_gcs") as mock_store:
        mock_store.return_value = "gs://fake-bucket/fake-video.mp4"
        yield mock_store


@pytest.fixture
def mock_create_display_url():
    """Mock display URL generation helper."""
    with patch("models.gemini_omni.create_display_url") as mock_url:
        mock_url.return_value = "https://example.com/fake-video.mp4"
        yield mock_url


def test_generate_omni_video_t2v(
    mock_genai_client,
    mock_store_to_gcs,
    mock_create_display_url,
):
    """Test text-to-video generation."""
    # Arrange
    mock_interaction = MagicMock()
    mock_interaction.id = "turn1_id"
    mock_interaction.output_video.data = b"fake_base64_encoded_video_data"
    mock_genai_client.interactions.create.return_value = mock_interaction

    # Act
    gcs_uri, display_url, interaction_id = generate_omni_video(
        prompt="A cute cat playing",
        mode="t2v",
        aspect_ratio="16:9",
    )

    # Assert
    assert gcs_uri == "gs://fake-bucket/fake-video.mp4"
    assert display_url == "https://example.com/fake-video.mp4"
    assert interaction_id == "turn1_id"

    # Verify API calls
    mock_genai_client.interactions.create.assert_called_once_with(
        model="gemini-omni-flash-preview",
        input="A cute cat playing",
        previous_interaction_id=None,
        response_format={"type": "video", "aspect_ratio": "16:9"},
    )
    mock_store_to_gcs.assert_called_once()
    mock_create_display_url.assert_called_once_with(
        "gs://fake-bucket/fake-video.mp4",
    )


def test_generate_omni_video_i2v(
    mock_genai_client,
    mock_store_to_gcs,
    mock_create_display_url,
):
    """Test image-to-video generation."""
    # Arrange
    mock_interaction = MagicMock()
    mock_interaction.id = "turn1_id_i2v"
    mock_interaction.output_video.data = b"fake_video"
    mock_genai_client.interactions.create.return_value = mock_interaction

    # Act
    generate_omni_video(
        prompt="Make it move",
        mode="i2v",
        aspect_ratio="9:16",
        i2v_image_gcs="gs://bucket/start.png",
        i2v_image_mime="image/png",
    )

    # Assert
    _, called_kwargs = mock_genai_client.interactions.create.call_args
    assert called_kwargs["model"] == "gemini-omni-flash-preview"
    assert called_kwargs["previous_interaction_id"] is None
    assert called_kwargs["response_format"] == {
        "type": "video",
        "aspect_ratio": "9:16",
    }

    # Check parts
    input_data = called_kwargs["input"]
    assert isinstance(input_data, list)
    assert input_data[0] == "Make it move"
    assert input_data[1].file_data.file_uri == "gs://bucket/start.png"
    assert input_data[1].file_data.mime_type == "image/png"


def test_generate_omni_video_editing_with_ref(
    mock_genai_client,
    mock_store_to_gcs,
    mock_create_display_url,
):
    """Test video editing with optional style/reference image."""
    # Arrange
    mock_interaction = MagicMock()
    mock_interaction.id = "turn1_id_edit"
    mock_interaction.output_video.data = b"fake_video"
    mock_genai_client.interactions.create.return_value = mock_interaction

    # Act
    generate_omni_video(
        prompt="Make it cartoon style",
        mode="editing",
        aspect_ratio="16:9",
        edit_video_gcs="gs://bucket/base.mp4",
        edit_video_mime="video/mp4",
        edit_style_gcs="gs://bucket/style.png",
        edit_style_mime="image/png",
    )

    # Assert
    _, called_kwargs = mock_genai_client.interactions.create.call_args
    input_data = called_kwargs["input"]
    assert len(input_data) == 3
    assert input_data[0] == "Make it cartoon style"
    assert input_data[1].file_data.file_uri == "gs://bucket/base.mp4"
    assert input_data[2].file_data.file_uri == "gs://bucket/style.png"


def test_generate_omni_video_missing_i2v_image(mock_genai_client):
    """Test that missing image in i2v raises GenerationError."""
    with pytest.raises(GenerationError) as exc_info:
        generate_omni_video(
            prompt="Make it move",
            mode="i2v",
            aspect_ratio="16:9",
        )
    assert "Image-to-Video mode requires a starting frame image" in str(
        exc_info.value,
    )
