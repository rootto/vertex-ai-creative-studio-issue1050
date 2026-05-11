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

"""Team service for handling team operations."""

from dataclasses import asdict

from google.cloud import firestore

from common.analytics import get_logger
from common.metadata import MediaItem, Team, _create_media_item_from_dict, get_media_item_by_id
from config.default import Default
from config.firebase_config import FirebaseClient
from models.gemini import generate_text

config = Default()
db = FirebaseClient(database_id=config.GENMEDIA_FIREBASE_DB).get_client()
logger = get_logger(__name__)


def create_team(name: str, created_by: str) -> str:
    """Create a new team."""
    if not db:
        logger.warning("Firestore client is not initialized.")
        return ""
    try:
        team_ref = db.collection(config.TEAMS_COLLECTION_NAME).document()
        team = Team(id=team_ref.id, name=name, created_by=created_by, managers=[created_by], members=[created_by])
        team_ref.set(asdict(team))
        logger.info(f"Created team {name} with ID {team_ref.id}")
        return team_ref.id
    except Exception as e:
        logger.error(f"Error creating team {name}: {e}")
        raise e


def get_team(team_id: str) -> Team | None:
    """Retrieve a team by ID."""
    if not db:
        return None
    try:
        doc_ref = db.collection(config.TEAMS_COLLECTION_NAME).document(team_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            # Fetch assets by ID from genmedia collection
            asset_ids = data.get("asset_ids", [])
            assets = []
            for asset_id in asset_ids:
                assets.append(get_media_item_by_id(asset_id))
            data["assets"] = assets
            data["id"] = doc.id
            return Team(**data)
        return None
    except Exception as e:
        logger.error(f"Error fetching team {team_id}: {e}")
        return None


def add_manager_to_team(team_id: str, manager_email: str):
    """Add a manager to a team."""
    try:
        team_ref = db.collection(config.TEAMS_COLLECTION_NAME).document(team_id)
        team_ref.update({"managers": firestore.ArrayUnion([manager_email])})
        logger.info(f"Added manager {manager_email} to team {team_id}")
    except Exception as e:
        logger.error(f"Error adding manager to team {team_id}: {e}")
        raise e


def add_member_to_team(team_id: str, member_email: str):
    """Add a member to a team."""
    try:
        team_ref = db.collection(config.TEAMS_COLLECTION_NAME).document(team_id)
        team_ref.update({"members": firestore.ArrayUnion([member_email])})
        logger.info(f"Added member {member_email} to team {team_id}")
    except Exception as e:
        logger.error(f"Error adding member to team {team_id}: {e}")
        raise e


def add_asset_to_team(team_id: str, media_item: MediaItem):
    """Add an asset to a team."""
    try:
        team_ref = db.collection(config.TEAMS_COLLECTION_NAME).document(team_id)
        # Store only the reference ID
        team_ref.update({"asset_ids": firestore.ArrayUnion([media_item.id])})
        logger.info(f"Added asset reference {media_item.id} to team {team_id}")
    except Exception as e:
        logger.error(f"Error adding asset to team {team_id}: {e}")
        raise e

def delete_team(team_id: str):
    """Delete a team."""
    try:
        db.collection(config.TEAMS_COLLECTION_NAME).document(team_id).delete()
        logger.info(f"Deleted team {team_id}")
    except Exception as e:
        logger.error(f"Error deleting team {team_id}: {e}")
        raise e


def remove_asset_from_team(team_id: str, asset_id: str):
    """Remove an asset reference from a team."""
    try:
        team_ref = db.collection(config.TEAMS_COLLECTION_NAME).document(team_id)
        team_ref.update({"asset_ids": firestore.ArrayRemove([asset_id])})
        logger.info(f"Removed asset reference {asset_id} from team {team_id}")
    except Exception as e:
        logger.error(f"Error removing asset from team {team_id}: {e}")
        raise e


def set_branding_guideline(
    team_id: str,
    guideline_type: str,
    content: str,
    extracted_text: str = None,
):
    """Set branding guidelines for a team."""
    try:
        team_ref = db.collection(config.TEAMS_COLLECTION_NAME).document(team_id)
        update_data = {
            "branding_guideline": {"type": guideline_type, "content": content},
        }
        if extracted_text:
            update_data["extracted_text"] = extracted_text
        team_ref.update(update_data)
        logger.info(f"Set branding guideline for team {team_id}")
    except Exception as e:
        logger.error(f"Error setting branding guideline for team {team_id}: {e}")
        raise e


def extract_branding_guidelines(pdf_gcs_uri: str) -> str:
    """Extract branding guidelines from a PDF using Gemini."""
    prompt = "Analyze this brand guidelines PDF. Extract the following visual identity elements: Color Palette (hex codes if available), Visual Style (e.g., minimalist, vibrant), Key Imagery Rules (Do's and Don'ts). Summarize this into a concise paragraph for an image generation prompt."
    try:
        # Using gemini-3.1-pro-preview as corrected by user
        text, _ = generate_text(
            prompt=prompt,
            images=[pdf_gcs_uri],
            model_name="gemini-3.1-pro-preview",
        )
        return text
    except Exception as e:
        logger.error(f"Error extracting guidelines from {pdf_gcs_uri}: {e}")
        raise e


def get_teams_for_user(
    email: str, role: str, assigned_only: bool = False,
) -> list[Team]:
    """Get teams for a user based on their role."""
    if not db:
        return []
    try:
        query = db.collection(config.TEAMS_COLLECTION_NAME)

        if assigned_only:
            # Query for teams where user is member or manager
            docs_members = query.where("members", "array_contains", email).stream()
            docs_managers = query.where("managers", "array_contains", email).stream()

            docs = []
            seen_ids = set()
            for doc in docs_members:
                if doc.id not in seen_ids:
                    docs.append(doc)
                    seen_ids.add(doc.id)
            for doc in docs_managers:
                if doc.id not in seen_ids:
                    docs.append(doc)
                    seen_ids.add(doc.id)
        elif role == "administrator":
            # Admins see all teams
            docs = query.stream()
        elif role == "manager":
            # Managers see teams they manage
            docs = query.where("managers", "array_contains", email).stream()
        else:
            # Contributors see teams they are members of
            docs = query.where("members", "array_contains", email).stream()

        teams = []
        for doc in docs:
            data = doc.to_dict()
            asset_ids = data.get("asset_ids", [])
            assets = []
            for asset_id in asset_ids:
                assets.append(get_media_item_by_id(asset_id))
            data["assets"] = assets
            data["id"] = doc.id
            teams.append(Team(**data))
        return teams
    except Exception as e:
        logger.error(f"Error fetching teams for user {email}: {e}")
        return []
