import json
import mesop as me
from components.pill import pill
from components.content_credentials.content_credentials import content_credentials_viewer
from components.search_entry_point.search_entry_point import search_entry_point

def render_grounding_info(grounding_info_str: str, theme_mode: str):
    """Renders the grounding information (search entry point and sources)."""
    if not grounding_info_str:
        return
    try:
        info = json.loads(grounding_info_str)
        if not info:
            return
        with me.expansion_panel(title="Search Sources", icon="travel_explore"):
            if info.get("search_entry_point") and "rendered_content" in info["search_entry_point"]:
                search_entry_point(
                    html_content=info["search_entry_point"]["rendered_content"],
                    theme_mode=theme_mode,
                )
            if info.get("chunks"):
                me.text("Sources", type="headline-6", style=me.Style(margin=me.Margin(top=16, bottom=8)))
                with me.box(style=me.Style(display="flex", flex_direction="column", gap=4)):
                    for chunk in info["chunks"]:
                        if chunk.get("uri"):
                            with me.box(style=me.Style(display="flex", flex_direction="row", align_items="center", gap=4)):
                                me.icon("link", style=me.Style(font_size=16, color=me.theme_var("primary")))
                                me.link(
                                    text=chunk.get("title", "Source"),
                                    url=chunk["uri"],
                                    style=me.Style(
                                        color=me.theme_var("primary"),
                                        text_decoration="none"
                                    )
                                )
    except Exception as e:
        me.text(f"Error parsing grounding info: {e}")
        me.text(grounding_info_str)

@me.component
def gemini_image_gallery(state, app_state, on_thumbnail_click, custom_placeholder_icon: str = "image", custom_evaluations_ui=None):
    if state.generation_complete and not state.generated_image_urls:
        me.text("No images returned.")
        return
    if not state.generated_image_urls:
        with me.box(style=me.Style(opacity=0.2, width=128, height=128, color=me.theme_var("on-surface-variant"))):
            if custom_placeholder_icon.endswith(".svg") or custom_placeholder_icon == "banana":
                from components.svg_icon.svg_icon import svg_icon
                svg_icon(icon_name=custom_placeholder_icon)
            else:
                me.icon(custom_placeholder_icon, style=me.Style(font_size=128))
        return
    with me.box(style=me.Style(width="100%", height="100%", display="flex", flex_direction="column")):
        if len(state.generated_image_urls) == 1:
            _single_image_view(state, app_state, custom_evaluations_ui)
        else:
            _multi_image_view(state, app_state, on_thumbnail_click, custom_evaluations_ui)

def _single_image_view(state, app_state, custom_evaluations_ui):
    image_url = state.generated_image_urls[0]
    caption = state.generated_image_captions[0] if getattr(state, 'generated_image_captions', None) else ""
    with me.box(style=me.Style(position="relative", width="100%", height="100%", display="flex", justify_content="center")):
        me.image(src=image_url, alt=caption, style=me.Style(width="100%", max_height="85vh", object_fit="contain", border_radius=8))
        with me.box(style=me.Style(position="absolute", top=16, right=16)):
            manifest_json = getattr(state, 'c2pa_manifests', {}).get(image_url)
            if manifest_json:
                content_credentials_viewer(manifest=manifest_json)
    if state.generated_resolution:
        with me.box(style=me.Style(margin=me.Margin(top=8))):
            pill(label=f"Resolution: {state.generated_resolution}", pill_type="resolution")
    if custom_evaluations_ui:
        custom_evaluations_ui(image_url)
    if getattr(state, 'thoughts', None):
        with me.box(style=me.Style(margin=me.Margin(top=16), width="100%")):
            with me.expansion_panel(title="Thoughts", icon="psychology"):
                me.markdown(state.thoughts)
    if getattr(state, 'grounding_info', None):
        with me.box(style=me.Style(margin=me.Margin(top=16), width="100%")):
            render_grounding_info(state.grounding_info, app_state.theme_mode)

def _multi_image_view(state, app_state, on_thumbnail_click, custom_evaluations_ui):
    with me.box(style=me.Style(display="flex", flex_direction="column", gap=16)):
        selected_index = state.generated_image_urls.index(state.selected_image_url) if getattr(state, 'selected_image_url', None) in state.generated_image_urls else 0
        caption = state.generated_image_captions[selected_index] if getattr(state, 'generated_image_captions', None) and selected_index < len(state.generated_image_captions) else ""
        with me.box(style=me.Style(position="relative", width="100%", display="flex", justify_content="center")):
            me.image(src=state.selected_image_url, alt=caption, style=me.Style(width="100%", max_height="75vh", object_fit="contain", border_radius=8))
            with me.box(style=me.Style(position="absolute", top=16, right=16)):
                manifest_json = getattr(state, 'c2pa_manifests', {}).get(state.selected_image_url)
                if manifest_json:
                    content_credentials_viewer(manifest=manifest_json)
        if state.generated_resolution:
            with me.box(style=me.Style(margin=me.Margin(top=8))):
                pill(label=f"Resolution: {state.generated_resolution}", pill_type="resolution")
        if custom_evaluations_ui:
            custom_evaluations_ui(state.selected_image_url)
        with me.box(style=me.Style(display="flex", flex_direction="row", gap=16, justify_content="center")):
            for i, url in enumerate(state.generated_image_urls):
                is_selected = url == state.selected_image_url
                thumb_caption = state.generated_image_captions[i] if getattr(state, 'generated_image_captions', None) and i < len(state.generated_image_captions) else ""
                with me.box(key=url, on_click=on_thumbnail_click, style=me.Style(padding=me.Padding.all(4), border=me.Border.all(me.BorderSide(width=4, style="solid", color=me.theme_var("secondary") if is_selected else "transparent")), border_radius=12, cursor="pointer")):
                    me.image(src=url, alt=thumb_caption, style=me.Style(width=100, height=100, object_fit="cover", border_radius=6))
        if getattr(state, 'thoughts', None):
            with me.box(style=me.Style(margin=me.Margin(top=16), width="100%")):
                with me.expansion_panel(title="Thoughts", icon="psychology"):
                    me.markdown(state.thoughts)
        if getattr(state, 'grounding_info', None):
            with me.box(style=me.Style(margin=me.Margin(top=16), width="100%")):
                render_grounding_info(state.grounding_info, app_state.theme_mode)
