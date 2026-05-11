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

from unittest.mock import MagicMock, patch

from config.default import Default
from services.team_service import delete_team, remove_asset_from_team

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
