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
from enum import Enum
from typing import Any

# Dedicated logger for tracking the suppressed error
race_condition_logger = logging.getLogger("genmedia.race_condition_tracker")

# Map of Veo Safety Error Codes to Categories
SAFETY_CODE_MAP = {
    "58061214": {
        "category": "Child",
        "description": "Rejects requests to generate content depicting children if personGeneration isn't set to 'allow_all' or if the project isn't on the allowlist for this feature.",
    },
    "17301594": {
        "category": "Child",
        "description": "Rejects requests to generate content depicting children if personGeneration isn't set to 'allow_all' or if the project isn't on the allowlist for this feature.",
    },
    "29310472": {
        "category": "Celebrity",
        "description": "Rejects requests to generate a photorealistic representation of a prominent person or if the project isn't on the allowlist for this feature.",
    },
    "15236754": {
        "category": "Celebrity",
        "description": "Rejects requests to generate a photorealistic representation of a prominent person or if the project isn't on the allowlist for this feature.",
    },
    "64151117": {
        "category": "Video safety violation",
        "description": "General safety violation.",
    },
    "42237218": {
        "category": "Video safety violation",
        "description": "General safety violation.",
    },
    "62263041": {
        "category": "Dangerous content",
        "description": "Potentially dangerous content.",
    },
    "57734940": {"category": "Hate", "description": "Hate-related content."},
    "22137204": {"category": "Hate", "description": "Hate-related content."},
    "74803281": {
        "category": "Other",
        "description": "Miscellaneous safety issues with the request.",
    },
    "29578790": {
        "category": "Other",
        "description": "Miscellaneous safety issues with the request.",
    },
    "42876398": {
        "category": "Other",
        "description": "Miscellaneous safety issues with the request.",
    },
    "89371032": {
        "category": "Prohibited content",
        "description": "Prohibited content related to child safety or other sensitive content.",
    },
    "49114662": {
        "category": "Prohibited content",
        "description": "Prohibited content related to child safety or other sensitive content.",
    },
    "63429089": {
        "category": "Prohibited content",
        "description": "Prohibited content related to child safety or other sensitive content.",
    },
    "72817394": {
        "category": "Prohibited content",
        "description": "Prohibited content related to child safety or other sensitive content.",
    },
    "60599140": {
        "category": "Prohibited content",
        "description": "Prohibited content related to child safety or other sensitive content.",
    },
    "35561574": {
        "category": "Third-party content",
        "description": "Guardrails related to third-party content.",
    },
    "35561575": {
        "category": "Third-party content",
        "description": "Guardrails related to third-party content.",
    },
    "90789179": {"category": "Sexual", "description": "Sexual or suggestive content."},
    "43188360": {"category": "Sexual", "description": "Sexual or suggestive content."},
    "78610348": {"category": "Toxic", "description": "Toxic content."},
    "61493863": {"category": "Violence", "description": "Violent content."},
    "56562880": {"category": "Violence", "description": "Violent content."},
    "32635315": {"category": "Vulgar", "description": "Vulgar content."},
}


def get_safety_reason(error_message: str) -> str | None:
    """Extracts the safety code from the error message and returns the mapped category."""
    match = re.search(r"Support codes?:\s*(\d+)", error_message)
    if match:
        code = match.group(1)
        safety_info = SAFETY_CODE_MAP.get(
            code,
            {
                "category": "Unknown Safety Issue",
                "description": "No additional details available.",
            },
        )
        category = safety_info["category"]
        description = safety_info["description"]
        return f"Safety Filter Blocked: {category} (Support Code: {code}). {description} Please adjust your request."
    return None


class ErrorCategory(str, Enum):
    CAPACITY_EXHAUSTED = "CAPACITY_EXHAUSTED"  # Code 8 / 429 Quota / High Load
    SAFETY_FILTER = "SAFETY_FILTER"  # RAI moderation / Recitation filter
    CLIENT_TIMEOUT = "CLIENT_TIMEOUT"  # Generation duration exceeded threshold
    INVALID_ARGUMENT = (
        "INVALID_ARGUMENT"  # Unsupported resolution, aspect ratio, prompt length
    )
    AUTH_ERROR = "AUTH_ERROR"  # Permission / IAM failure
    NOT_FOUND = "NOT_FOUND"  # Resource, object, or bucket 404
    UPSTREAM_FAILURE = "UPSTREAM_FAILURE"  # 500 / 503 internal backend error
    UNKNOWN = "UNKNOWN"


