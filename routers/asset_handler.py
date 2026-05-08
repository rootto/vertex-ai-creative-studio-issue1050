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

from fastapi import APIRouter, HTTPException, Request
from common.utils import create_display_url
from common.storage import get_or_create_session

router = APIRouter()

@router.get("/api/get_asset_url")
async def get_asset_url(request: Request, gcs_uri: str):
    """Returns a signed URL for a GCS asset if the user is authenticated."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Unauthorized: No session ID found.")
    
    session = get_or_create_session(session_id, "anonymous@google.com")
    if session.user_email == "anonymous@google.com":
        raise HTTPException(status_code=401, detail="Unauthorized: User not signed in.")
    
    if not gcs_uri.startswith("gs://"):
        raise HTTPException(status_code=400, detail="Invalid GCS URI.")
    
    try:
        url = create_display_url(gcs_uri)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {e}")
