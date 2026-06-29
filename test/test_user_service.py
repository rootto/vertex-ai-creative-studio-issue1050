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

"""Unit tests for user service."""

import os

# Set dummy environment variables to prevent Gemini client init error during import
os.environ["PROJECT_ID"] = "dummy-project"
os.environ["LOCATION"] = "us-central1"

from unittest.mock import MagicMock, patch

from config.default import Default
from services.user_service import bootstrap_user

config = Default()


@patch("services.user_service.db")
@patch("services.user_service.create_team")
@patch("services.user_service.set_user_role")
def test_bootstrap_user_first_user(
    mock_set_user_role: MagicMock,
    mock_create_team: MagicMock,
    mock_db: MagicMock,
) -> None:
    """Test that the first user is bootstrapped as administrator and gets a team."""
    # Arrange
    mock_users_ref = MagicMock()
    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_db.collection.return_value = mock_users_ref
    mock_users_ref.document.return_value = mock_doc_ref
    mock_doc_ref.get.return_value = mock_doc
    mock_doc.exists = False  # User does not exist yet

    # Simulate empty users collection (first user ever)
    mock_users_ref.limit.return_value.stream.return_value = []

    email = "admin@example.com"

    # Act
    bootstrap_user(email)

    # Assert
    mock_db.collection.assert_called_with(config.USERS_COLLECTION_NAME)
    mock_users_ref.document.assert_called_with(email)
    mock_set_user_role.assert_called_once_with(email, "administrator")
    mock_create_team.assert_called_once_with(
        name=f"Team {email}",
        created_by=email,
    )


@patch("services.user_service.db")
@patch("services.user_service.create_team")
@patch("services.user_service.set_user_role")
def test_bootstrap_user_subsequent_user(
    mock_set_user_role: MagicMock,
    mock_create_team: MagicMock,
    mock_db: MagicMock,
) -> None:
    """Test that subsequent users are bootstrapped as contributor and get a team."""
    # Arrange
    mock_users_ref = MagicMock()
    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_db.collection.return_value = mock_users_ref
    mock_users_ref.document.return_value = mock_doc_ref
    mock_doc_ref.get.return_value = mock_doc
    mock_doc.exists = False  # User does not exist yet

    # Simulate non-empty users collection (other users exist)
    mock_users_ref.limit.return_value.stream.return_value = [MagicMock()]

    email = "contributor@example.com"

    # Act
    bootstrap_user(email)

    # Assert
    mock_db.collection.assert_called_with(config.USERS_COLLECTION_NAME)
    mock_users_ref.document.assert_called_with(email)
    mock_set_user_role.assert_called_once_with(email, "contributor")
    mock_create_team.assert_called_once_with(
        name=f"Team {email}",
        created_by=email,
    )


@patch("services.user_service.db")
@patch("services.user_service.create_team")
@patch("services.user_service.set_user_role")
def test_bootstrap_user_existing_user(
    mock_set_user_role: MagicMock,
    mock_create_team: MagicMock,
    mock_db: MagicMock,
) -> None:
    """Test that an existing user is not bootstrapped again and no team is created."""
    # Arrange
    mock_users_ref = MagicMock()
    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_db.collection.return_value = mock_users_ref
    mock_users_ref.document.return_value = mock_doc_ref
    mock_doc_ref.get.return_value = mock_doc
    mock_doc.exists = True  # User already exists

    email = "existing@example.com"

    # Act
    bootstrap_user(email)

    # Assert
    mock_db.collection.assert_called_with(config.USERS_COLLECTION_NAME)
    mock_users_ref.document.assert_called_with(email)
    mock_set_user_role.assert_not_called()
    mock_create_team.assert_not_called()
