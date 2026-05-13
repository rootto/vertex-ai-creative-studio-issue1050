from typing import Callable, Any
import mesop as me

@me.web_component(path="./banana_button.js")
def banana_button(
    *,
    selected: bool = False,
    badge: str = "",
    label: str = "",
    model_name: str = "",
    on_click: Callable[[me.WebEvent], Any],
    key: str | None = None,
):
    """
    A custom web component representing a selectable banana model button.
    """
    if key is None:
        key = model_name
        
    return me.insert_web_component(
        key=key,
        name="banana-button",
        properties={
            "selected": selected,
            "badge": badge,
            "label": label,
            "modelName": model_name,
        },
        events={
            "modelSelected": on_click,
        },
    )
