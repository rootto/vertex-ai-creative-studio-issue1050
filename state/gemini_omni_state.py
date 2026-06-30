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
"""State for Gemini Omni page."""

import mesop as me


@me.stateclass
class PageState:
    """Page state for Gemini Omni workflow."""

    prompt: str = (
        "A golden retriever running joyfully through a field of wildflowers at sunset."
    )
    generation_mode: str = "t2v"  # t2v, i2v, r2v, editing
    model_version: str = "gemini-omni-flash-preview"
    aspect_ratio: str = "16:9"
    duration: int = 10

    # UI Flow states
    is_loading: bool = False
    error_message: str = ""
    show_error_dialog: bool = False

    # Outputs
    generated_video_url: str = ""  # Base64 data URL or HTTP display URL
    generated_video_gcs: str = ""

    # Image-to-Video inputs
    i2v_image_file_key: int = 0
    i2v_image_gcs: str = ""
    i2v_image_display_url: str = ""
    i2v_image_mime_type: str = ""

    # Reference-to-Video inputs (JSON serialized list to avoid serialization bugs)
    # Schema: list[dict] where dict contains {"gcs_uri": str, "display_url": str, "mime_type": str}
    r2v_images_json: str = "[]"
    r2v_upload_key: int = 0

    # Video Editing inputs
    edit_video_file_key: int = 0
    edit_video_gcs: str = ""
    edit_video_display_url: str = ""
    edit_video_mime_type: str = ""

    edit_style_image_file_key: int = 0
    edit_style_image_gcs: str = ""
    edit_style_image_display_url: str = ""
    edit_style_image_mime_type: str = ""
