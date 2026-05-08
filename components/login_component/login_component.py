import typing
import mesop as me

@me.web_component(path="./login_component.js")
def login_component(
    *,
    client_id: str,
    on_login: typing.Callable[[me.WebEvent], None] | None = None,
    key: str | None = None,
):
    return me.insert_web_component(
        key=key,
        name="login-component",
        properties={
            "clientId": client_id,
        },
        events={
            "login": on_login,
        },
    )
