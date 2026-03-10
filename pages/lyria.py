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
"""Lyria mesop ui page"""

import datetime  # Required for timestamp
import json
import time

import mesop as me

from common.metadata import MediaItem, add_media_item_to_firestore  # Updated import
from common.utils import create_display_url
from components.content_credentials.content_credentials import (
    content_credentials_viewer,
)
from components.dialog import dialog, dialog_actions
from components.feedback.feedback import feedback
from components.header import header
from components.image_thumbnail import image_thumbnail
from components.library.events import LibrarySelectionChangeEvent
from components.library.library_chooser_button import library_chooser_button
from components.lyria.audio_critic import audio_critic
from components.lyria.technical_metrics import technical_metrics
from components.page_scaffold import (
    page_frame,
    page_scaffold,
)
from config.default import ABOUT_PAGE_CONTENT, Default
from config.lyria_models import LYRIA_MODELS, get_lyria_model_config
from config.rewriters import MUSIC_REWRITER
from models.audio_analysis import analyze_audio_file
from models.gemini import analyze_audio_with_gemini, rewriter
from models.lyria import generate_music_with_lyria
from state.lyria_state import PageState
from state.state import AppState

cfg = Default()


@me.page(path="/lyria", title="Lyria - GenMedia Creative Studio")
def lyria_page():
    """Main Page."""
    state = me.state(AppState)
    with page_scaffold(page_name="lyria"):  # pylint: disable=not-context-manager
        lyria_content(state)


# Original box style
_BOX_STYLE = me.Style(
    background=me.theme_var("background"),
    border_radius=12,
    box_shadow=("0 3px 1px -2px #0003, 0 2px 2px #00000024, 0 1px 5px #0000001f"),
    padding=me.Padding(top=16, left=16, right=16, bottom=16),
    display="flex",
    flex_direction="column",
)


# Combined style for the reference images display box
_REFERENCE_IMAGES_BOX_STYLE = me.Style(
    background=me.theme_var("background"),
    border_radius=12,
    box_shadow=("0 3px 1px -2px #0003, 0 2px 2px #00000024, 0 1px 5px #0000001f"),
    padding=me.Padding(top=16, left=16, right=16, bottom=16),
    display="flex",
    flex_direction="column",
    margin=me.Margin(top=16, bottom=16),
)


