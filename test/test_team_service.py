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

"""Unit tests for team service."""

import os

# Set dummy environment variables to prevent Gemini client init error during import
os.environ["PROJECT_ID"] = "dummy-project"
os.environ["LOCATION"] = "us-central1"

from unittest.mock import MagicMock, patch

from google.cloud import firestore

from config.default import Default
from services.team_service import (
    add_branding_guideline,
    delete_branding_guideline,
    delete_team,
    remove_asset_from_team,
)

config = Default()


@patch("services.team_service.db")
def test_delete_team(mock_db: MagicMock) -> None:
    """Test that delete_team calls Firestore delete."""
    # Arrange
    mock_doc = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_doc
    team_id = "test-team-id"

    # Act
    delete_team(team_id)

    # Assert
    mock_db.collection.assert_called_once_with(config.TEAMS_COLLECTION_NAME)
    mock_db.collection.return_value.document.assert_called_once_with(team_id)
    mock_doc.delete.assert_called_once()


@patch("services.team_service.db")
def test_remove_asset_from_team(mock_db: MagicMock) -> None:
    """Test that remove_asset_from_team calls Firestore update with ArrayRemove."""
    # Arrange
    mock_doc = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_doc
    team_id = "test-team-id"
    asset_id = "test-asset-id"

    # Act
    remove_asset_from_team(team_id, asset_id)

    # Assert
    mock_db.collection.assert_called_once_with(config.TEAMS_COLLECTION_NAME)
    mock_db.collection.return_value.document.assert_called_once_with(team_id)
    mock_doc.update.assert_called_once()

    # Verify ArrayRemove was used
    args, _ = mock_doc.update.call_args
    assert "asset_ids" in args[0]  # noqa: S101


@patch("services.team_service.db")
def test_add_branding_guideline(mock_db: MagicMock) -> None:
    """Test that add_branding_guideline calls Firestore update with ArrayUnion."""
    # Arrange
    mock_doc = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_doc
    team_id = "test-team-id"
    name = "Test Guideline"
    g_type = "text"
    content = "vibrant colors"

    # Act
    g_id = add_branding_guideline(team_id, name, g_type, content)

    # Assert
    assert len(g_id) > 0  # noqa: S101
    mock_db.collection.assert_called_once_with(config.TEAMS_COLLECTION_NAME)
    mock_db.collection.return_value.document.assert_called_once_with(team_id)
    mock_doc.update.assert_called_once()

    args, _ = mock_doc.update.call_args
    assert "branding_guidelines" in args[0]  # noqa: S101
    union_arg = args[0]["branding_guidelines"]
    assert isinstance(union_arg, firestore.ArrayUnion)  # noqa: S101


@patch("services.team_service.db")
@patch("services.team_service.get_team")
def test_delete_branding_guideline(
    mock_get_team: MagicMock, mock_db: MagicMock,
) -> None:
    """Test that delete_branding_guideline removes a guideline by ID."""
    # Arrange
    mock_doc = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_doc

    team_id = "test-team-id"
    guideline_id = "target-guideline-id"

    # Mock team object returned by get_team
    mock_team = MagicMock()
    mock_team.branding_guidelines = [
        {"id": "other-id", "name": "Other", "type": "text", "content": "foo"},
        {"id": guideline_id, "name": "Target", "type": "text", "content": "bar"},
    ]
    mock_get_team.return_value = mock_team

    # Act
    delete_branding_guideline(team_id, guideline_id)

    # Assert
    mock_db.collection.assert_called_once_with(config.TEAMS_COLLECTION_NAME)
    mock_db.collection.return_value.document.assert_called_once_with(team_id)
    mock_doc.update.assert_called_once()

    # Verify ArrayRemove was used on the correct guideline dict
    args, _ = mock_doc.update.call_args
    assert "branding_guidelines" in args[0]  # noqa: S101
    remove_arg = args[0]["branding_guidelines"]
    assert isinstance(remove_arg, firestore.ArrayRemove)  # noqa: S101
