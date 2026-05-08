import mesop as me

@me.web_component(path="./navigate_button.js")
def navigate_button(*, label: str, url: str, key: str | None = None):
    return me.insert_web_component(
        key=key,
        name="navigate-button",
        properties={
            "label": label,
            "url": url,
        },
    )
