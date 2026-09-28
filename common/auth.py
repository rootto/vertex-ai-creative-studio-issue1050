# Copyright 2025 Google LLC
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
"""FastAPI middleware for request identity and session state."""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request
from google.auth.transport import requests
from google.oauth2 import id_token
from starlette.responses import Response

from common.identity import ANONYMOUS_USER_EMAIL, get_authenticated_user_email
from common.storage import get_or_create_session
from config.default import Default

cfg = Default()


def verify_google_id_token(id_token_str: str) -> dict:
    """Verifies a Google ID Token and returns the token payload.
    Raises ValueError if the token is invalid.
    """
    return id_token.verify_oauth2_token(
        id_token_str,
        requests.Request(),
        cfg.GOOGLE_CLIENT_ID,
    )


async def set_user_identity_and_session(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Set user identity and session information."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())

    user_email = get_authenticated_user_email(request.headers)
    if not user_email:
        session = get_or_create_session(session_id, ANONYMOUS_USER_EMAIL)
        user_email = session.user_email or ANONYMOUS_USER_EMAIL
    else:
        get_or_create_session(session_id, user_email)

    request.state.user_email = user_email
    request.state.session_id = session_id

    response = await call_next(request)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="Lax",
        secure=True,
        path="/",
    )

    return response
