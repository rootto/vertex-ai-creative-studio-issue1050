# Copyright 2024 Google LLC
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
import mesop as me

from common.analytics import log_page_view
from components.side_nav import sidenav
from components.styles import (
    MAIN_COLUMN_STYLE,
    PAGE_BACKGROUND_PADDING_STYLE,
    PAGE_BACKGROUND_STYLE,
    SIDENAV_MAX_WIDTH,
    SIDENAV_MIN_WIDTH,
)
from components.theme_manager.theme_manager import theme_manager
from state.state import AppState, is_logged_in


def on_theme_load(e: me.WebEvent):
    s = me.state(AppState)
    s.theme_mode = e.value["theme"]
    me.set_theme_mode(s.theme_mode)
    yield




@me.content_component
def page_scaffold(page_name: str):
    """Page scaffold component"""
    app_state = me.state(AppState)
    app_state.current_page = page_name
    log_page_view(page_name=page_name, session_id=app_state.session_id)

    theme_manager(theme=app_state.theme_mode, on_theme_load=on_theme_load)

    # Allow login page to render without auth
    if page_name == "login" or is_logged_in():
        app_state.has_redirected = False  # Reset redirect status
        sidenav("")

        with (
            me.box(
                style=me.Style(
                    display="flex",
                    flex_direction="column",
                    height="100%",
                    margin=me.Margin(
                        left=SIDENAV_MAX_WIDTH
                        if app_state.sidenav_open
                        else SIDENAV_MIN_WIDTH,
                    ),
                ),
            ),
            me.box(
                style=me.Style(
                    background=me.theme_var("background"),
                    height="100%",
                    overflow_y="scroll",
                    margin=me.Margin(bottom=20),
                ),
            ),
        ):
            me.slot()
    else:
        # Automatically redirect unauthenticated users to the login page exactly once
        if not app_state.has_redirected:
            app_state.has_redirected = True
            me.navigate("/login")
        # Mesop requires me.slot() to be called in content components.
        # So we call it here but hide it!
        with me.box(style=me.Style(display="none")):
            me.slot()


@me.content_component
def page_frame():
    """Page Frame"""
    with me.box(style=MAIN_COLUMN_STYLE), me.box(style=PAGE_BACKGROUND_STYLE):
        with me.box(style=PAGE_BACKGROUND_PADDING_STYLE):
            me.slot()
