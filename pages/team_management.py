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

"""Team management page."""

import mesop as me

from components.header import header
from components.page_scaffold import page_frame, page_scaffold
from components.snackbar import snackbar
from services.team_service import (
    add_manager_to_team,
    add_member_to_team,
    create_team,
    get_teams_for_user,
)
from services.user_service import get_user_role, set_user_role
from state.state import AppState
from state.team_management_state import PageState


@me.page(
    path="/team_management",
    title="Team Management - GenMedia Creative Studio",
)
def page() -> None:
    """Render the team management page."""
    with page_scaffold(page_name="team_management"), page_frame():
        header("Team Management", "group")
        team_management_content()


def team_management_content() -> None:
    """Render the content for team management."""
    app_state = me.state(AppState)
    page_state = me.state(PageState)
    print(f"DEBUG: team_management_content entered. user_role={app_state.user_role}, email={app_state.user_email}", flush=True)

    if app_state.user_role not in ["administrator", "manager"]:
        with me.box(style=me.Style(padding=me.Padding.all(24))):
            me.text(
                "You do not have permission to view this page.",
                type="headline-6",
                style=me.Style(color=me.theme_var("error")),
            )
        return

    snackbar(is_visible=page_state.show_snackbar, label=page_state.snackbar_message)

    with me.box(
        style=me.Style(
            display="flex", flex_direction="column", gap=24, padding=me.Padding.all(24),
        ),
    ):
        # --- Admin Section ---
        if app_state.user_role == "administrator":
            with me.box(
                style=me.Style(
                    background=me.theme_var("surface"),
                    padding=me.Padding.all(16),
                    border_radius=8,
                ),
            ):
                me.text(
                    "Administrator Actions",
                    type="headline-5",
                    style=me.Style(margin=me.Margin(bottom=16)),
                )

                # Create Team
                with me.box(
                    style=me.Style(
                        display="flex",
                        flex_direction="row",
                        gap=16,
                        align_items="center",
                        margin=me.Margin(bottom=16),
                    ),
                ):
                    me.input(
                        label="New Team Name",
                        value=page_state.new_team_name,
                        on_blur=on_new_team_name_blur,
                        style=me.Style(flex_grow=1),
                    )
                    me.button(
                        "Create Team",
                        on_click=on_create_team_click,
                        type="raised",
                        disabled=not page_state.new_team_name,
                    )

                me.divider()

                # Assign User to Team
                me.text(
                    "Assign User to Team",
                    type="headline-6",
                    style=me.Style(margin=me.Margin(top=16, bottom=8)),
                )
                with me.box(
                    style=me.Style(
                        display="flex",
                        flex_direction="row",
                        gap=16,
                        align_items="center",
                    ),
                ):
                    # Fetch all teams for dropdown
                    teams = get_teams_for_user(
                        app_state.user_email, app_state.user_role,
                    )
                    team_options = [
                        me.SelectOption(label=t.name, value=t.id) for t in teams
                    ]

                    me.select(
                        label="Select Team",
                        options=team_options,
                        on_selection_change=on_select_team_change,
                        style=me.Style(flex_grow=1),
                    )
                    me.input(
                        label="User Email",
                        value=page_state.user_email_to_assign,
                        on_blur=on_user_email_blur,
                        style=me.Style(flex_grow=1),
                    )

                    role_options = [
                        me.SelectOption(label="Manager", value="manager"),
                        me.SelectOption(label="Contributor", value="contributor"),
                    ]
                    me.select(
                        label="Role",
                        options=role_options,
                        on_selection_change=on_role_change,
                        value=page_state.role_to_assign,
                        style=me.Style(width="150px"),
                    )

                    me.button(
                        "Assign",
                        on_click=on_assign_user_click,
                        type="raised",
                        disabled=not (
                            page_state.selected_team_id
                            and page_state.user_email_to_assign
                        ),
                    )

        # --- Manager Section ---
        with me.box(
            style=me.Style(
                background=me.theme_var("surface"),
                padding=me.Padding.all(16),
                border_radius=8,
            ),
        ):
            me.text(
                "My Teams",
                type="headline-5",
                style=me.Style(margin=me.Margin(bottom=16)),
            )

            teams = get_teams_for_user(app_state.user_email, app_state.user_role)

            if not teams:
                me.text("You are not managing any teams.")
            else:
                for team in teams:
                    with me.expansion_panel(title=team.name, icon="group"), me.box(
                        style=me.Style(
                            display="flex",
                            flex_direction="column",
                            gap=16,
                            padding=me.Padding.all(16),
                        ),
                    ):


                            # Assets Section
                            me.text(
                                "Team Assets",
                                type="headline-6",
                                style=me.Style(margin=me.Margin(top=8)),
                            )
                            me.text(f"Total Assets: {len(team.assets)}")
                            me.button(
                                "Manage Team Assets",
                                on_click=on_manage_assets_click,
                                type="stroked",
                            )


# --- Event Handlers ---


def on_manage_assets_click(_: me.ClickEvent) -> None:
    """Navigate to team assets page."""
    me.navigate("/team_assets")


def on_new_team_name_blur(e: me.InputBlurEvent) -> None:
    """Handle new team name blur."""
    state = me.state(PageState)
    state.new_team_name = e.value


def on_create_team_click(_: me.ClickEvent):  # noqa: ANN201
    """Handle create team click."""
    app_state = me.state(AppState)
    page_state = me.state(PageState)
    try:
        create_team(page_state.new_team_name, app_state.user_email)
        page_state.show_snackbar = True
        page_state.snackbar_message = (
            f"Team '{page_state.new_team_name}' created successfully."
        )
        page_state.new_team_name = ""
    except Exception as ex:  # noqa: BLE001
        page_state.show_snackbar = True
        page_state.snackbar_message = f"Error creating team: {ex}"
    yield


def on_select_team_change(e: me.SelectSelectionChangeEvent) -> None:
    """Handle team selection change."""
    state = me.state(PageState)
    state.selected_team_id = e.value


def on_user_email_blur(e: me.InputBlurEvent) -> None:
    """Handle user email blur."""
    state = me.state(PageState)
    state.user_email_to_assign = e.value


def on_role_change(e: me.SelectSelectionChangeEvent) -> None:
    """Handle role change."""
    state = me.state(PageState)
    state.role_to_assign = e.value


def on_assign_user_click(_: me.ClickEvent):  # noqa: ANN201
    """Handle assign user click."""
    page_state = me.state(PageState)
    try:
        if page_state.role_to_assign == "manager":
            add_manager_to_team(
                page_state.selected_team_id, page_state.user_email_to_assign,
            )
            current_role = get_user_role(page_state.user_email_to_assign)
            if current_role == "contributor":
                set_user_role(page_state.user_email_to_assign, "manager")
        else:
            add_member_to_team(
                page_state.selected_team_id, page_state.user_email_to_assign,
            )

        page_state.show_snackbar = True
        page_state.snackbar_message = f"Assigned {page_state.user_email_to_assign} as {page_state.role_to_assign} successfully."
        page_state.user_email_to_assign = ""
    except Exception as ex:  # noqa: BLE001
        page_state.show_snackbar = True
        page_state.snackbar_message = f"Error assigning user: {ex}"
    yield



