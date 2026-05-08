import mesop as me

from components.login_component.login_component import login_component
from state.state import AppState, update_user_and_session_info
from common.auth import verify_google_id_token
from config.default import Default


@me.stateclass
class PageState:
    pass


def on_login(e: me.WebEvent):
    print(f"DEBUG: on_login entered. Event value: {e.value}")
    state = me.state(AppState)
    id_token_str = e.value["value"]

    try:
        id_info = verify_google_id_token(id_token_str)
        email = id_info["email"]
        print(f"User logged in: {email}")

        # Update state with user email
        yield from update_user_and_session_info(email, state.session_id)

        # Navigate to welcome page
        me.navigate("/welcome")
    except Exception as ex:
        print(f"Login failed: {ex}")
    yield


def navigate_to_login(e: me.ClickEvent):
    me.navigate("/login")


@me.page(path="/login", title="Login - GenMedia Creative Studio")
def page():
    with me.box(style=me.Style(display="flex", flex_direction="column", align_items="center", justify_content="center", height="100vh")):
        me.text("Welcome to GenMedia Creative Studio", type="headline-4")
        me.text("Please sign in to access the application.")
        cfg = Default()
        login_component(client_id=cfg.GOOGLE_CLIENT_ID, on_login=on_login)
