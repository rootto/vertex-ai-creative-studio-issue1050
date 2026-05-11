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

"""State for team management page."""

from dataclasses import field
import mesop as me


@me.stateclass
class PageState:
    teams: list[dict] = field(default_factory=list)
    new_team_name: str = ""
    selected_team_id: str = ""
    user_email_to_assign: str = ""
    role_to_assign: str = "contributor"
    guideline_type: str = "text"  # "text" or "pdf"
    guideline_text: str = ""
    pdf_gcs_uri: str = ""
    pdf_filename: str = ""
    is_extracting: bool = False
    show_snackbar: bool = False
    snackbar_message: str = ""
