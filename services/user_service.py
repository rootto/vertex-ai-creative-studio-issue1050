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

"""User service for handling roles and bootstrapping."""

from common.analytics import get_logger
from config.default import Default
from config.firebase_config import FirebaseClient
from services.team_service import create_team

config = Default()
db = FirebaseClient(database_id=config.GENMEDIA_FIREBASE_DB).get_client()
logger = get_logger(__name__)


def get_user_role(email: str) -> str:
    """Retrieve the role of a user by email."""
    logger.info(
        f"DEBUG: get_user_role called for {email}. DB ID={config.GENMEDIA_FIREBASE_DB}",
    )
    if not db:
        logger.warning("Firestore client is not initialized.")
        return "contributor"
    try:
        user_ref = db.collection(config.USERS_COLLECTION_NAME).document(email)
        doc = user_ref.get()
        if doc.exists:
            return doc.to_dict().get("role", "contributor")
        return "contributor"
    except Exception:
        logger.exception(f"Error fetching user role for {email}")
        return "contributor"


def set_user_role(email: str, role: str) -> None:
    """Set the role of a user."""
    if not db:
        logger.warning("Firestore client is not initialized.")
        return
    try:
        user_ref = db.collection(config.USERS_COLLECTION_NAME).document(email)
        user_ref.set({"role": role}, merge=True)
        logger.info(f"Set role {role} for user {email}")
    except Exception:
        logger.exception(f"Error setting user role for {email}")
        raise


def bootstrap_user(email: str) -> None:
    """Bootstrap a user upon login.

    If the users collection is completely empty, the first user is bootstrapped as
    an 'administrator'. Subsequent new users are bootstrapped as 'contributor'.
    Every user is checked to ensure they have their own individual team 'Team <email>'.
    If it is missing, it is created.
    """
    if not db:
        logger.warning("Firestore client is not initialized.")
        return
    try:
        users_ref = db.collection(config.USERS_COLLECTION_NAME)
        doc = users_ref.document(email).get()

        if not doc.exists:
            # Check if this is the first user in the entire system
            docs = users_ref.limit(1).stream()
            doc_list = list(docs)

            role = "administrator" if not doc_list else "contributor"
            set_user_role(email, role)
            logger.info(f"Bootstrapped new user {email} with role {role}")

        # Ensure the user has their personal team "Team <email>"
        teams_ref = db.collection(config.TEAMS_COLLECTION_NAME)
        personal_team_query = (
            teams_ref.where("name", "==", f"Team {email}").limit(1).stream()
        )
        if not list(personal_team_query):
            team_id = create_team(name=f"Team {email}", created_by=email)
            logger.info(
                f"Automatically created missing individual team 'Team {email}' (ID: {team_id}) for {email}",
            )
    except Exception:
        logger.exception(f"Error bootstrapping user {email}")
        raise
