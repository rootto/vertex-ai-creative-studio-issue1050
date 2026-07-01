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
"""Gemini Omni page."""

import json
from collections.abc import Generator

import mesop as me

from common.storage import store_to_gcs
from common.utils import create_display_url
from components.dialog import dialog, dialog_actions
from components.gemini_omni.media_uploaders import media_uploaders
from components.gemini_omni.settings_panel import settings_panel
from components.header import header
from components.page_scaffold import page_frame, page_scaffold
from models.gemini_omni import generate_omni_video
from state.gemini_omni_state import PageState
from state.state import AppState


def on_omni_load(_e: me.LoadEvent) -> Generator[None]:
    """Initialize the page state on load."""
    me.state(PageState)
    # We can load defaults here if needed
    yield


@me.page(
    path="/gemini-omni",
    title="Gemini Omni - GenMedia Creative Studio",
    on_load=on_omni_load,
    security_policy=me.SecurityPolicy(
        dangerously_disable_trusted_types=True,
        allowed_script_srcs=[
            "https://cdn.jsdelivr.net",
        ],
    ),
)
def gemini_omni_page() -> None:
    """Render the Gemini Omni page."""
    me.state(AppState)
    state = me.state(PageState)

    # 1. Error dialog
    if state.show_error_dialog:
        with dialog(is_open=state.show_error_dialog):
            me.text("Generation Error", type="headline-6")
            me.text(state.error_message)
            with dialog_actions():
                me.button("Close", on_click=on_close_error_dialog, type="flat")

    with page_scaffold(page_name="gemini-omni"), page_frame():
        header(
            "Gemini Omni",
            "movie_filter",
            show_info_button=True,
            on_info_click=on_info_click,
        )

        # Two-column layout
        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="row",
                gap=20,
                width="100%",
                height="100%",
            ),
        ):
            # Left Column: Prompt, Uploads, Preview (65%)
            with me.box(
                style=me.Style(
                    flex_basis="calc(100% - 360px)",
                    display="flex",
                    flex_direction="column",
                    gap=16,
                ),
            ):
                # Prompt Description Card
                with me.box(
                    style=me.Style(
                        background=me.theme_var("surface-container-low"),
                        border_radius=12,
                        padding=me.Padding.all(16),
                        display="flex",
                        flex_direction="column",
                        gap=8,
                        width="100%",
                    ),
                ):
                    me.text(
                        "Prompt Description",
                        style=me.Style(font_size=13, font_weight=500),
                    )
                    me.native_textarea(
                        autosize=True,
                        min_rows=4,
                        max_rows=8,
                        placeholder="Video generation instructions...",
                        value=state.prompt,
                        on_blur=on_prompt_blur,
                        style=me.Style(
                            width="100%",
                            border=me.Border.all(
                                me.BorderSide(
                                    width=1,
                                    style="solid",
                                    color=me.theme_var("outline-variant"),
                                ),
                            ),
                            border_radius=8,
                            padding=me.Padding.all(12),
                            background=me.theme_var("surface"),
                            color=me.theme_var("on-surface"),
                            font_family="Roboto, sans-serif",
                            font_size=14,
                            outline="none",
                        ),
                    )

                # Dynamic Media Uploaders
                media_uploaders(
                    on_upload_i2v_image=on_upload_i2v_image,
                    on_clear_i2v_image=on_clear_i2v_image,
                    on_upload_r2v_image=on_upload_r2v_image,
                    on_clear_r2v_image_idx=on_clear_r2v_image_idx,
                    on_upload_edit_video=on_upload_edit_video,
                    on_clear_edit_video=on_clear_edit_video,
                    on_upload_edit_style=on_upload_edit_style,
                    on_clear_edit_style=on_clear_edit_style,
                )

                # Preview Box
                with me.box(
                    style=me.Style(
                        background=me.theme_var("surface-container-low"),
                        border_radius=12,
                        padding=me.Padding.all(16),
                        display="flex",
                        flex_direction="column",
                        align_items="center",
                        justify_content="center",
                        min_height="320px",
                        border=me.Border.all(
                            me.BorderSide(
                                width=1,
                                style="solid"
                                if state.generated_video_url
                                else "dashed",
                                color=me.theme_var("outline-variant"),
                            ),
                        ),
                        width="100%",
                    ),
                ):
                    if state.is_loading:
                        with me.box(
                            style=me.Style(
                                display="flex",
                                flex_direction="column",
                                align_items="center",
                                gap=16,
                            ),
                        ):
                            me.progress_spinner()
                            me.text(
                                "Generating video with Gemini Omni Flash...",
                                style=me.Style(
                                    font_size=14,
                                    font_weight=500,
                                    color=me.theme_var("on-surface-variant"),
                                ),
                            )
                    elif state.generated_video_url:
                        me.video(
                            src=state.generated_video_url,
                            style=me.Style(
                                width="100%",
                                max_height="400px",
                                border_radius=8,
                                box_shadow=me.theme_var("shadow_elevation_1"),
                            ),
                        )
                        # Conversational Refinement Prompt Box
                        with me.box(
                            style=me.Style(
                                display="flex",
                                flex_direction="column",
                                gap=10,
                                width="100%",
                                margin=me.Margin(top=20),
                                padding=me.Padding.all(12),
                                background=me.theme_var("surface-container-high"),
                                border_radius=8,
                            ),
                        ):
                            me.text(
                                "Chat Refinement (Multi-turn edit)",
                                style=me.Style(font_size=13, font_weight=500),
                            )
                            me.native_textarea(
                                autosize=True,
                                min_rows=2,
                                max_rows=5,
                                placeholder="e.g. Change the car color to metallic blue. Keep everything else same.",
                                value=state.refinement_prompt,
                                on_blur=on_refinement_blur,
                                style=me.Style(
                                    width="100%",
                                    border=me.Border.all(
                                        me.BorderSide(
                                            width=1,
                                            style="solid",
                                            color=me.theme_var("outline-variant"),
                                        ),
                                    ),
                                    border_radius=8,
                                    padding=me.Padding.all(10),
                                    background=me.theme_var("surface"),
                                    color=me.theme_var("on-surface"),
                                    outline="none",
                                ),
                            )
                            with me.box(
                                style=me.Style(
                                    display="flex",
                                    justify_content="flex-end",
                                    gap=10,
                                ),
                            ):
                                me.button(
                                    "Reset Chat",
                                    type="stroked",
                                    on_click=on_reset_chat,
                                    style=me.Style(border_radius=18),
                                )
                                me.button(
                                    "Send",
                                    type="flat",
                                    on_click=on_send_refinement,
                                    style=me.Style(border_radius=18),
                                )
                    else:
                        me.text(
                            "Generate a video to see preview here.",
                            style=me.Style(
                                font_size=14,
                                color=me.theme_var("on-surface-variant"),
                                font_weight=500,
                            ),
                        )

            # Right Column: Settings Card (35%)
            with me.box(
                style=me.Style(
                    flex_basis="340px",
                    display="flex",
                    flex_direction="column",
                ),
            ):
                settings_panel(
                    on_mode_change=on_mode_change,
                    on_model_change=on_model_change,
                    on_aspect_ratio_change=on_aspect_ratio_change,
                    on_generate_click=on_generate_click,
                )