def lyria_content(app_state: me.state):
    """Lyria Mesop Page"""
    pagestate = me.state(PageState)

    if pagestate.info_dialog_open:
        with dialog(is_open=pagestate.info_dialog_open):  # pylint: disable=not-context-manager
            me.text("About Lyria", type="headline-6")
            me.markdown(
                next(
                    (
                        s["description"]
                        for s in ABOUT_PAGE_CONTENT.get("sections", [])
                        if s.get("id") == "lyria"
                    ),
                    "",
                ),
            )
            me.divider()
            me.text("Current Settings", type="headline-6")
            me.text(f"Prompt: {pagestate.music_prompt_input}")
            with dialog_actions():  # pylint: disable=not-context-manager
                me.button("Close", on_click=close_info_dialog, type="flat")

    with page_frame():  # pylint: disable=not-context-manager
        header(
            "Lyria",
            "music_note",
            show_info_button=True,
            on_info_click=open_info_dialog,
        )

        # Model Selector
        with me.box(style=me.Style(margin=me.Margin(bottom=16))):
            me.select(
                label="Model",
                options=[
                    me.SelectOption(label=m.display_name, value=m.version_id)
                    for m in LYRIA_MODELS
                ],
                on_selection_change=on_lyria_model_change,
                value=pagestate.selected_model_id,
                style=me.Style(width=250),
            )

        model_config = get_lyria_model_config(pagestate.selected_model_id)

        if model_config and model_config.max_samples > 1:
            with me.box(style=me.Style(margin=me.Margin(bottom=16))):
                me.select(
                    label="Sample Count",
                    options=[
                        me.SelectOption(label=str(i), value=str(i))
                        for i in range(1, model_config.max_samples + 1)
                    ],
                    on_selection_change=on_lyria_sample_count_change,
                    value=str(pagestate.sample_count),
                    style=me.Style(width=250),
                )

        _FLEX_BOX_STYLE = me.Style(
            background=me.theme_var("background"),
            border_radius=12,
            box_shadow=(
                "0 3px 1px -2px #0003, 0 2px 2px #00000024, 0 1px 5px #0000001f"
            ),
            padding=me.Padding(top=16, left=16, right=16, bottom=16),
            display="flex",
            flex_direction="column",
            flex=1,
        )

        if model_config and model_config.supports_lyrics:
            with me.box(
                style=me.Style(
                    display="flex",
                    flex_direction="row",
                    gap=16,
                    width="100%",
                ),
            ):
                with me.box(style=_FLEX_BOX_STYLE):
                    me.text(
                        "Prompt for music generation",
                        style=me.Style(font_weight=500),
                    )
                    me.box(style=me.Style(height=16))
                    subtle_lyria_input()
                with me.box(style=_FLEX_BOX_STYLE):
                    me.text("Lyrics (Optional)", style=me.Style(font_weight=500))
                    me.box(style=me.Style(height=16))
                    subtle_lyrics_input()
        else:
            with me.box(style=_BOX_STYLE):
                me.text("Prompt for music generation", style=me.Style(font_weight=500))
                me.box(style=me.Style(height=16))
                subtle_lyria_input()

        if model_config and model_config.supports_images:
            with me.box(style=_REFERENCE_IMAGES_BOX_STYLE):
                me.text("Reference Images", style=me.Style(font_weight=500))
                me.box(style=me.Style(height=16))
                with me.box(
                    style=me.Style(
                        display="flex",
                        flex_direction="row",
                        gap=16,
                        margin=me.Margin(bottom=16),
                        align_items="center",
                    ),
                ):
                    me.uploader(
                        label="Upload Image(s)",
                        accepted_file_types=["image/jpeg", "image/png", "image/webp"],
                        on_upload=on_upload_lyria_image,
                        multiple=True,
                        type="flat",
                    )
                    library_chooser_button(
                        on_library_select=on_library_select,
                        button_label="Choose from Library",
                    )
                    if pagestate.uploaded_image_gcs_uris:
                        me.button(
                            "Clear All",
                            on_click=on_clear_lyria_image,
                            type="stroked",
                        )

                if pagestate.uploaded_image_gcs_uris:
                    with me.box(
                        style=me.Style(
                            display="flex",
                            flex_wrap="wrap",
                            gap=10,
                            justify_content="flex-start",
                        ),
                    ):
                        for i, uri in enumerate(pagestate.uploaded_image_display_urls):
                            image_thumbnail(
                                image_uri=uri,
                                index=i,
                                on_remove=on_remove_image,
                                icon_size=18,
                            )

        me.box(style=me.Style(height=24))

        # Primary Operation Loading Indicator (Lyria Generation or Rewriter)
        if pagestate.is_loading:
            with me.box(
                style=me.Style(
                    display="grid",
                    justify_content="center",
                    justify_items="center",
                    padding=me.Padding.all(16),
                ),
            ):
                me.progress_spinner()
                me.text(
                    pagestate.loading_operation_message,  # Display dynamic loading message
                    style=me.Style(margin=me.Margin(top=8)),
                )

        # Audio Player - Show if URI exists AND primary loading is done
        if (
            pagestate.music_display_urls
            and not pagestate.is_loading  # Check generic loading
            and not pagestate.show_error_dialog
        ):
            with me.box(
                style=me.Style(
                    display="flex",
                    flex_direction="column",
                    gap=16,
                    align_items="center",
                    margin=me.Margin(bottom=16),
                ),
            ):
                if len(pagestate.music_display_urls) > 1:
                    with me.box(
                        style=me.Style(
                            display="flex",
                            flex_direction="row",
                            gap=16,
                            align_items="center",
                        ),
                    ):
                        me.select(
                            label="Select Track",
                            options=[
                                me.SelectOption(label=f"Track {i+1}", value=str(i))
                                for i in range(len(pagestate.music_display_urls))
                            ],
                            on_selection_change=on_track_selection_change,
                            value=str(pagestate.selected_track_index),
                            style=me.Style(width=250),
                        )

                current_audio_url = (
                    pagestate.music_display_urls[pagestate.selected_track_index]
                    if pagestate.selected_track_index
                    < len(pagestate.music_display_urls)
                    else pagestate.music_display_urls[0]
                )
                me.audio(src=current_audio_url)

                if pagestate.current_media_item_id and not pagestate.is_loading and not pagestate.show_error_dialog:
                    with me.box(style=me.Style(display="flex", justify_content="center", margin=me.Margin(top=8, bottom=16))):
                        feedback(media_item_id=pagestate.current_media_item_id)

                if pagestate.c2pa_manifest_json:
                    with me.box(style=me.Style(margin=me.Margin(top=16))):
                        content_credentials_viewer(
                            manifest=pagestate.c2pa_manifest_json,
                        )

                if pagestate.generated_text:
                    with me.box(style=me.Style(margin=me.Margin(top=16), width="100%")):
                        with me.expansion_panel(
                            title="Generated Text Outputs",
                            icon="notes",
                        ):
                            for text_output in pagestate.generated_text:
                                me.markdown(text_output)
                                me.divider()

        # Gemini Analysis Loading Indicator - Show if analyzing AND primary loading is done
        if pagestate.is_analyzing and not pagestate.is_loading:
            with me.box(
                style=me.Style(
                    display="grid",
                    justify_content="center",
                    justify_items="center",
                    padding=me.Padding.all(16),
                ),
            ):
                me.progress_spinner()
                me.text(
                    "Analyzing audio with Gemini...",
                    style=me.Style(margin=me.Margin(top=8)),
                )

        audio_critic()

        technical_metrics()

        # Error Dialog for Generation Errors (Lyria errors)
        with dialog(is_open=pagestate.show_error_dialog):  # pylint: disable=not-context-manager
            me.text(
                "Generation Error",
                type="headline-6",
                style=me.Style(color=me.theme_var("error"), font_weight="bold"),
            )
            me.text(pagestate.error_message, style=me.Style(margin=me.Margin(top=16)))
            with dialog_actions():  # pylint: disable=not-context-manager
                me.button("Close", on_click=on_close_error_dialog, type="flat")


