"""Gmail API integration and OAuth flow for OTPilot.

This module handles Supabase-backed Google OAuth login, token loading, and
retrieval of recent Gmail messages for OTP extraction. It is OTPilot's bridge
between local runtime services and remote Gmail APIs.

Key exports:
    run_oauth_flow: Run browser-based OAuth and persist the provider token.
    fetch_recent_emails: Retrieve normalized recent inbox messages for OTP scan.
    NotAuthenticatedError: Raised when no usable token exists.
    GmailAuthError: Raised when auth state or auth flow is invalid.
"""

import base64
import os
import re
import time
import uuid
import webbrowser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from otpilot.config import get_config
from otpilot.token_store import load_token, save_token

SCOPES: list = ["https://www.googleapis.com/auth/gmail.readonly"]
# DEFAULT_AUTH_BASE_URL = "https://otpilot-git-codex-replace-oauth-fce1ef-codewithjenils-projects.vercel.app"
# DEFAULT_AUTH_BASE_URL = "https://solid-space-barnacle-9vrvwx4grpfpp76-3000.app.github.dev/"
DEFAULT_AUTH_BASE_URL = "https://jenil-otpilot.vercel.app"
OTPILOT_AUTH_BASE_URL = os.getenv("OTPILOT_AUTH_BASE_URL", DEFAULT_AUTH_BASE_URL)


class NotAuthenticatedError(Exception):
    """Error raised when OTPilot has no stored Google access token.

    This exception signals that the user must run setup authentication before
    Gmail requests can proceed.

    Attributes:
        args: Exception message tuple inherited from ``Exception``.
    """

    def __init__(self, message: str = "Not authenticated. Run `otpilot setup` to sign in.") -> None:
        """Initialize a missing-authentication error.

        Args:
            message (str): Human-readable remediation message.

        Returns:
            None: This constructor does not return a value.

        Raises:
            None: The constructor itself does not raise additional exceptions.
        """
        super().__init__(message)


class GmailAuthError(Exception):
    """Error raised when OAuth or token state is invalid for Gmail access.

    This exception is used for malformed token payloads, failed auth session
    responses, and OAuth timeout conditions.

    Attributes:
        args: Exception message tuple inherited from ``Exception``.
    """

    def __init__(self, message: str = "Authentication failed. Run `otpilot setup` to re-authenticate.") -> None:
        """Initialize a Gmail authentication error.

        Args:
            message (str): Human-readable remediation message.

        Returns:
            None: This constructor does not return a value.

        Raises:
            None: The constructor itself does not raise additional exceptions.
        """
        super().__init__(message)


def _load_credentials() -> Credentials:
    """Load OAuth credentials from local token storage.

    Returns:
        Credentials: Google OAuth credentials scoped for read-only Gmail access.

    Raises:
        NotAuthenticatedError: If no token payload is stored.
        GmailAuthError: If the stored token payload is invalid.
    """
    token_payload = load_token()
    if not token_payload:
        raise NotAuthenticatedError()

    provider_token = token_payload.get("access_token")
    if not provider_token or not isinstance(provider_token, str):
        raise GmailAuthError("Invalid stored token. Run `otpilot setup` to sign in again.")

    return Credentials(token=provider_token, scopes=SCOPES)