# --- Event Handlers ---


def on_info_click(_e: me.ClickEvent) -> None:
    """Handle info dialog click."""


def on_prompt_blur(e: me.InputBlurEvent) -> None:
    """Update the prompt text in state."""
    state = me.state(PageState)
    state.prompt = e.value


def on_mode_change(e: me.SelectSelectionChangeEvent) -> None:
    """Update the generation mode and resets corresponding mode assets."""
    state = me.state(PageState)
    state.generation_mode = e.value


def on_model_change(e: me.SelectSelectionChangeEvent) -> None:
    """Update the selected model."""
    state = me.state(PageState)
    state.model_version = e.value


def on_aspect_ratio_change(e: me.SelectSelectionChangeEvent) -> None:
    """Update the aspect ratio."""
    state = me.state(PageState)
    state.aspect_ratio = e.value


def on_close_error_dialog(_e: me.ClickEvent) -> None:
    """Close the error dialog."""
    state = me.state(PageState)
    state.show_error_dialog = False


def on_upload_i2v_image(e: me.UploadEvent) -> Generator[None]:
    """Upload the starting frame image for i2v mode."""
    state = me.state(PageState)
    try:
        gcs_path = store_to_gcs(
            folder="omni_uploads",
            file_name=e.file.name,
            mime_type=e.file.mime_type,
            contents=e.file.getvalue(),
        )
        state.i2v_image_gcs = gcs_path
        state.i2v_image_display_url = create_display_url(gcs_path)
        state.i2v_image_mime_type = e.file.mime_type
    except Exception as ex:  # noqa: BLE001
        state.error_message = f"Failed to upload starting frame image: {ex}"
        state.show_error_dialog = True
    yield