@me.component
def subtle_lyria_input():
    """Lyria music description input component"""
    pagestate = me.state(PageState)
    icon_style = me.Style(
        display="flex",
        flex_direction="column",
        gap=2,
        font_size=10,
        align_items="center",
    )
    with me.box(
        style=me.Style(
            border_radius=16,
            padding=me.Padding.all(8),
            background=me.theme_var("secondary-container"),
            display="flex",
            width="100%",
        ),
    ):
        with me.box(style=me.Style(flex_grow=1)):
            me.native_textarea(
                autosize=True,
                min_rows=8,
                placeholder="enter a musical audio description",
                style=me.Style(
                    padding=me.Padding(top=16, left=16, right=16, bottom=16),
                    background=me.theme_var("secondary-container"),
                    outline="none",
                    width="100%",
                    max_height=300,
                    overflow_y="auto",
                    border=me.Border.all(me.BorderSide(style="none")),
                    color=me.theme_var("foreground"),
                    flex_grow=1,
                ),
                on_blur=on_blur_lyria_prompt,
                key=str(pagestate.music_prompt_textarea_key),
                value=pagestate.music_prompt_placeholder,
            )
        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="column",
                gap=10,
                padding=me.Padding(left=16, right=16, bottom=16),
            ),
        ):
            with me.content_button(
                type="icon",
                on_click=on_click_lyria,
                disabled=pagestate.is_loading or pagestate.is_analyzing,
            ):
                with me.box(style=icon_style):
                    me.icon("music_note")
                    me.text("Generate Audio")
            me.box(style=me.Style(height=5))
            with me.content_button(
                type="icon",
                on_click=on_click_lyria_rewriter,
                disabled=pagestate.is_loading or pagestate.is_analyzing,
            ):
                with me.box(style=icon_style):
                    me.icon("auto_awesome")
                    me.text("Rewrite")
            me.box(style=me.Style(height=5))
            with me.content_button(
                type="icon",
                on_click=clear_music,
                disabled=pagestate.is_loading or pagestate.is_analyzing,
            ):
                with me.box(style=icon_style):
                    me.icon("clear")
                    me.text("Clear")


