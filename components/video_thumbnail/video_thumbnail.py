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

"""Video thumbnail component wrapper."""

import typing

import mesop as me


@me.web_component(path="./video_thumbnail.js")
def video_thumbnail(
    *,
    video_src: str,
    thumbnail_src: str | None = None,
    selected: bool = False,
    on_click: typing.Callable[[me.WebEvent], None] | None = None,
    key: str | None = None,
) -> me.insert_web_component:
    """Render a clickable video thumbnail with mouse-over autoplay and selection state."""
    return me.insert_web_component(
        key=key,
        name="video-thumbnail",
        properties={
            "videoSrc": video_src,
            "thumbnailSrc": thumbnail_src or "",
            "selected": selected,
        },
        events={
            "thumbnailClick": on_click,
        },
    )
