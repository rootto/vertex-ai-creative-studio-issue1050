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

from common.metadata import MediaItem, Team, add_media_item_to_firestore
from common.storage import store_to_gcs
from common.utils import create_display_url
from components.header import header
from components.page_scaffold import page_frame, page_scaffold
from components.snackbar import snackbar
from services.team_service import (
    add_asset_to_team,
    extract_branding_guidelines,
    get_team,
    get_teams_for_user,
    set_branding_guideline,
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
            upload_assets_section(page_state)
            branding_guidelines_section(selected_team, page_state)
            assets_display_section(selected_team)


def upload_assets_section(page_state: PageState) -> None:
    """Render the upload assets section."""
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


def branding_guidelines_section(selected_team: Team, page_state: PageState) -> None:
    """Render the branding guidelines section."""
    with me.box(
        style=me.Style(
            background=me.theme_var("surface"),
            padding=me.Padding.all(16),
            border_radius=8,
            margin=me.Margin(top=16),
                ),
            ):
                me.text("Branding Guidelines", type="headline-6")

                with me.box(
                    style=me.Style(
                        display="flex",
                        flex_direction="row",
                        gap=16,
                        align_items="center",
                    ),
                ):
                    type_options = [
                        me.SelectOption(label="Free Text", value="text"),
                        me.SelectOption(label="PDF Upload", value="pdf"),
                    ]
                    me.select(
                        label="Type",
                        options=type_options,
                        on_selection_change=on_guideline_type_change,
                        value=page_state.guideline_type,
                        style=me.Style(width="150px"),
                    )

                    if page_state.guideline_type == "text":
                        me.textarea(
                            label="Enter Guidelines",
                            value=page_state.guideline_text,
                            on_blur=on_guideline_text_blur,
                            style=me.Style(flex_grow=1),
                            rows=3,
                        )
                    else:
                        with me.box(
                            style=me.Style(
                                display="flex",
                                flex_direction="row",
                                gap=8,
                                align_items="center",
                                flex_grow=1,
                            ),
                        ):
                            me.upload_button(
                                "Upload PDF",
                                on_upload=on_upload_pdf,
                                accept="application/pdf",
                                type="stroked",
                            )
                            if page_state.pdf_filename:
                                me.text(f"File: {page_state.pdf_filename}")
                                me.button(
                                    "Clear",
                                    on_click=on_clear_pdf,
                                    type="icon",
                                    icon="clear",
                                )

                                if (
                                    not selected_team.extracted_text
                                    and not page_state.is_extracting
                                ):
                                    me.button(
                                        "Extract Text",
                                        on_click=lambda e, t_id=selected_team.id: (
                                            on_extract_click(e, t_id)
                                        ),
                                        type="raised",
                                    )

                                if page_state.is_extracting:
                                    me.progress_spinner(diameter=24)

                    me.button(
                        "Save",
                        on_click=lambda e, t_id=selected_team.id: (
                            on_save_guidelines_click(e, t_id)
                        ),
                        type="raised",
                    )

                if selected_team.extracted_text:
                    with me.box(
                        style=me.Style(
                            margin=me.Margin(top=8),
                            padding=me.Padding.all(8),
                            background=me.theme_var("secondary-container"),
                            border_radius=4,
                        ),
                    ):
                        me.text(
                            "Extracted Guidelines Summary:",
                            type="subtitle-2",
                        )
                        me.text(selected_team.extracted_text)


def assets_display_section(selected_team: Team) -> None:
    """Render the assets display section."""
    with me.box(
        style=me.Style(
            background=me.theme_var("surface"),
            padding=me.Padding.all(16),
            border_radius=8,
            margin=me.Margin(top=16),
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


def on_guideline_type_change(e: me.SelectSelectionChangeEvent) -> None:
    """Handle guideline type change."""
    state = me.state(PageState)
    state.guideline_type = e.value


def on_guideline_text_blur(e: me.InputBlurEvent) -> None:
    """Handle guideline text blur."""
    state = me.state(PageState)
    state.guideline_text = e.value


def on_upload_pdf(e: me.UploadEvent):  # noqa: ANN201
    """Handle PDF upload for branding guidelines."""
    state = me.state(PageState)
    file = e.files[0]
    gcs_uri = store_to_gcs(
        "brand_guidelines", file.name, file.mime_type, file.getvalue(),
    )
    state.pdf_gcs_uri = gcs_uri
    state.pdf_filename = file.name
    yield


def on_clear_pdf(_: me.ClickEvent):  # noqa: ANN201
    """Handle clearing the uploaded PDF."""
    state = me.state(PageState)
    state.pdf_gcs_uri = ""
    state.pdf_filename = ""
    state.guideline_text = ""
    yield


def on_extract_click(_: me.ClickEvent, team_id: str):  # noqa: ANN201
    """Handle extract text click."""
    state = me.state(PageState)
    state.is_extracting = True
    yield
    try:
        extracted_text = extract_branding_guidelines(state.pdf_gcs_uri)
        set_branding_guideline(team_id, "pdf", state.pdf_gcs_uri, extracted_text)
        state.show_snackbar = True
        state.snackbar_message = "Guidelines extracted and saved successfully."
    except Exception as ex:  # noqa: BLE001
        state.show_snackbar = True
        state.snackbar_message = f"Error extracting guidelines: {ex}"
    finally:
        state.is_extracting = False
    yield


def on_save_guidelines_click(_: me.ClickEvent, team_id: str):  # noqa: ANN201
    """Handle save guidelines click."""
    state = me.state(PageState)
    try:
        if state.guideline_type == "text":
            set_branding_guideline(team_id, "text", state.guideline_text)
        else:
            set_branding_guideline(team_id, "pdf", state.pdf_gcs_uri)
        state.show_snackbar = True
        state.snackbar_message = "Guidelines saved successfully."
    except Exception as ex:  # noqa: BLE001
        state.show_snackbar = True
        state.snackbar_message = f"Error saving guidelines: {ex}"
    yield