@me.component
def subtle_lyrics_input():
    """Lyria lyrics input component"""
    pagestate = me.state(PageState)
    icon_style = me.Style(
        display="flex",
        flex_direction="column",
        gap=2,
        font_size=10,
        align_items="center",
    )
    with me.box(
        style=me.Style(
            border_radius=16,
            padding=me.Padding.all(8),
            background=me.theme_var("secondary-container"),
            display="flex",
            width="100%",
        ),
    ):
        with me.box(style=me.Style(flex_grow=1)):
            me.native_textarea(
                autosize=True,
                min_rows=8,
                placeholder="Enter lyrics here...",
                style=me.Style(
                    padding=me.Padding(top=16, left=16, right=16, bottom=16),
                    background=me.theme_var("secondary-container"),
                    outline="none",
                    width="100%",
                    max_height=300,
                    overflow_y="auto",
                    border=me.Border.all(me.BorderSide(style="none")),
                    color=me.theme_var("foreground"),
                    flex_grow=1,
                ),
                on_blur=on_blur_lyria_lyrics,
                value=pagestate.lyrics_placeholder,
            )
        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="column",
                gap=10,
                padding=me.Padding(left=16, right=16, bottom=16),
            ),
        ):
            with me.content_button(
                type="icon",
                on_click=on_click_lyria_lyrics_generate,
                disabled=pagestate.is_generating_lyrics or pagestate.is_loading,
            ):
                with me.box(style=icon_style):
                    me.icon("auto_awesome")
                    me.text("Generate")


def on_lyria_model_change(e: me.SelectSelectionChangeEvent):
    state = me.state(PageState)
    state.selected_model_id = e.value
    # Reset lyrics and images if switching to a model that doesn't support them
    model_config = get_lyria_model_config(e.value)
    if model_config and not model_config.supports_lyrics:
        state.lyrics_input = ""
        state.lyrics_placeholder = ""
    if model_config and not model_config.supports_images:
        state.uploaded_image_gcs_uris = []
    state.uploaded_image_mime_types = []
    state.uploaded_image_display_urls = []


def on_blur_lyria_lyrics(e: me.InputBlurEvent):
    state = me.state(PageState)
    state.lyrics_input = e.value
    state.lyrics_placeholder = e.value


def on_clear_lyria_image(e: me.ClickEvent):
    state = me.state(PageState)
    state.uploaded_image_gcs_uris = []
    state.uploaded_image_mime_types = []
    state.uploaded_image_display_urls = []


def on_library_select(e: LibrarySelectionChangeEvent):
    state = me.state(PageState)
    # We could restrict max images based on Lyria config here if needed, but for now we'll just append
    state.uploaded_image_gcs_uris.append(e.gcs_uri)

    # MIME type is hard to guess from just GCS URI in this event,
    # but we can assume jpeg or png based on extension or fallback to jpeg.
    ext = e.gcs_uri.split(".")[-1].lower() if "." in e.gcs_uri else "jpeg"
    mime_type = f"image/{ext}" if ext in ["png", "webp"] else "image/jpeg"
    state.uploaded_image_mime_types.append(mime_type)

    from common.utils import create_display_url

    state.uploaded_image_display_urls.append(create_display_url(e.gcs_uri))
    yield


def on_remove_image(e: me.ClickEvent):
    state = me.state(PageState)
    index_to_remove = int(e.key)

    if 0 <= index_to_remove < len(state.uploaded_image_gcs_uris):
        state.uploaded_image_gcs_uris.pop(index_to_remove)
        state.uploaded_image_mime_types.pop(index_to_remove)
        state.uploaded_image_display_urls.pop(index_to_remove)
    yield


