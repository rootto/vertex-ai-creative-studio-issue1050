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
"""Login page for GenMedia Creative Studio."""

from collections.abc import Generator

import mesop as me

from common.analytics import get_logger
from common.auth import verify_google_id_token
from common.storage import create_session
from components.login_component.login_component import login_component
from config.default import Default
from state.state import AppState, is_logged_in, update_user_and_session_info

logger = get_logger(__name__)


@me.stateclass
class PageState:
    """State class for the login page."""


def on_load(_e: me.LoadEvent) -> None:
    """Redirects the user to the welcome page if already logged in."""
    if is_logged_in():
        me.navigate("/welcome")


def on_login(e: me.WebEvent) -> Generator[None]:
    """Handle the login event by verifying the token and establishing a session."""
    logger.info(f"DEBUG: on_login entered. Event value: {e.value}")
    state = me.state(AppState)
    id_token_str = e.value["value"]

    try:
        id_info = verify_google_id_token(id_token_str)
        email = id_info["email"]
        logger.info(f"User logged in: {email}")

        # Persist session to Firestore
        create_session(state.session_id, email)

        # Update state with user email
        yield from update_user_and_session_info(email, state.session_id)

        # Navigate to welcome page
        me.navigate("/welcome")
    except Exception:
        logger.exception("Login failed")
    yield


def navigate_to_login(_e: me.ClickEvent) -> None:
    """Navigate to the login page."""
    me.navigate("/login")


@me.page(
    path="/login",
    title="Login - GenMedia Creative Studio",
    on_load=on_load,
)
def page() -> None:
    """Render the login page."""
    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            align_items="center",
            justify_content="center",
            height="100vh",
        ),
    ):
        me.text("Welcome to GenMedia Creative Studio", type="headline-4")
        me.text("Please sign in to access the application.")
        cfg = Default()
        login_component(client_id=cfg.GOOGLE_CLIENT_ID, on_login=on_login)
