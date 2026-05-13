import mesop as me
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

@me.component
def technical_metrics():
    pagestate = me.state(PageState)
    if (
        pagestate.has_audio_metrics
        and not pagestate.is_analyzing
        and not pagestate.is_loading
    ):
        with me.box(style=_ANALYSIS_BOX_STYLE):
            with me.expansion_panel(
                title="Technical Audio Metrics",
                icon="graphic_eq",
            ):
                metrics = pagestate.audio_metrics
                with me.box(
                    style=me.Style(
                        display="grid",
                        grid_template_columns="1fr 1fr",
                        gap=16,
                        padding=me.Padding.all(16),
                    ),
                ):
                    me.text(
                        f"Duration: {metrics.duration_sec:.2f}s",
                        style=me.Style(font_weight="bold"),
                    )
                    me.text(
                        f"Tempo: {metrics.estimated_tempo_bpm:.1f} BPM",
                        style=me.Style(font_weight="bold"),
                    )
                    me.text(f"Mean Pitch: {metrics.mean_pitch_hz:.1f} Hz")
                    me.text(f"Pitch Range: {metrics.pitch_range_hz:.1f} Hz")