def on_upload_lyria_image(e: me.UploadEvent):
    state = me.state(PageState)
    if not e.files:
        return
    import shortuuid

    from common.storage import store_to_gcs
    from common.utils import create_display_url
    from config.default import Default

    cfg = Default()

    for file in e.files:
        mime_type = file.mime_type
        ext = "jpg" if "jpeg" in mime_type else "png"
        file_name = f"lyria_image_{shortuuid.uuid()}.{ext}"

        # Store to GCS
        gcs_uri = store_to_gcs(
            "images",
            file_name,
            mime_type,
            file.getvalue(),
            False,
            bucket_name=cfg.MEDIA_BUCKET,
        )
        state.uploaded_image_gcs_uris.append(gcs_uri)
        state.uploaded_image_mime_types.append(mime_type)
        state.uploaded_image_display_urls.append(create_display_url(gcs_uri))


def on_blur_lyria_prompt(e: me.InputBlurEvent):
    state = me.state(PageState)
    if not state.is_loading and not state.is_analyzing:
        state.music_prompt_input = e.value
        state.music_prompt_placeholder = e.value
        state.original_user_prompt = e.value
        state.audio_analysis_result_json = None
        state.analysis_error_message = ""
        state.loading_operation_message = ""


def on_click_lyria_rewriter(e: me.ClickEvent):
    state = me.state(PageState)
    prompt_to_rewrite = state.music_prompt_input
    if not prompt_to_rewrite:
        state.error_message = "Please enter a prompt before rewriting."
        state.show_error_dialog = True
        yield
        return
    if not state.original_user_prompt:
        state.original_user_prompt = prompt_to_rewrite

    state.is_loading = True
    state.loading_operation_message = (
        "Music rewriter in progress..."  # Set specific message
    )
    state.show_error_dialog = False
    state.error_message = ""
    state.audio_analysis_result_json = None
    state.analysis_error_message = ""
    yield

    try:
        rewritten_prompt = rewriter(prompt_to_rewrite, MUSIC_REWRITER)
        state.music_prompt_input = rewritten_prompt
        state.music_prompt_placeholder = rewritten_prompt
    except Exception as err:
        print(f"Error during prompt rewriting: {err}")
        state.error_message = str(err)
        state.show_error_dialog = True
    finally:
        state.is_loading = False
        state.loading_operation_message = ""  # Clear message
        yield