class GenerationError(Exception):
    """Custom exception for video generation and generative model errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory | str = ErrorCategory.UNKNOWN,
        code: int | None = None,
        retryable: bool = False,
    ):
        self.message = message
        self.category = (
            category.value if isinstance(category, ErrorCategory) else str(category)
        )
        self.code = code
        self.retryable = retryable
        super().__init__(self.message)


class AsyncVeoPollingFailedError(Exception):
    """Exception for failures during async Veo job polling."""


def classify_error(exc: Exception) -> dict[str, Any]:
    """Classifies an exception into a structured canonical error dict.

    Returns a dict with keys: category, code, message, retryable.
    """
    if isinstance(exc, GenerationError):
        return {
            "category": exc.category,
            "code": exc.code,
            "message": exc.message,
            "retryable": exc.retryable,
        }

    code = getattr(exc, "code", getattr(exc, "status_code", None))
    msg = str(exc)
    msg_lower = msg.lower()
    exc_type_name = type(exc).__name__

    # 1. Capacity / Quota
    if (
        code in (429, 8)
        or "resourceexhausted" in exc_type_name.lower()
        or any(
            k in msg_lower
            for k in [
                "quota",
                "resource_exhausted",
                "capacity",
                "rate limit",
                "high load",
            ]
        )
        or bool(re.search(r"\b429\b", msg_lower))
    ):
        return {
            "category": ErrorCategory.CAPACITY_EXHAUSTED.value,
            "code": code or 429,
            "message": msg,
            "retryable": True,
        }

    # 2. Safety Filter / RAI
    if any(
        k in msg_lower
        for k in [
            "recitation",
            "harmful",
            "rai",
            "content policy",
            "finish_reason",
            "safety_filter_exceeded",
        ]
    ) or bool(
        re.search(r"\b(block|blocked|safety filter|safety violation)\b", msg_lower)
    ):
        return {
            "category": ErrorCategory.SAFETY_FILTER.value,
            "code": code,
            "message": msg,
            "retryable": False,
        }

    # 3. Timeout
    if (
        code in (504, 4)
        or "deadlineexceeded" in exc_type_name.lower()
        or "timeout" in exc_type_name.lower()
        or any(k in msg_lower for k in ["timeout", "timed out", "deadline exceeded"])
        or bool(re.search(r"\b504\b", msg_lower))
    ):
        return {
            "category": ErrorCategory.CLIENT_TIMEOUT.value,
            "code": code or 504,
            "message": msg,
            "retryable": True,
        }

    # 4. Invalid Argument
    if (
        code in (400, 3)
        or "invalidargument" in exc_type_name.lower()
        or any(
            k in msg_lower
            for k in [
                "invalidargument",
                "invalid_argument",
                "invalid argument",
                "unsupported",
                "invalid prompt",
                "bad request",
            ]
        )
        or bool(re.search(r"\b400\b", msg_lower))
    ):
        return {
            "category": ErrorCategory.INVALID_ARGUMENT.value,
            "code": code or 400,
            "message": msg,
            "retryable": False,
        }

    # 5. Auth Error
    if (
        code in (401, 403, 7, 16)
        or any(
            k in exc_type_name.lower() for k in ["unauthenticated", "permissiondenied"]
        )
        or any(k in msg_lower for k in ["permission denied", "unauthorized", "iam"])
        or bool(re.search(r"\b(401|403)\b", msg_lower))
    ):
        return {
            "category": ErrorCategory.AUTH_ERROR.value,
            "code": code or 403,
            "message": msg,
            "retryable": False,
        }

    # 6. Not Found (404)
    if (
        code in (404, 5)
        or "notfound" in exc_type_name.lower()
        or any(k in msg_lower for k in ["not found", "notfound"])
        or bool(re.search(r"\b404\b", msg_lower))
    ):
        return {
            "category": ErrorCategory.NOT_FOUND.value,
            "code": code or 404,
            "message": msg,
            "retryable": False,
        }

    # 7. Upstream / Server Error
    if (
        code in (500, 502, 503, 13, 14)
        or any(
            k in exc_type_name.lower()
            for k in ["internalservererror", "serviceunavailable"]
        )
        or any(
            k in msg_lower
            for k in [
                "internal server error",
                "service unavailable",
                "backend error",
            ]
        )
        or bool(re.search(r"\b(500|502|503)\b", msg_lower))
    ):
        return {
            "category": ErrorCategory.UPSTREAM_FAILURE.value,
            "code": code or 500,
            "message": msg,
            "retryable": True,
        }

    # Default
    return {
        "category": ErrorCategory.UNKNOWN.value,
        "code": code,
        "message": msg,
        "retryable": False,
    }


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
