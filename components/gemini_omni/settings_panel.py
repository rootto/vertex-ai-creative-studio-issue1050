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
"""Settings panel component for Gemini Omni."""

import mesop as me

from config.gemini_omni_models import GEMINI_OMNI_MODELS, get_omni_model_config
from state.gemini_omni_state import PageState


@me.component
def settings_panel(
    on_mode_change,
    on_model_change,
    on_aspect_ratio_change,
    on_duration_change,
    on_generate_click,
) -> None:
    """Renders the right-hand settings panel card for Gemini Omni."""
    state = me.state(PageState)
    model_config = get_omni_model_config(state.model_version)

    with me.box(
        style=me.Style(
            background=me.theme_var("surface-container"),
            border_radius=16,
            padding=me.Padding.all(20),
            box_shadow=me.theme_var("shadow_elevation_1"),
            display="flex",
            flex_direction="column",
            gap=20,
            width="340px",
            height="fit-content",
        ),
    ):
        # 1. EAP Quota warning banner
        with me.box(
            style=me.Style(
                background=me.theme_var("error-container"),
                color=me.theme_var("on-error-container"),
                padding=me.Padding.all(12),
                border_radius=8,
                font_size=12,
                font_weight=500,
            ),
        ):
            me.text("EAP Quota Limit: 3 QPM. Please run sparingly.")

        # 2. Generation Mode select
        me.select(
            label="Generation Mode",
            appearance="outline",
            options=[
                me.SelectOption(label="Text-to-Video", value="t2v"),
                me.SelectOption(label="Image-to-Video", value="i2v"),
                me.SelectOption(label="Reference-to-Video", value="r2v"),
                me.SelectOption(label="Video Editing", value="editing"),
            ],
            value=state.generation_mode,
            on_selection_change=on_mode_change,
            style=me.Style(width="100%"),
        )

        # 3. Model select
        me.select(
            label="Model",
            appearance="outline",
            options=[
                me.SelectOption(label=m.display_name, value=m.version_id)
                for m in GEMINI_OMNI_MODELS
            ],
            value=state.model_version,
            on_selection_change=on_model_change,
            style=me.Style(width="100%"),
        )

        # 4. Aspect Ratio select
        if model_config:
            me.select(
                label="Aspect Ratio",
                appearance="outline",
                options=[
                    me.SelectOption(
                        label=f"Landscape ({ratio})"
                        if ratio == "16:9"
                        else (
                            f"Portrait ({ratio})"
                            if ratio == "9:16"
                            else f"Square ({ratio})"
                        ),
                        value=ratio,
                    )
                    for ratio in model_config.supported_aspect_ratios
                ],
                value=state.aspect_ratio,
                on_selection_change=on_aspect_ratio_change,
                style=me.Style(width="100%"),
            )

        # 5. Video Duration slider
        if model_config:
            with me.box(
                style=me.Style(
                    display="flex",
                    flex_direction="column",
                    gap=4,
                    width="100%",
                ),
            ):
                with me.box(
                    style=me.Style(
                        display="flex",
                        justify_content="space-between",
                        align_items="center",
                        width="100%",
                    ),
                ):
                    me.text(
                        "Video Duration",
                        style=me.Style(font_size=13, font_weight=500),
                    )
                    me.text(
                        f"{state.duration}s",
                        style=me.Style(font_size=13, font_weight=500),
                    )

                me.slider(
                    min=model_config.min_duration,
                    max=model_config.max_duration,
                    step=1,
                    value=state.duration,
                    on_value_change=on_duration_change,
                    style=me.Style(width="100%"),
                )

        # 6. Generate Video button
        me.button(
            "Generate Video",
            type="stroked",
            on_click=on_generate_click,
            disabled=state.is_loading,
            style=me.Style(
                width="100%",
                padding=me.Padding.symmetric(vertical=10),
                border_radius=24,
                font_weight=500,
                color=me.theme_var("primary"),
            ),
        )
