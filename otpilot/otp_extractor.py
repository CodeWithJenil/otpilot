"""OTP extraction utilities for Gmail message content.

This module applies context-aware regular expressions to email subjects and
bodies to identify one-time passwords. Within OTPilot, it is responsible for
converting fetched message text into a single OTP candidate suitable for
clipboard copy.

Key exports:
    extract_otp: Extract the highest-priority OTP from recent emails.
"""

import re
from typing import Dict, List, Optional

# Keywords that indicate a nearby numeric token is likely an OTP.
_CONTEXT_WORDS = [
    "otp",
    "code",
    "verify",
    "verification",
    "one-time",
    "one time",
    "passcode",
    "pass code",
    "password",
    "pin",
    "token",
    "authentication",
    "confirm",
    "confirmation",
    "security",
    "login",
    "sign-in",
    "signin",
    "2fa",
    "mfa",
]

# Compile one case-insensitive context matcher for OTP-adjacent language.
_CONTEXT_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in _CONTEXT_WORDS) + r")\b",
    re.IGNORECASE,
)

# Match standalone numeric sequences likely used as OTPs.
_OTP_DIGIT_PATTERN = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")


def _has_otp_context(text: str) -> bool:
    """Check whether text contains OTP-related context keywords.

    Args:
        text (str): Text to inspect.

    Returns:
        bool: ``True`` when OTP context language is present.
    """
    return bool(_CONTEXT_PATTERN.search(text))


def _find_otp_in_text(text: str) -> Optional[str]:
    """Extract the first OTP-like number from context-qualified text.

    The function first validates that the text contains OTP-related keywords,
    then returns the first standalone 4-8 digit match.

    Args:
        text (str): Email subject or body text.

    Returns:
        Optional[str]: OTP digits when found, otherwise ``None``.
    """
    if not text or not _has_otp_context(text):
        return None

    match = _OTP_DIGIT_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def extract_otp(emails: List[Dict[str, str]]) -> Optional[str]:
    """Extract an OTP from recent emails using priority-based scanning.

    Search order:
    1. Subject lines from most recent to oldest.
    2. Message bodies from most recent to oldest.

    Args:
        emails (List[Dict[str, str]]): Email dictionaries containing at least
            ``subject`` and ``body`` keys.

    Returns:
        Optional[str]: First matching OTP candidate, or ``None`` if absent.

    Raises:
        None: This function does not raise application-level exceptions.
    """
    if not emails:
        return None

    # Pass 1: subjects often contain concise OTP phrases from providers.
    for email in emails:
        subject = email.get("subject", "")
        otp = _find_otp_in_text(subject)
        if otp:
            return otp

    # Pass 2: fallback to body scanning for providers that omit subject OTPs.
    for email in emails:
        body = email.get("body", "")
        otp = _find_otp_in_text(body)
        if otp:
            return otp

    return None