def _normalize_auth_base_url(auth_base_url: str) -> str:
    """Normalize auth URL roots by stripping known API route suffixes.

    Args:
        auth_base_url (str): Supabase auth endpoint base or direct route URL.

    Returns:
        str: Deployment base URL without ``/api/auth/*`` suffixes.
    """
    normalized = auth_base_url.rstrip("/")
    for suffix in ("/api/auth/callback", "/api/auth/start", "/api/auth/session"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def run_oauth_flow(auth_base_url: str = OTPILOT_AUTH_BASE_URL) -> Credentials:
    """Run Supabase Google OAuth flow and persist the provider token.

    Args:
        auth_base_url (str): Base URL for OTPilot auth APIs.

    Returns:
        Credentials: Google OAuth credentials built from the saved provider token.

    Raises:
        GmailAuthError: If auth session polling fails, returns invalid data,
            or times out.
    """
    session_key = uuid.uuid4().hex
    base_url = _normalize_auth_base_url(auth_base_url)
    auth_url = f"{base_url}/api/auth/start?{urlencode({'session_key': session_key})}"

    # Launch browser to let the user complete Supabase-hosted Google OAuth.
    webbrowser.open(auth_url)

    session_url = f"{base_url}/api/auth/session?{urlencode({'session_key': session_key})}"

    start = time.time()
    while time.time() - start < 180:
        # Poll the session endpoint until provider token issuance completes.
        response = requests.get(session_url, timeout=10)
        if response.status_code == 202:
            time.sleep(2)
            continue
        if response.status_code != 200:
            raise GmailAuthError(f"Auth session failed ({response.status_code}): {response.text}")

        payload = response.json()
        provider_token = payload.get("provider_token")
        if not provider_token:
            raise GmailAuthError("No provider token returned from auth session.")

        save_token({"access_token": provider_token, "retrieved_at": int(time.time())})
        return Credentials(token=provider_token, scopes=SCOPES)

    raise GmailAuthError("Authentication timed out. Please try again.")


def _decode_body(payload: Dict[str, Any]) -> str:
    """Decode plain-text content from a Gmail message payload tree.

    Args:
        payload (Dict[str, Any]): Gmail message payload node.

    Returns:
        str: Decoded body text aggregated from the payload and parts.
    """
    body_text = ""
    if payload.get("body", {}).get("data"):
        try:
            # Gmail sends message bodies as URL-safe base64 chunks.
            body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        except Exception:
            pass

    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            try:
                decoded = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                body_text += decoded
            except Exception:
                pass
        elif mime_type.startswith("multipart/"):
            # Recurse through nested MIME multiparts to gather all text nodes.
            body_text += _decode_body(part)

    return body_text


def _parse_timestamp(headers: List[Dict[str, str]]) -> Optional[datetime]:
    """Extract and parse the Date header from Gmail headers.

    Args:
        headers (List[Dict[str, str]]): Gmail header dictionaries.

    Returns:
        Optional[datetime]: Parsed datetime when available, else ``None``.
    """
    for header in headers:
        if header.get("name", "").lower() == "date":
            try:
                return parsedate_to_datetime(header["value"])
            except Exception:
                return None
    return None


def _get_header(headers: List[Dict[str, str]], name: str) -> str:
    """Return a case-insensitive header value from Gmail headers.

    Args:
        headers (List[Dict[str, str]]): Gmail header dictionaries.
        name (str): Header name to search.

    Returns:
        str: Header value when present, else an empty string.
    """
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _strip_html(html: str) -> str:
    """Strip HTML tags and normalize whitespace for text matching.

    Args:
        html (str): Message body potentially containing HTML markup.

    Returns:
        str: Plain text with collapsed spaces.
    """
    # Remove markup tags before OTP regex scanning.
    clean = re.sub(r"<[^>]+>", " ", html)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def fetch_recent_emails(n: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetch recent inbox emails formatted for OTP extraction.

    Args:
        n (Optional[int]): Maximum number of messages to fetch. When ``None``,
            the value from configuration ``email_fetch_count`` is used.

    Returns:
        List[Dict[str, Any]]: List of normalized email dictionaries containing
            ``subject``, ``body``, ``timestamp``, and ``sender`` keys.

    Raises:
        NotAuthenticatedError: If no stored token is available.
        GmailAuthError: If stored auth state is invalid.
        googleapiclient.errors.HttpError: If Gmail API requests fail.
        OSError: If underlying network or transport calls fail.
    """
    config = get_config()
    if n is None:
        n = config.get("email_fetch_count", 10)

    # Enforce freshness cutoff so stale OTP emails are ignored.
    max_age_minutes: int = config.get("otp_max_age_minutes", 10)

    creds = _load_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    # Query the most recent inbox messages from the Gmail REST API.
    results = service.users().messages().list(userId="me", maxResults=n, labelIds=["INBOX"]).execute()
    messages = results.get("messages", [])
    if not messages:
        return []

    emails: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for msg_meta in messages:
        msg = service.users().messages().get(userId="me", id=msg_meta["id"], format="full").execute()
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        subject = _get_header(headers, "Subject")
        sender = _get_header(headers, "From")
        timestamp = _parse_timestamp(headers)

        if timestamp:
            age_minutes = (now - timestamp).total_seconds() / 60
            if age_minutes > max_age_minutes:
                continue

        body = _decode_body(payload) or msg.get("snippet", "")
        body = _strip_html(body)

        emails.append(
            {
                "subject": subject,
                "body": body,
                "timestamp": timestamp.isoformat() if timestamp else "",
                "sender": sender,
            }
        )

    return emails
