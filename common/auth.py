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

import uuid

from fastapi import Request
from google.oauth2 import id_token
from google.auth.transport import requests

from common.storage import get_or_create_session
from config.default import Default

cfg = Default()

def verify_google_id_token(id_token_str: str) -> dict:
    """Verifies a Google ID Token and returns the token payload.
    Raises ValueError if the token is invalid.
    """
    return id_token.verify_oauth2_token(id_token_str, requests.Request(), cfg.GOOGLE_CLIENT_ID)


async def set_user_identity_and_session(request: Request, call_next):
    """FastAPI middleware to set user identity and session information.
    """
    # Get user email from header - assuming IAP
    user_email = request.headers.get("X-Goog-Authenticated-User-Email")
    if not user_email:
        # Fallback for local development or unauthenticated access
        user_email = "anonymous@google.com"

    # Get or create session ID from cookie
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())

    # Attach user and session info to the request state
    request.state.user_email = user_email
    request.state.session_id = session_id

    # Ensure session exists in Firestore
    get_or_create_session(session_id, user_email)

    response = await call_next(request)

    # Set session ID cookie on the response
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, samesite="Lax",
    )

    return response
