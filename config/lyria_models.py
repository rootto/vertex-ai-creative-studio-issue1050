# Copyright 2025 Google LLC
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

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LyriaModelConfig:
    """Configuration for a specific Lyria model."""

    version_id: str  # Short ID for UI/Logic
    model_name: str  # Full API Model ID
    display_name: str  # Human-readable name

    # Capabilities
    supports_lyrics: bool = False
    supports_images: bool = False
    supports_c2pa: bool = False
    max_samples: int = 1


# Single source of truth
LYRIA_MODELS: List[LyriaModelConfig] = [
    LyriaModelConfig(
        version_id="2",
        model_name="lyria-002",
        display_name="Lyria 2",
        supports_lyrics=False,
        supports_images=False,
        supports_c2pa=False,
        max_samples=4,
    ),
    LyriaModelConfig(
        version_id="3-clip-preview",
        model_name="lyria-3-clip-preview",
        display_name="Lyria 3 Clip",
        supports_lyrics=True,
        supports_images=True,
        supports_c2pa=True,
    ),
    LyriaModelConfig(
        version_id="3-pro-preview",
        model_name="lyria-3-pro-preview",
        display_name="Lyria 3 Pro",
        supports_lyrics=True,
        supports_images=True,
        supports_c2pa=True,
    ),
]


def get_lyria_model_config(
    model_name_or_version: str,
) -> Optional[LyriaModelConfig]:
    """Finds config by either full model name or short version ID."""
    for model in LYRIA_MODELS:
        if (
            model.model_name == model_name_or_version
            or model.version_id == model_name_or_version
        ):
            return model
    return None
