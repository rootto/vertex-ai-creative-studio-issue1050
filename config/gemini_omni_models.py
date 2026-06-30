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
"""Gemini Omni model configurations."""

from dataclasses import dataclass


@dataclass
class GeminiOmniModelConfig:
    """Configuration for a specific Gemini Omni model version."""

    version_id: str
    model_name: str
    display_name: str
    supported_modes: list[str]
    supported_aspect_ratios: list[str]
    min_duration: int
    max_duration: int
    default_duration: int


GEMINI_OMNI_MODELS: list[GeminiOmniModelConfig] = [
    GeminiOmniModelConfig(
        version_id="gemini-omni-flash-preview",
        model_name="gemini-omni-flash-preview",
        display_name="Gemini Omni Flash (Preview)",
        supported_modes=["t2v", "i2v", "r2v", "editing"],
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        min_duration=1,
        max_duration=10,
        default_duration=10,
    ),
]


def get_omni_model_config(version_id: str) -> GeminiOmniModelConfig | None:
    """Helper to find config by version_id."""
    for model in GEMINI_OMNI_MODELS:
        if model.version_id == version_id:
            return model
    return None