def on_clear_i2v_image(_e: me.ClickEvent) -> None:
    """Clear the starting frame image."""
    state = me.state(PageState)
    state.i2v_image_gcs = ""
    state.i2v_image_display_url = ""
    state.i2v_image_mime_type = ""
    state.i2v_image_file_key += 1


def on_upload_r2v_image(e: me.UploadEvent) -> Generator[None]:
    """Upload a reference image for r2v mode."""
    state = me.state(PageState)
    try:
        gcs_path = store_to_gcs(
            folder="omni_uploads",
            file_name=e.file.name,
            mime_type=e.file.mime_type,
            contents=e.file.getvalue(),
        )
        refs = json.loads(state.r2v_images_json)
        refs.append(
            {
                "gcs_uri": gcs_path,
                "display_url": create_display_url(gcs_path),
                "mime_type": e.file.mime_type,
            },
        )
        state.r2v_images_json = json.dumps(refs)
        state.r2v_upload_key += 1
    except Exception as ex:  # noqa: BLE001
        state.error_message = f"Failed to upload reference image: {ex}"
        state.show_error_dialog = True
    yield


def on_clear_r2v_image_idx(e: me.ClickEvent) -> None:
    """Clear a reference image by its index."""
    state = me.state(PageState)
    try:
        idx = int(e.key)
        refs = json.loads(state.r2v_images_json)
        if 0 <= idx < len(refs):
            refs.pop(idx)
        state.r2v_images_json = json.dumps(refs)
    except Exception as ex:  # noqa: BLE001
        state.error_message = f"Failed to clear reference image: {ex}"
        state.show_error_dialog = True


def on_upload_edit_video(e: me.UploadEvent) -> Generator[None]:
    """Upload the base video for editing mode."""
    state = me.state(PageState)
    try:
        gcs_path = store_to_gcs(
            folder="omni_uploads",
            file_name=e.file.name,
            mime_type=e.file.mime_type,
            contents=e.file.getvalue(),
        )
        state.edit_video_gcs = gcs_path
        state.edit_video_display_url = create_display_url(gcs_path)
        state.edit_video_mime_type = e.file.mime_type
    except Exception as ex:  # noqa: BLE001
        state.error_message = f"Failed to upload base video: {ex}"
        state.show_error_dialog = True
    yield


def on_clear_edit_video(_e: me.ClickEvent) -> None:
    """Clear the base video."""
    state = me.state(PageState)
    state.edit_video_gcs = ""
    state.edit_video_display_url = ""
    state.edit_video_mime_type = ""
    state.edit_video_file_key += 1


