import mesop as me
from dataclasses import field
from typing import Optional

@me.stateclass
class AudioMetricsState:
    mean_pitch_hz: float = 0.0
    pitch_std_hz: float = 0.0
    pitch_range_hz: float = 0.0
    jitter_percent: float = 0.0
    shimmer_db: float = 0.0
    hnr_db: float = 0.0
    estimated_tempo_bpm: float = 0.0
    duration_sec: float = 0.0

@me.stateclass
class PageState:
    """Local Page State for Lyria"""

    is_loading: bool = False
    is_analyzing: bool = False
    is_generating_lyrics: bool = False

    loading_operation_message: str = ""

    music_prompt_input: str = ""
    music_prompt_placeholder: str = ""
    original_user_prompt: str = ""
    music_prompt_textarea_key: int = 0
    music_gcs_uris: list[str] = field(default_factory=list)
    music_display_urls: list[str] = field(default_factory=list)
    selected_track_index: int = 0

    selected_model_id: str = "3-clip-preview"
    sample_count: int = 1
    
    lyrics_input: str = ""
    lyrics_placeholder: str = ""
    
    uploaded_image_gcs_uris: list[str] = field(default_factory=list)
    uploaded_image_mime_types: list[str] = field(default_factory=list)
    uploaded_image_display_urls: list[str] = field(default_factory=list)
    c2pa_manifest_json: str = ""
    generated_text: list[str] = field(default_factory=list)

    timing: str = ""

    show_error_dialog: bool = False
    error_message: str = ""

    audio_analysis_result_json: Optional[str] = None
    analysis_error_message: str = ""

    info_dialog_open: bool = False

    audio_metrics: AudioMetricsState = field(default_factory=AudioMetricsState)
    has_audio_metrics: bool = False
