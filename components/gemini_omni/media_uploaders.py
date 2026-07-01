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
"""Media uploaders component for Gemini Omni."""

import json
from collections.abc import Callable

import mesop as me

from components.image_thumbnail import image_thumbnail
from state.gemini_omni_state import PageState


def media_uploaders(  # noqa: C901, PLR0912, PLR0913
    on_upload_i2v_image: Callable,
    on_clear_i2v_image: Callable,
    on_upload_r2v_image: Callable,
    on_clear_r2v_image_idx: Callable,
    on_upload_edit_video: Callable,
    on_clear_edit_video: Callable,
    on_upload_edit_style: Callable,
    on_clear_edit_style: Callable,
) -> None:
    """Render the media uploaders depending on the selected mode in PageState."""
    state = me.state(PageState)
    print(
        "DEBUG - media_uploaders rendering: generation_mode =",
        state.generation_mode,
        flush=True,
    )

    if state.generation_mode == "t2v":
        # Text-to-Video doesn't need any uploaders
        return

    with me.box(
        style=me.Style(
            background=me.theme_var("surface-container-low"),
            border_radius=12,
            padding=me.Padding.all(16),
            display="flex",
            flex_direction="column",
            gap=16,
            width="100%",
            margin=me.Margin(bottom=16),
        ),
    ):
        if state.generation_mode == "i2v":
            me.text(
                "Upload Starting Frame Image",
                style=me.Style(font_size=13, font_weight=500),
            )
            with me.box(style=me.Style(display="flex", gap=10, flex_direction="row")):
                if state.i2v_image_display_url:
                    image_thumbnail(
                        image_uri=state.i2v_image_display_url,
                        index=0,
                        on_remove=on_clear_i2v_image,
                        width=180,
                        height=150,
                    )
                else:
                    _placeholder_uploader(
                        label="Upload Image",
                        on_upload=on_upload_i2v_image,
                        accepted_types=["image/jpeg", "image/png", "image/webp"],
                        key=f"i2v_img_{state.i2v_image_file_key}",
                    )

        elif state.generation_mode == "r2v":
            me.text(
                "Upload Reference Images (guides consistency, max 3)",
                style=me.Style(font_size=13, font_weight=500),
            )
            try:
                refs = json.loads(state.r2v_images_json)
            except Exception:  # noqa: BLE001
                refs = []

            with me.box(style=me.Style(display="flex", gap=10, flex_direction="row")):
                for idx, ref in enumerate(refs):
                    image_thumbnail(
                        image_uri=ref["display_url"],
                        index=idx,
                        on_remove=on_clear_r2v_image_idx,
                        width=180,
                        height=150,
                    )

                if len(refs) < 3:  # noqa: PLR2004
                    _placeholder_uploader(
                        label="Add Reference Image",
                        on_upload=on_upload_r2v_image,
                        accepted_types=["image/jpeg", "image/png", "image/webp"],
                        key=f"r2v_img_{state.r2v_upload_key}",
                    )

        elif state.generation_mode == "editing":
            # Section 1: Optional style reference
            with me.box(style=me.Style(display="flex", flex_direction="column", gap=8)):
                me.text(
                    "Optional: Upload Reference/Style Image",
                    style=me.Style(font_size=13, font_weight=500),
                )
                with me.box(
                    style=me.Style(display="flex", gap=10, flex_direction="row"),
                ):
                    if state.edit_style_image_display_url:
                        image_thumbnail(
                            image_uri=state.edit_style_image_display_url,
                            index=0,
                            on_remove=on_clear_edit_style,
                            width=180,
                            height=150,
                        )
                    else:
                        _placeholder_uploader(
                            label="Upload Image",
                            on_upload=on_upload_edit_style,
                            accepted_types=["image/jpeg", "image/png", "image/webp"],
                            key=f"edit_style_{state.edit_style_image_file_key}",
                        )

            # Section 2: Base video reference
            with me.box(style=me.Style(display="flex", flex_direction="column", gap=8)):
                me.text(
                    "Upload Base Video to Edit",
                    style=me.Style(font_size=13, font_weight=500),
                )
                with me.box(
                    style=me.Style(display="flex", gap=10, flex_direction="row"),
                ):
                    if state.edit_video_display_url:
                        image_thumbnail(
                            image_uri=state.edit_video_display_url,
                            index=0,
                            on_remove=on_clear_edit_video,
                            width=180,
                            height=150,
                        )
                    else:
                        _placeholder_uploader(
                            label="Upload Video",
                            on_upload=on_upload_edit_video,
                            accepted_types=[
                                "video/mp4",
                                "video/quicktime",
                                "video/x-matroska",
                                "video/webm",
                            ],
                            key=f"edit_vid_{state.edit_video_file_key}",
                        )


def _placeholder_uploader(
    label: str,
    on_upload: Callable,
    accepted_types: list[str],
    key: str,
) -> None:
    """Render a dashed placeholder card wrapping a file uploader."""
    with me.box(
        style=me.Style(
            height=150,
            width=180,
            border=me.Border.all(
                me.BorderSide(
                    width=1,
                    style="dashed",
                    color=me.theme_var("outline"),
                ),
            ),
            border_radius=8,
            display="flex",
            flex_direction="column",
            align_items="center",
            justify_content="center",
            padding=me.Padding.all(8),
            background=me.theme_var("surface-container-low"),
        ),
    ):
        me.uploader(
            label=label,
            on_upload=on_upload,
            accepted_file_types=accepted_types,
            key=key,
            style=me.Style(font_size=12),
        )
