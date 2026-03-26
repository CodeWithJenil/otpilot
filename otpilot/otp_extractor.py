"""OTP extraction from email content.

Uses regex-based pattern matching to find one-time passwords in email
subjects and bodies. Context-aware: only matches digit sequences near
OTP-related keywords.
"""

import re
from typing import Dict, List, Optional

# Keywords that indicate a digit sequence is likely an OTP
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

# Compile a single pattern for context words (case-insensitive)
_CONTEXT_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in _CONTEXT_WORDS) + r")\b",
    re.IGNORECASE,
)

# Pattern to find standalone 4–8 digit numbers
_OTP_DIGIT_PATTERN = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")


def _has_otp_context(text: str) -> bool:
    """Check whether the text contains OTP-related context words.

    Args:
        text: The text to search.

    Returns:
        True if at least one context word is found.
    """
    return bool(_CONTEXT_PATTERN.search(text))


def _find_otp_in_text(text: str) -> Optional[str]:
    """Search for a standalone 4–8 digit number in text that also contains OTP context words.

    The function checks for context words first, then returns the first
    digit match found.

    Args:
        text: The email subject or body text.

    Returns:
        The OTP string, or None if no match is found.
    """
    if not text or not _has_otp_context(text):
        return None

    match = _OTP_DIGIT_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def extract_otp(emails: List[Dict[str, str]]) -> Optional[str]:
    """Extract an OTP from a list of email dicts.

    Strategy (in priority order):
      1. Search each email's subject line for a 4–8 digit number with
         OTP context words.
      2. Search each email's body for the same pattern.
      3. Return the match from the most recent email (emails are assumed
         to be ordered most-recent-first).

    Args:
        emails: A list of dicts, each with ``subject`` and ``body`` keys.

    Returns:
        The extracted OTP string, or None if nothing was found.
    """
    if not emails:
        return None

    # Pass 1: search subjects (most-recent first)
    for email in emails:
        subject = email.get("subject", "")
        otp = _find_otp_in_text(subject)
        if otp:
            return otp

    # Pass 2: search bodies (most-recent first)
    for email in emails:
        body = email.get("body", "")
        otp = _find_otp_in_text(body)
        if otp:
            return otp

    return None
