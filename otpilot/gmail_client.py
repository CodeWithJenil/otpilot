"""Gmail API client for OTPilot.

Handles Supabase-powered Google OAuth authentication and Gmail fetching.
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
DEFAULT_AUTH_BASE_URL = "https://otpilot-git-codex-replace-oauth-fce1ef-codewithjenils-projects.vercel.app"
OTPILOT_AUTH_BASE_URL = os.getenv("OTPILOT_AUTH_BASE_URL", DEFAULT_AUTH_BASE_URL)


class NotAuthenticatedError(Exception):
    def __init__(self, message: str = "Not authenticated. Run `otpilot setup` to sign in.") -> None:
        super().__init__(message)


class GmailAuthError(Exception):
    def __init__(self, message: str = "Authentication failed. Run `otpilot setup` to re-authenticate.") -> None:
        super().__init__(message)


def _load_credentials() -> Credentials:
    token_payload = load_token()
    if not token_payload:
        raise NotAuthenticatedError()

    provider_token = token_payload.get("access_token")
    if not provider_token or not isinstance(provider_token, str):
        raise GmailAuthError("Invalid stored token. Run `otpilot setup` to sign in again.")

    return Credentials(token=provider_token, scopes=SCOPES)


def _normalize_auth_base_url(auth_base_url: str) -> str:
    """Return the deployment base URL without auth route suffixes."""
    normalized = auth_base_url.rstrip("/")
    for suffix in ("/api/auth/callback", "/api/auth/start", "/api/auth/session"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def run_oauth_flow(auth_base_url: str = OTPILOT_AUTH_BASE_URL) -> Credentials:
    """Run Supabase Google OAuth and persist provider token locally."""
    session_key = uuid.uuid4().hex
    base_url = _normalize_auth_base_url(auth_base_url)
    auth_url = f"{base_url}/api/auth/start?{urlencode({'session_key': session_key})}"
    webbrowser.open(auth_url)

    session_url = f"{base_url}/api/auth/session?{urlencode({'session_key': session_key})}"

    start = time.time()
    while time.time() - start < 180:
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
    body_text = ""
    if payload.get("body", {}).get("data"):
        try:
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
            body_text += _decode_body(part)

    return body_text


def _parse_timestamp(headers: List[Dict[str, str]]) -> Optional[datetime]:
    for header in headers:
        if header.get("name", "").lower() == "date":
            try:
                return parsedate_to_datetime(header["value"])
            except Exception:
                return None
    return None


def _get_header(headers: List[Dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _strip_html(html: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", html)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def fetch_recent_emails(n: Optional[int] = None) -> List[Dict[str, Any]]:
    config = get_config()
    if n is None:
        n = config.get("email_fetch_count", 10)

    max_age_minutes: int = config.get("otp_max_age_minutes", 10)

    creds = _load_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

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

        emails.append({
            "subject": subject,
            "body": body,
            "timestamp": timestamp.isoformat() if timestamp else "",
            "sender": sender,
        })

    return emails
