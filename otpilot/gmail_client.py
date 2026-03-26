"""Gmail API client for OTPilot.

Handles OAuth2 authentication and email fetching via the Gmail API.
Emails are fetched on-demand only — never polled in the background.
"""

import base64
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from otpilot.config import TOKEN_FILE, get_config
from otpilot.credentials import CREDENTIALS_FILE, SCOPES, credentials_exist, validate_credentials_file


class NotAuthenticatedError(Exception):
    """Raised when no valid OAuth token is available."""

    def __init__(self, message: str = "Not authenticated. Run `otpilot setup` to sign in.") -> None:
        super().__init__(message)


class GmailAuthError(Exception):
    """Raised when authentication fails or token cannot be refreshed."""

    def __init__(self, message: str = "Authentication failed. Run `otpilot setup` to re-authenticate.") -> None:
        super().__init__(message)


class CredentialsNotFoundError(Exception):
    """Raised when the user-provided credentials.json file is missing or invalid."""

    def __init__(self, message: str = "credentials.json not found. Run `otpilot setup` to provide your credentials file.") -> None:
        super().__init__(message)


def _load_credentials() -> Credentials:
    """Load OAuth2 credentials from the stored token file.

    Returns:
        Valid ``Credentials`` instance.

    Raises:
        CredentialsNotFoundError: If credentials.json is missing or invalid.
        NotAuthenticatedError: If no token file exists.
        GmailAuthError: If the token cannot be refreshed.
    """
    if not credentials_exist():
        raise CredentialsNotFoundError()

    if not validate_credentials_file(CREDENTIALS_FILE):
        raise CredentialsNotFoundError(
            "Invalid credentials file. Re-run `otpilot setup` with a valid credentials.json."
        )

    if not TOKEN_FILE.exists():
        raise NotAuthenticatedError()

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Persist the refreshed token
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        except RefreshError as exc:
            raise GmailAuthError(
                "Token expired and could not be refreshed. Run `otpilot setup` to re-authenticate."
            ) from exc

    if not creds.valid:
        raise GmailAuthError()

    return creds


def run_oauth_flow() -> Credentials:
    """Run the interactive OAuth2 consent flow in the user's browser.

    Loads client secrets from ``~/.otpilot/credentials.json`` and saves
    the resulting token to ``~/.otpilot/token.json``.

    Returns:
        Authenticated ``Credentials`` instance.

    Raises:
        CredentialsNotFoundError: If credentials.json is missing or invalid.
    """
    from otpilot.config import CONFIG_DIR  # avoid circular at module level

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not credentials_exist():
        raise CredentialsNotFoundError()

    if not validate_credentials_file(CREDENTIALS_FILE):
        raise CredentialsNotFoundError(
            "Invalid credentials file. Re-run `otpilot setup` with a valid credentials.json."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _decode_body(payload: Dict[str, Any]) -> str:
    """Recursively extract and decode the plain-text body from a Gmail message payload.

    Args:
        payload: The Gmail API message payload dict.

    Returns:
        Decoded body text, or an empty string if not found.
    """
    body_text = ""

    # Direct body data
    if payload.get("body", {}).get("data"):
        try:
            body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        except Exception:
            pass

    # Recurse into parts (multipart messages)
    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            try:
                decoded = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                body_text += decoded
            except Exception:
                pass
        elif mime_type.startswith("multipart/"):
            body_text += _decode_body(part)

    return body_text


def _parse_timestamp(headers: List[Dict[str, str]]) -> Optional[datetime]:
    """Extract and parse the Date header from Gmail message headers.

    Args:
        headers: List of header dicts with 'name' and 'value' keys.

    Returns:
        A timezone-aware datetime, or None if parsing fails.
    """
    for header in headers:
        if header.get("name", "").lower() == "date":
            try:
                return parsedate_to_datetime(header["value"])
            except Exception:
                return None
    return None


def _get_header(headers: List[Dict[str, str]], name: str) -> str:
    """Get a specific header value by name.

    Args:
        headers: List of header dicts.
        name: Header name to look up (case-insensitive).

    Returns:
        The header value, or an empty string if not found.
    """
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _strip_html(html: str) -> str:
    """Remove HTML tags from a string, keeping only text content.

    Args:
        html: Raw HTML string.

    Returns:
        Plain text with HTML tags removed.
    """
    clean = re.sub(r"<[^>]+>", " ", html)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def fetch_recent_emails(n: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetch the most recent emails from the user's Gmail inbox.

    Only retrieves emails within the configured ``otp_max_age_minutes`` window.

    Args:
        n: Number of emails to fetch. Defaults to the ``email_fetch_count``
           value in the config file.

    Returns:
        A list of dicts, each with keys: ``subject``, ``body``, ``timestamp``,
        ``sender``.

    Raises:
        NotAuthenticatedError: If no token is available.
        GmailAuthError: If the token is invalid/expired.
    """
    config = get_config()
    if n is None:
        n = config.get("email_fetch_count", 10)

    max_age_minutes: int = config.get("otp_max_age_minutes", 10)

    creds = _load_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    # Fetch message IDs
    results = (
        service.users()
        .messages()
        .list(userId="me", maxResults=n, labelIds=["INBOX"])
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return []

    emails: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for msg_meta in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_meta["id"], format="full")
            .execute()
        )

        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        subject = _get_header(headers, "Subject")
        sender = _get_header(headers, "From")
        timestamp = _parse_timestamp(headers)

        # Filter by max age
        if timestamp:
            age_minutes = (now - timestamp).total_seconds() / 60
            if age_minutes > max_age_minutes:
                continue

        # Decode body
        body = _decode_body(payload)
        if not body:
            # Fallback: try snippet
            body = msg.get("snippet", "")

        # Strip any residual HTML
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
