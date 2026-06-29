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
    add_branding_guideline,
    delete_branding_guideline,
    extract_branding_guidelines,
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


def _load_team_guidelines(page_state: PageState, team: Team) -> None:
    """Load team guidelines into state."""
    if team.branding_guideline:
        page_state.guideline_type = team.branding_guideline.get("type", "text")
        page_state.guideline_text = team.branding_guideline.get("content", "")
        page_state.pdf_filename = team.branding_guideline.get("filename", "")
        page_state.pdf_gcs_uri = team.branding_guideline.get("gcs_uri", "")
    else:
        page_state.guideline_type = "text"
        page_state.guideline_text = ""
        page_state.pdf_filename = ""
        page_state.pdf_gcs_uri = ""


def _get_role_label(team: Team, email: str, global_role: str) -> str:
    """Get the role label for a user in a team."""
    if global_role == "administrator":
        return "Administrator"
    if email in team.managers:
        return "Manager"
    if email in team.members:
        return "Contributor"
    return "None"


def team_assets_content() -> None:
    """Provide main content for team assets page."""
    app_state = me.state(AppState)
    page_state = me.state(PageState)

    snackbar(is_visible=page_state.show_snackbar, label=page_state.snackbar_message)

    teams = get_teams_for_user(app_state.user_email, app_state.user_role)
    is_manager_of_any_team = any(app_state.user_email in t.managers for t in teams)

    if app_state.user_role != "administrator" and not is_manager_of_any_team:
        with me.box(style=me.Style(padding=me.Padding.all(24))):
            me.text(
                "You do not have permission to view this page.",
                type="headline-6",
                style=me.Style(color=me.theme_var("error")),
            )
        return

    if not teams:

        with me.box(style=me.Style(padding=me.Padding.all(24))):
            me.text("You are not part of any teams.")
        return

    if not page_state.selected_team_id and teams:
        page_state.selected_team_id = teams[0].id

    # Refresh team data to get latest assets
    selected_team = get_team(page_state.selected_team_id)

    if not page_state.initial_load_complete and selected_team:
        _load_team_guidelines(page_state, selected_team)
        page_state.initial_load_complete = True

    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            gap=24,
            padding=me.Padding.all(24),
        ),
    ):
        # Team Selector
        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="row",
                gap=16,
                align_items="center",
            ),
        ):
            me.text("Select Team:", type="subtitle-1")
            me.select(
                label="Team",
                options=[
                    me.SelectOption(
                        label=f"{t.name} ({_get_role_label(t, app_state.user_email, app_state.user_role)})",
                        value=t.id,
                    )
                    for t in teams
                ],
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
                label="Select Assets",
                accepted_file_types=["image/jpeg", "image/png", "video/mp4"],
                on_upload=on_upload_assets,
                multiple=True,
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

        # List existing guidelines
        if selected_team.branding_guidelines:
            with me.box(style=me.Style(margin=me.Margin(bottom=16))):
                me.text("Existing Guidelines:", type="subtitle-1")
                for g in selected_team.branding_guidelines:
                    with me.box(
                        style=me.Style(
                            display="flex",
                            flex_direction="row",
                            align_items="center",
                            gap=16,
                            padding=me.Padding.symmetric(vertical=4),
                        ),
                    ):
                        me.text(
                            f"• {g.get('name')} ({g.get('type').upper()})",
                            style=me.Style(flex_grow=1),
                        )
                        if g.get("type") == "pdf" and g.get("extracted_text"):
                            with me.box(
                                style=me.Style(
                                    max_height=80,
                                    overflow_y="auto",
                                    font_size=12,
                                    background=me.theme_var("secondary-container"),
                                    padding=me.Padding.all(4),
                                    border_radius=4,
                                    width="50%",
                                ),
                            ):
                                me.text(g.get("extracted_text"))

        me.text(
            "Add New Guideline",
            type="subtitle-1",
            style=me.Style(margin=me.Margin(top=16)),
        )

        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="column",
                gap=16,
                margin=me.Margin(top=8),
            ),
        ):
            with me.box(
                style=me.Style(
                    display="flex",
                    flex_direction="row",
                    gap=16,
                    align_items="center",
                ),
            ):
                me.input(
                    label="Guideline Name",
                    value=page_state.guideline_name,
                    on_blur=on_guideline_name_blur,
                    style=me.Style(width="250px"),
                )
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
                    style=me.Style(width="100%"),
                    rows=10,
                )
            else:
                with me.box(
                    style=me.Style(
                        display="flex",
                        flex_direction="row",
                        gap=8,
                        align_items="center",
                        width="100%",
                    ),
                ):
                    me.uploader(
                        label="Upload PDF",
                        accepted_file_types=["application/pdf"],
                        on_upload=on_upload_pdf,
                    )
                    if page_state.pdf_filename:
                        me.text(f"File: {page_state.pdf_filename}")
                        with me.content_button(
                            on_click=on_clear_pdf,
                            type="stroked",
                        ):
                            me.icon("clear")

            me.button(
                "Add Guideline",
                on_click=on_save_guidelines_click,
                key=selected_team.id,
                type="raised",
                style=me.Style(align_self="flex-start"),
            )


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
                        with me.box(
                            style=me.Style(
                                display="flex",
                                flex_direction="row",
                                align_items="center",
                                justify_content="space-between",
                                width="100%",
                                margin=me.Margin(top=4),
                            ),
                        ):
                            me.text(
                                asset.prompt or "Asset",
                                type="caption",
                                style=me.Style(flex_grow=1),
                            )
                            with me.content_button(
                                on_click=on_delete_asset_click,
                                key=f"{selected_team.id}:{asset.id}",
                                style=me.Style(
                                    padding=me.Padding.all(0), min_width=24, height=24,
                                ),
                            ):
                                me.icon(
                                    "delete",
                                    style=me.Style(color=me.theme_var("error")),
                                )