def on_click_lyria(e: me.ClickEvent):
    """Generate music with Lyria handler"""
    app_state = me.state(AppState)
    state = me.state(PageState)
    prompt_for_api = state.music_prompt_input
    if not prompt_for_api:
        state.error_message = "Music prompt cannot be empty."
        state.show_error_dialog = True
        yield
        return

    state.is_loading = True
    state.loading_operation_message = (
        "Generating music with Lyria..."  # Set specific message
    )
    state.music_upload_uri = ""
    state.show_error_dialog = False
    state.error_message = ""
    state.audio_analysis_result_json = None
    state.analysis_error_message = ""
    yield

    print(
        f"Let's make music with: {prompt_for_api} (Model: {state.selected_model_id}, Samples: {state.sample_count}, Images: {len(state.uploaded_image_gcs_uris)})",
    )
    if state.original_user_prompt and state.original_user_prompt != prompt_for_api:
        print(f"Original user prompt was: {state.original_user_prompt}")

    start_time = time.time()
    generated_successfully = False
    lyria_error_message_for_metadata = ""
    gcs_uri_for_analysis_and_metadata = ""
    analysis_dict_for_metadata = None

    try:
        destination_blob_paths, c2pa_data, text_outputs = generate_music_with_lyria(
            prompt=prompt_for_api,
            model_name=get_lyria_model_config(state.selected_model_id).model_name,
            lyrics=state.lyrics_input,
            image_gcs_uri=state.uploaded_image_gcs_uris[0]
            if state.uploaded_image_gcs_uris
            else None,
            image_mime_type=state.uploaded_image_mime_types[0]
            if state.uploaded_image_mime_types
            else None,
            sample_count=state.sample_count,
        )
        if c2pa_data:
            state.c2pa_manifest_json = (
                json.dumps(c2pa_data) if isinstance(c2pa_data, dict) else c2pa_data
            )

        state.music_gcs_uris = destination_blob_paths
        state.music_display_urls = [
            create_display_url(p) for p in destination_blob_paths
        ]

        # Use the first one for analysis and metadata for now
        gcs_uri_for_analysis_and_metadata = (
            destination_blob_paths[0] if destination_blob_paths else ""
        )

        print(f"Music generated: {state.music_display_urls}")
        generated_successfully = True
    except Exception as err:
        print(f"Error during music generation: {err}")
        state.error_message = str(err)
        lyria_error_message_for_metadata = str(err)
        state.show_error_dialog = True
    finally:
        state.is_loading = False
        state.loading_operation_message = ""  # Clear message
        yield

    if generated_successfully and gcs_uri_for_analysis_and_metadata:
        state.is_analyzing = True
        yield

        # --- Technical Audio Analysis ---
        try:
            print(
                f"Starting technical audio analysis for: {gcs_uri_for_analysis_and_metadata}",
            )
            metrics = analyze_audio_file(gcs_uri_for_analysis_and_metadata)
            state.audio_metrics.mean_pitch_hz = metrics.mean_pitch_hz
            state.audio_metrics.pitch_std_hz = metrics.pitch_std_hz
            state.audio_metrics.pitch_range_hz = metrics.pitch_range_hz
            state.audio_metrics.jitter_percent = metrics.jitter_percent
            state.audio_metrics.shimmer_db = metrics.shimmer_db
            state.audio_metrics.hnr_db = metrics.hnr_db
            state.audio_metrics.estimated_tempo_bpm = metrics.estimated_tempo_bpm
            state.audio_metrics.duration_sec = metrics.duration_sec
            state.has_audio_metrics = True
            print("Technical audio analysis successful.")
        except Exception as tech_err:
            print(f"Warning: Technical audio analysis failed: {tech_err}")
            # Don't fail the whole process, just log it.

        # --- Gemini Analysis ---
        try:
            print(
                f"Starting analysis with GCS URI: {gcs_uri_for_analysis_and_metadata}",
            )
            analysis_result_dict = analyze_audio_with_gemini(
                audio_uri=gcs_uri_for_analysis_and_metadata,
                music_generation_prompt=prompt_for_api,
            )
            if analysis_result_dict:
                state.audio_analysis_result_json = json.dumps(analysis_result_dict)
                analysis_dict_for_metadata = analysis_result_dict
                print(
                    f"Analysis successful, stored as JSON. Dict: {analysis_result_dict}",
                )
            else:
                state.analysis_error_message = "Analysis returned no result."
                print(state.analysis_error_message)

        except Exception as analysis_err:
            print(f"Error during audio analysis: {analysis_err}")
            state.analysis_error_message = f"Analysis failed: {analysis_err!s}"
        finally:
            state.is_analyzing = False
            yield

    end_time = time.time()
    execution_time = end_time - start_time
    state.timing = f"Generation time: {round(execution_time)} seconds"
    print(
        f"Total process (generation + analysis attempt) took: {execution_time:.2f} seconds",
    )

    logged_original_prompt = state.original_user_prompt
    logged_rewritten_prompt = ""
    if state.original_user_prompt and prompt_for_api != state.original_user_prompt:
        logged_rewritten_prompt = prompt_for_api
    elif not state.original_user_prompt and prompt_for_api:
        logged_original_prompt = prompt_for_api

    try:
        print(
            f"Logging to metadata: API Prompt='{prompt_for_api}', Original='{logged_original_prompt}', Rewritten='{logged_rewritten_prompt}'",
        )
        item = MediaItem(
            user_email=app_state.user_email,
            timestamp=datetime.datetime.now(datetime.UTC),
            prompt=prompt_for_api,
            original_prompt=logged_original_prompt,
            rewritten_prompt=logged_rewritten_prompt
            if logged_rewritten_prompt
            else None,
            model=get_lyria_model_config(state.selected_model_id).model_name,
            mime_type="audio/wav",  # Lyria generates WAV
            generation_time=execution_time,
            error_message=lyria_error_message_for_metadata
            if lyria_error_message_for_metadata
            else None,
            gcs_uris=state.music_gcs_uris if generated_successfully else [],
            generated_text=state.generated_text if generated_successfully else [],
            audio_analysis=json.dumps(analysis_dict_for_metadata)
            if analysis_dict_for_metadata
            else None,
            # duration might be available if analysis_dict_for_metadata contains it, or if Lyria API provides it
        )
        add_media_item_to_firestore(item)
        state.current_media_item_id = item.id
    except Exception as meta_err:
        print(f"CRITICAL: Failed to store metadata: {meta_err}")


