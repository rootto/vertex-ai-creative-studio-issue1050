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

"""Team assets page."""

import datetime

import mesop as me

from common.metadata import MediaItem, add_media_item_to_firestore
from common.storage import store_to_gcs
from common.utils import create_display_url
from components.header import header
from components.page_scaffold import page_frame, page_scaffold
from components.snackbar import snackbar
from services.team_service import (
    add_asset_to_team,
    get_team,
    get_teams_for_user,
)
from state.state import AppState
from state.team_assets_state import PageState


@me.page(
    path="/team_assets",
    title="Team Assets - GenMedia Creative Studio",
)
def page() -> None:
    """Team assets page."""
    with page_scaffold(page_name="team_assets"), page_frame():
        header("Team Assets", "folder")
        team_assets_content()


def team_assets_content() -> None:
    """Provide main content for team assets page."""
    app_state = me.state(AppState)
    page_state = me.state(PageState)

    if app_state.user_role not in ["administrator", "manager"]:
        with me.box(style=me.Style(padding=me.Padding.all(24))):
            me.text(
                "You do not have permission to view this page.",
                type="headline-6",
                style=me.Style(color=me.theme_var("error")),
            )
        return

    snackbar(is_visible=page_state.show_snackbar, label=page_state.snackbar_message)

    teams = get_teams_for_user(app_state.user_email, app_state.user_role)

    if not teams:
        with me.box(style=me.Style(padding=me.Padding.all(24))):
            me.text("You are not part of any teams.")
        return

    if not page_state.selected_team_id and teams:
        page_state.selected_team_id = teams[0].id

    # Refresh team data to get latest assets
    selected_team = get_team(page_state.selected_team_id)

    with me.box(
        style=me.Style(
            display="flex", flex_direction="column", gap=24, padding=me.Padding.all(24),
        ),
    ):
        # Team Selector
        with me.box(
            style=me.Style(
                display="flex", flex_direction="row", gap=16, align_items="center",
            ),
        ):
            me.text("Select Team:", type="subtitle-1")
            me.select(
                label="Team",
                options=[me.SelectOption(label=t.name, value=t.id) for t in teams],
                value=page_state.selected_team_id,
                on_selection_change=on_select_team_change,
            )

        if selected_team:
            # Upload Section
            with me.box(
                style=me.Style(
                    background=me.theme_var("surface"),
                    padding=me.Padding.all(16),
                    border_radius=8,
                ),
            ):
                me.text("Upload Assets", type="headline-6")
                me.text("Supported types: JPEG, PNG", type="caption")

                with me.box(style=me.Style(margin=me.Margin(top=8))):
                    me.uploader(
                        label="Select Images",
                        accepted_file_types=["image/jpeg", "image/png"],
                        on_upload=on_upload_assets,
                        type="flat",
                        color="primary",
                    )

                if page_state.is_uploading:
                    me.progress_spinner()

            # Assets Display
            with me.box(
                style=me.Style(
                    background=me.theme_var("surface"),
                    padding=me.Padding.all(16),
                    border_radius=8,
                ),
            ):
                me.text("Team Assets", type="headline-6")

                if not selected_team.assets:
                    me.text("No assets uploaded yet.")
                else:
                    with me.box(
                        style=me.Style(
                            display="flex",
                            flex_direction="row",
                            flex_wrap="wrap",
                            gap=16,
                            margin=me.Margin(top=16),
                        ),
                    ):
                        for asset in selected_team.assets:
                            with me.box(
                                style=me.Style(
                                    width=150,
                                    display="flex",
                                    flex_direction="column",
                                    align_items="center",
                                ),
                            ):
                                display_url = create_display_url(asset.gcsuri)
                                me.image(
                                    src=display_url,
                                    style=me.Style(
                                        width="100%",
                                        height=150,
                                        object_fit="cover",
                                        border_radius=4,
                                    ),
                                )
                                me.text(
                                    asset.prompt or "Asset",
                                    type="caption",
                                    style=me.Style(margin=me.Margin(top=4)),
                                )


def on_select_team_change(e: me.SelectSelectionChangeEvent) -> None:
    """Handle team selection change."""
    state = me.state(PageState)
    state.selected_team_id = e.value


def on_upload_assets(e: me.UploadEvent):  # noqa: ANN201
    """Handle multi-file upload for team assets."""
    state = me.state(PageState)
    app_state = me.state(AppState)
    state.is_uploading = True
    yield

    try:
        success_count = 0
        for file in e.files:
            contents = file.getvalue()
            mime_type = file.mime_type
            filename = file.name

            # Store to GCS
            gcs_uri = store_to_gcs(
                "team_assets", filename, mime_type, contents,
            )

            # Create MediaItem
            media_item = MediaItem(
                status="complete",
                user_email=app_state.user_email,
                team_id=state.selected_team_id,
                timestamp=datetime.datetime.utcnow(),
                mime_type=mime_type,
                gcsuri=gcs_uri,
                prompt=f"Asset uploaded by {app_state.user_email}",
                comment="team asset",
            )

            # Add to library (sets media_item.id)
            add_media_item_to_firestore(media_item)

            # Add to team
            add_asset_to_team(state.selected_team_id, media_item)
            success_count += 1

        state.snackbar_message = f"Successfully uploaded {success_count} assets."
        state.show_snackbar = True
    except Exception as ex:  # noqa: BLE001
        state.snackbar_message = f"Error uploading assets: {ex}"
        state.show_snackbar = True
    finally:
        state.is_uploading = False
        yield
