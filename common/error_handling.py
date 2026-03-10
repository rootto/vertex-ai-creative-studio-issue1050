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

import logging
import re

# Dedicated logger for tracking the suppressed error
race_condition_logger = logging.getLogger("genmedia.race_condition_tracker")

# Map of Veo Safety Error Codes to Categories
SAFETY_CODE_MAP = {
    "58061214": {"category": "Child", "description": "Rejects requests to generate content depicting children if personGeneration isn't set to 'allow_all' or if the project isn't on the allowlist for this feature."},
    "17301594": {"category": "Child", "description": "Rejects requests to generate content depicting children if personGeneration isn't set to 'allow_all' or if the project isn't on the allowlist for this feature."},
    "29310472": {"category": "Celebrity", "description": "Rejects requests to generate a photorealistic representation of a prominent person or if the project isn't on the allowlist for this feature."},
    "15236754": {"category": "Celebrity", "description": "Rejects requests to generate a photorealistic representation of a prominent person or if the project isn't on the allowlist for this feature."},
    "64151117": {"category": "Video safety violation", "description": "General safety violation."},
    "42237218": {"category": "Video safety violation", "description": "General safety violation."},
    "62263041": {"category": "Dangerous content", "description": "Potentially dangerous content."},
    "57734940": {"category": "Hate", "description": "Hate-related content."},
    "22137204": {"category": "Hate", "description": "Hate-related content."},
    "74803281": {"category": "Other", "description": "Miscellaneous safety issues with the request."},
    "29578790": {"category": "Other", "description": "Miscellaneous safety issues with the request."},
    "42876398": {"category": "Other", "description": "Miscellaneous safety issues with the request."},
    "89371032": {"category": "Prohibited content", "description": "Prohibited content related to child safety or other sensitive content."},
    "49114662": {"category": "Prohibited content", "description": "Prohibited content related to child safety or other sensitive content."},
    "63429089": {"category": "Prohibited content", "description": "Prohibited content related to child safety or other sensitive content."},
    "72817394": {"category": "Prohibited content", "description": "Prohibited content related to child safety or other sensitive content."},
    "60599140": {"category": "Prohibited content", "description": "Prohibited content related to child safety or other sensitive content."},
    "35561574": {"category": "Third-party content", "description": "Guardrails related to third-party content."},
    "35561575": {"category": "Third-party content", "description": "Guardrails related to third-party content."},
    "90789179": {"category": "Sexual", "description": "Sexual or suggestive content."},
    "43188360": {"category": "Sexual", "description": "Sexual or suggestive content."},
    "78610348": {"category": "Toxic", "description": "Toxic content."},
    "61493863": {"category": "Violence", "description": "Violent content."},
    "56562880": {"category": "Violence", "description": "Violent content."},
    "32635315": {"category": "Vulgar", "description": "Vulgar content."}
}

def get_safety_reason(error_message: str) -> str | None:
    """Extracts the safety code from the error message and returns the mapped category."""
    match = re.search(r"Support codes?:\s*(\d+)", error_message)
    if match:
        code = match.group(1)
        safety_info = SAFETY_CODE_MAP.get(code, {"category": "Unknown Safety Issue", "description": "No additional details available."})
        category = safety_info["category"]
        description = safety_info["description"]
        return f"Safety Filter Blocked: {category} (Support Code: {code}). {description} Please adjust your request."
    return None


class GenerationError(Exception):
    """Custom exception for video generation errors."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AsyncVeoPollingFailedError(Exception):
    """Exception for failures during async Veo job polling."""



class UnknownHandlerIdFilter(logging.Filter):
    """A logging filter to suppress 'Unknown handler id' errors."""

    def filter(self, record):
        # Suppress the specific benign error message from Mesop
        if "Unknown handler id" in record.getMessage():
            # Log to a separate, non-disruptive logger for tracking purposes
            race_condition_logger.info(
                "Suppressed 'Unknown handler id' error",
                extra={"original_record": record.getMessage()},
            )
            return False  # Prevent the original logger from processing it
        return True