def clear_music(e: me.ClickEvent):
    state = me.state(PageState)
    state.music_prompt_input = ""
    state.music_prompt_placeholder = ""
    state.original_user_prompt = ""
    state.music_prompt_textarea_key += 1
    state.music_gcs_uris = []
    state.music_display_urls = []
    state.selected_track_index = 0
    state.generated_text = []
    state.is_loading = False
    state.is_analyzing = False
    state.show_error_dialog = False
    state.error_message = ""
    state.timing = ""
    state.audio_analysis_result_json = None
    state.analysis_error_message = ""
    state.loading_operation_message = ""  # Clear loading message
    state.has_audio_metrics = False
    state.current_media_item_id = None
    # Reset metrics
    state.audio_metrics.mean_pitch_hz = 0.0
    state.audio_metrics.pitch_std_hz = 0.0
    state.audio_metrics.pitch_range_hz = 0.0
    state.audio_metrics.jitter_percent = 0.0
    state.audio_metrics.shimmer_db = 0.0
    state.audio_metrics.hnr_db = 0.0
    state.audio_metrics.estimated_tempo_bpm = 0.0
    state.audio_metrics.duration_sec = 0.0
    yield


def on_close_error_dialog(e: me.ClickEvent):
    state = me.state(PageState)
    state.show_error_dialog = False
    state.error_message = ""
    yield


def open_info_dialog(e: me.ClickEvent):
    """Open the info dialog."""
    state = me.state(PageState)
    state.info_dialog_open = True
    yield


def close_info_dialog(e: me.ClickEvent):
    """Close the info dialog."""
    state = me.state(PageState)
    state.info_dialog_open = False
    yield


def on_click_lyria_lyrics_generate(e: me.ClickEvent):
    state = me.state(PageState)
    prompt_to_use = state.music_prompt_input
    if not prompt_to_use:
        state.error_message = "Please enter a music prompt to generate lyrics from."
        state.show_error_dialog = True
        yield
        return

    state.is_generating_lyrics = True
    yield

    try:
        from config.rewriters import LYRICS_GENERATOR
        from models.gemini import rewriter

        # Handle seed lyrics if the user already started typing something
        seed_lyrics = state.lyrics_input.strip()

        prompt_with_seed = LYRICS_GENERATOR.format(user_prompt=prompt_to_use)
        if seed_lyrics:
            prompt_with_seed += f"\n\nSeed Ideas/Partial Lyrics:\n{seed_lyrics}"

        generated_lyrics = rewriter(
            prompt_with_seed,
            "",
        )  # The rewriter function appends the second param to the first if it's not a template. Since we manually formatted it, we can just pass empty string for the template. Actually, `rewriter(user_prompt, system_prompt)` where system_prompt is the rule.

        # Let's adjust how we use the rewriter. `rewriter(prompt, template)` does:
        # prompt = template + "\n\n" + user_prompt if template is string.
        # So we can pass prompt_to_use as the user_prompt, and build a custom template.

        custom_template = LYRICS_GENERATOR
        if seed_lyrics:
            custom_template += f"\n\nSeed Ideas/Partial Lyrics:\n{seed_lyrics}"

        generated_lyrics = rewriter(prompt_to_use, custom_template)

        state.lyrics_input = generated_lyrics
        state.lyrics_placeholder = generated_lyrics
    except Exception as err:
        print(f"Error during lyrics generation: {err}")
        state.error_message = str(err)
        state.show_error_dialog = True
    finally:
        state.is_generating_lyrics = False
        yield


def on_lyria_sample_count_change(e: me.SelectSelectionChangeEvent):
    state = me.state(PageState)
    state.sample_count = int(e.value)


def on_track_selection_change(e: me.SelectSelectionChangeEvent):
    state = me.state(PageState)
    state.selected_track_index = int(e.value)

    # Update analysis if available? We probably want to keep the analysis tied to the first track or explicitly run it again.
    # For now, just change the active track.