def on_upload_edit_style(e: me.UploadEvent) -> Generator[None]:
    """Upload the optional style image for editing mode."""
    state = me.state(PageState)
    try:
        gcs_path = store_to_gcs(
            folder="omni_uploads",
            file_name=e.file.name,
            mime_type=e.file.mime_type,
            contents=e.file.getvalue(),
        )
        state.edit_style_image_gcs = gcs_path
        state.edit_style_image_display_url = create_display_url(gcs_path)
        state.edit_style_image_mime_type = e.file.mime_type
    except Exception as ex:  # noqa: BLE001
        state.error_message = f"Failed to upload style image: {ex}"
        state.show_error_dialog = True
    yield


def on_clear_edit_style(_e: me.ClickEvent) -> None:
    """Clear the style image."""
    state = me.state(PageState)
    state.edit_style_image_gcs = ""
    state.edit_style_image_display_url = ""
    state.edit_style_image_mime_type = ""
    state.edit_style_image_file_key += 1


def on_generate_click(_e: me.ClickEvent) -> Generator[None]:
    """Trigger the Gemini Omni video generation/editing workflow."""
    state = me.state(PageState)

    # Validation
    if not state.prompt:
        state.error_message = "Please enter a prompt instruction."
        state.show_error_dialog = True
        yield
        return

    state.is_loading = True
    state.generated_video_url = ""
    state.generated_video_gcs = ""
    state.last_interaction_id = ""
    yield

    try:
        gcs_uri, display_url, interaction_id = generate_omni_video(
            prompt=state.prompt,
            mode=state.generation_mode,
            aspect_ratio=state.aspect_ratio,
            i2v_image_gcs=state.i2v_image_gcs,
            i2v_image_mime=state.i2v_image_mime_type,
            r2v_images_json=state.r2v_images_json,
            edit_video_gcs=state.edit_video_gcs,
            edit_video_mime=state.edit_video_mime_type,
            edit_style_gcs=state.edit_style_image_gcs,
            edit_style_mime=state.edit_style_image_mime_type,
        )
        state.generated_video_gcs = gcs_uri
        state.generated_video_url = display_url
        state.last_interaction_id = interaction_id
    except Exception as ex:  # noqa: BLE001
        state.error_message = str(ex)
        state.show_error_dialog = True
    finally:
        state.is_loading = False
    yield


def on_refinement_blur(e: me.InputBlurEvent) -> None:
    """Update the refinement prompt in state."""
    state = me.state(PageState)
    state.refinement_prompt = e.value


def on_send_refinement(_e: me.ClickEvent) -> Generator[None]:
    """Send refinement prompt to the Omni interaction model."""
    state = me.state(PageState)

    if not state.refinement_prompt:
        state.error_message = "Please enter a refinement instruction."
        state.show_error_dialog = True
        yield
        return

    refinement_to_send = state.refinement_prompt
    state.is_loading = True
    state.refinement_prompt = ""
    yield

    try:
        gcs_uri, display_url, interaction_id = generate_omni_video(
            prompt=refinement_to_send,
            mode=state.generation_mode,
            aspect_ratio=state.aspect_ratio,
            i2v_image_gcs=state.i2v_image_gcs,
            i2v_image_mime=state.i2v_image_mime_type,
            r2v_images_json=state.r2v_images_json,
            edit_video_gcs=state.edit_video_gcs,
            edit_video_mime=state.edit_video_mime_type,
            edit_style_gcs=state.edit_style_image_gcs,
            edit_style_mime=state.edit_style_image_mime_type,
            previous_interaction_id=state.last_interaction_id,
        )
        state.generated_video_gcs = gcs_uri
        state.generated_video_url = display_url
        state.last_interaction_id = interaction_id
    except Exception as ex:  # noqa: BLE001
        state.error_message = str(ex)
        state.show_error_dialog = True
    finally:
        state.is_loading = False
    yield


def on_reset_chat(_e: me.ClickEvent) -> None:
    """Reset the chat session and clear the page output."""
    state = me.state(PageState)
    state.generated_video_url = ""
    state.generated_video_gcs = ""
    state.last_interaction_id = ""
    state.refinement_prompt = ""
