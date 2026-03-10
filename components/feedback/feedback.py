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

"""Reusable Mesop component for collecting user feedback on an asset."""

import mesop as me
from common.metadata import update_media_feedback
from components.snackbar import snackbar


@me.stateclass
class FeedbackState:
    current_media_item_id: str = ""
    feedback_vote: str = ""
    feedback_comment: str = ""
    show_feedback_box: bool = False
    feedback_submitted: bool = False
    show_snackbar: bool = False
    snackbar_message: str = ""


def _show_snackbar(state: FeedbackState, message: str):
    """Displays a localized snackbar message for the feedback component."""
    state.snackbar_message = message
    state.show_snackbar = True
    yield
    import time
    time.sleep(3)
    state.show_snackbar = False
    yield


def on_feedback_comment_blur(e: me.InputEvent):
    me.state(FeedbackState).feedback_comment = e.value


def on_thumb_click(e: me.ClickEvent):
    state = me.state(FeedbackState)
    if state.feedback_submitted:
        return
    state.feedback_vote = e.key
    state.show_feedback_box = True
    
    # Record the vote immediately
    if state.current_media_item_id:
        update_media_feedback(state.current_media_item_id, vote=state.feedback_vote)
        
    yield from _show_snackbar(state, "Vote recorded. You can add an optional comment below.")


def on_send_feedback_click(e: me.ClickEvent):
    state = me.state(FeedbackState)
    if state.current_media_item_id:
         update_media_feedback(
            state.current_media_item_id, 
            vote=state.feedback_vote, 
            comment=state.feedback_comment
        )
    state.feedback_submitted = True
    state.show_feedback_box = False
    yield from _show_snackbar(state, "Feedback and comment recorded. Thank you!")


@me.component
def feedback(media_item_id: str):
    """
    Renders a Thumbs Up/Down and optional comment feedback form.
    
    Args:
        media_item_id: The ID of the MediaItem in Firestore to attach feedback to.
    """
    state = me.state(FeedbackState)
    
    if not media_item_id:
        return

    # Automatically reset state if the ID changes
    if state.current_media_item_id != media_item_id:
        state.current_media_item_id = media_item_id
        state.feedback_vote = ""
        state.feedback_comment = ""
        state.show_feedback_box = False
        state.feedback_submitted = False

    if state.feedback_submitted:
        me.text("Thank you for your feedback!", style=me.Style(margin=me.Margin(top=16), font_style="italic", color=me.theme_var("on-surface-variant")))
        snackbar(is_visible=state.show_snackbar, label=state.snackbar_message)
        return

    with me.box(style=me.Style(display="flex", flex_direction="column", gap=8, margin=me.Margin(top=16), width="100%")):
        with me.box(style=me.Style(display="flex", flex_direction="row", gap=8, align_items="center")):
            me.text("Rate this generation:", style=me.Style(font_size=14))
            with me.content_button(type="icon", key="up", on_click=on_thumb_click):
                 me.icon("thumb_up", style=me.Style(color=me.theme_var("primary") if state.feedback_vote == "up" else ""))
            with me.content_button(type="icon", key="down", on_click=on_thumb_click):
                 me.icon("thumb_down", style=me.Style(color=me.theme_var("primary") if state.feedback_vote == "down" else ""))
        
        if state.show_feedback_box:
            me.textarea(
                label="Why? (Optional)",
                on_blur=on_feedback_comment_blur,
                value=state.feedback_comment,
                style=me.Style(width="100%"),
            )
            me.button("Send", on_click=on_send_feedback_click, type="raised")
            
    snackbar(is_visible=state.show_snackbar, label=state.snackbar_message)
