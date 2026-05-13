import json
import mesop as me
from components.pill import pill
from state.lyria_state import PageState

# Combined style for the analysis display box
_ANALYSIS_BOX_STYLE = me.Style(
    background=me.theme_var("background"),
    border_radius=12,
    box_shadow=("0 3px 1px -2px #0003, 0 2px 2px #00000024, 0 1px 5px #0000001f"),
    padding=me.Padding(top=16, left=16, right=16, bottom=16),
    display="flex",
    flex_direction="column",
    margin=me.Margin(top=16),
)

# Combined style for the analysis error display box
_ANALYSIS_ERROR_BOX_STYLE = me.Style(
    background=me.theme_var("background"),
    border_radius=12,
    padding=me.Padding(top=16, left=16, right=16, bottom=16),
    display="flex",
    flex_direction="column",
    margin=me.Margin(top=16),
    border=me.Border.all(me.BorderSide(color=me.theme_var("error"), width=1)),
)

@me.component
def audio_critic():
    pagestate = me.state(PageState)
    if (
        pagestate.audio_analysis_result_json
        and not pagestate.is_analyzing
        and not pagestate.is_loading
    ):
        try:
            analysis = json.loads(pagestate.audio_analysis_result_json)
            if not isinstance(analysis, dict):
                raise ValueError("Response is not a valid JSON object")
            with me.box(style=_ANALYSIS_BOX_STYLE):
                me.text(
                    "Music Critic",
                    type="headline-5",
                    style=me.Style(margin=me.Margin(bottom=12)),
                )
                if analysis.get("genre-quality"):
                    with me.box(style=me.Style(margin=me.Margin(bottom=10))):
                        genre_list = analysis["genre-quality"]

                        if isinstance(genre_list, list):
                            with me.box(
                                style=me.Style(
                                    display="flex",
                                    flex_direction="row",
                                    gap=5,
                                    margin=me.Margin(bottom=5, top=10),
                                ),
                            ):
                                for item in genre_list:
                                    pill(item, pill_type="genre")
                        else:
                            me.text(str(genre_list))

                with me.box(
                    style=me.Style(
                        margin=me.Margin(bottom=10),
                        display="flex",
                        flex_direction="row",
                        gap=5,
                    ),
                ):
                    if analysis.get("audio-analysis"):
                        with me.box(
                            style=me.Style(
                                flex=1,
                                margin=me.Margin(bottom=10),
                                padding=me.Padding(right=10),
                            ),
                        ):
                            me.text(
                                "Description",
                                style=me.Style(font_weight="bold"),
                            )
                            me.markdown(analysis["audio-analysis"])

                    if analysis.get("prompt-alignment"):
                        with me.box(
                            style=me.Style(
                                flex=1,
                                margin=me.Margin(bottom=10),
                                padding=me.Padding(left=10),
                            ),
                        ):
                            me.text(
                                "Prompt Alignment",
                                style=me.Style(font_weight="bold"),
                            )
                            me.markdown(analysis["prompt-alignment"])

        except Exception as e:
            with me.box(style=_ANALYSIS_ERROR_BOX_STYLE):
                me.text(
                    "Audio Analysis Failed",
                    type="headline-6",
                    style=me.Style(
                        color=me.theme_var("error"),
                        margin=me.Margin(bottom=12),
                    ),
                )
                me.text(f"Error: Could not display analysis data ({e}).")

    # Analysis Error Display
    elif (
        pagestate.analysis_error_message
        and not pagestate.is_analyzing
        and not pagestate.is_loading
    ):
        with me.box(style=_ANALYSIS_ERROR_BOX_STYLE):
            me.text(
                "Audio Analysis Failed",
                type="headline-6",
                style=me.Style(
                    color=me.theme_var("error"),
                    margin=me.Margin(bottom=12),
                ),
            )
            me.text(pagestate.analysis_error_message)