def on_select_team_change(e: me.SelectSelectionChangeEvent) -> None:
    """Handle team selection change."""
    state = me.state(PageState)
    state.selected_team_id = e.value
    team = get_team(e.value)
    if team:
        _load_team_guidelines(state, team)


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
                "team_assets",
                filename,
                mime_type,
                contents,
            )

            team = get_team(state.selected_team_id)
            team_name = team.name if team else "Unknown Team"

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
                tags=[team_name],
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
    file = e.file
    gcs_uri = store_to_gcs(
        "brand_guidelines",
        file.name,
        file.mime_type,
        file.getvalue(),
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


def on_guideline_name_blur(e: me.InputBlurEvent) -> None:
    """Handle guideline name blur."""
    state = me.state(PageState)
    state.guideline_name = e.value


def on_save_guidelines_click(e: me.ClickEvent):  # noqa: ANN201
    """Handle save guidelines click."""
    team_id = e.key
    state = me.state(PageState)
    if not state.guideline_name.strip():
        state.show_snackbar = True
        state.snackbar_message = "Guideline name cannot be empty."
        yield
        return

    try:
        if state.guideline_type == "text":
            add_branding_guideline(
                team_id,
                state.guideline_name,
                "text",
                state.guideline_text,
            )
            state.show_snackbar = True
            state.snackbar_message = "Guideline added successfully."
            state.guideline_name = ""
            state.guideline_text = ""
        else:
            # For PDF, we add it with empty extracted text first
            guideline_id = add_branding_guideline(
                team_id,
                state.guideline_name,
                "pdf",
                state.pdf_gcs_uri,
                filename=state.pdf_filename,
            )

            # Start background thread to extract PDF text guidelines using Gemini
            import threading

            def run_extraction():
                try:
                    extracted_text = extract_branding_guidelines(state.pdf_gcs_uri)
                    # We need to update the specific guideline inside the list.
                    # A simple way is to delete the one we just added and add it back with extracted text,
                    # or update it. To keep it simple, we can implement an update function if needed,
                    # but let's just update the document in Firestore directly.
                    from services.team_service import config, db

                    team_ref = db.collection(config.TEAMS_COLLECTION_NAME).document(
                        team_id,
                    )
                    team_doc = team_ref.get()
                    if team_doc.exists:
                        guidelines = team_doc.to_dict().get("branding_guidelines", [])
                        for g in guidelines:
                            if g.get("id") == guideline_id:
                                g["extracted_text"] = extracted_text
                                break
                        team_ref.update({"branding_guidelines": guidelines})
                except Exception as ex:
                    print(f"Error in background guideline extraction: {ex}")

            threading.Thread(target=run_extraction).start()
            state.show_snackbar = True
            state.snackbar_message = (
                "Guideline added. PDF text extraction started in background."
            )
            state.guideline_name = ""
            state.pdf_filename = ""
            state.pdf_gcs_uri = ""
    except Exception as ex:  # noqa: BLE001
        state.show_snackbar = True
        state.snackbar_message = f"Error adding guideline: {ex}"
    yield


def on_delete_guideline_click(e: me.ClickEvent):  # noqa: ANN201
    """Handle delete guideline click."""
    team_id, guideline_id = e.key.split(":")
    try:
        delete_branding_guideline(team_id, guideline_id)
        state = me.state(PageState)
        state.snackbar_message = "Guideline deleted successfully."
        state.show_snackbar = True
    except Exception as ex:  # noqa: BLE001
        state = me.state(PageState)
        state.snackbar_message = f"Error deleting guideline: {ex}"
        state.show_snackbar = True
    yield


def on_delete_asset_click(e: me.ClickEvent):
    """Handle delete asset click."""
    state = me.state(PageState)
    team_id, asset_id = e.key.split(":")
    try:
        from services.team_service import remove_asset_from_team

        remove_asset_from_team(team_id, asset_id)
        state.snackbar_message = "Asset removed successfully."
        state.show_snackbar = True
    except Exception as ex:  # noqa: BLE001
        state.snackbar_message = f"Error removing asset: {ex}"
        state.show_snackbar = True
    yield
