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
import imaplib
import os
import re
import socket
import threading
import time
import uuid
import webbrowser
from datetime import datetime, timedelta, timezone
from email import message_from_bytes
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from otpilot.config import CONFIG_DIR, get_config
from otpilot.logger import get_logger
from otpilot.token_store import load_app_password, load_token, save_token

SCOPES: list = ["https://www.googleapis.com/auth/gmail.readonly"]
# DEFAULT_AUTH_BASE_URL = "https://otpilot-git-codex-replace-oauth-fce1ef-codewithjenils-projects.vercel.app"
# DEFAULT_AUTH_BASE_URL = "https://solid-space-barnacle-9vrvwx4grpfpp76-3000.app.github.dev/"
DEFAULT_AUTH_BASE_URL = "https://jenil-otpilot.vercel.app"
OTPILOT_AUTH_BASE_URL = os.getenv("OTPILOT_AUTH_BASE_URL", DEFAULT_AUTH_BASE_URL)

logger = get_logger(__name__)

T = TypeVar("T")


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

    creds = _build_credentials(token_payload)
    creds = _refresh_if_expired(creds)
    return creds


def _build_credentials(token_payload: Dict[str, Any]) -> Credentials:
    """Build Google OAuth2 Credentials from a stored token payload.

    Constructs a Credentials object with refresh capability when a
    refresh_token is present. Falls back to access-token-only credentials
    when no refresh token is available (legacy payloads).

    Args:
        token_payload (Dict[str, Any]): Stored token dict with keys:
            access_token (str): Current Google access token.
            refresh_token (str, optional): Google refresh token.
            expires_at (int, optional): Unix timestamp of token expiry.

    Returns:
        Credentials: google.oauth2.credentials.Credentials instance.

    Raises:
        GmailAuthError: If access_token is missing or invalid.
    """
    access_token = token_payload.get("access_token")
    if not access_token or not isinstance(access_token, str):
        raise GmailAuthError("Invalid stored token. Run `otpilot setup` to sign in again.")

    refresh_token = token_payload.get("refresh_token")
    expires_at = token_payload.get("expires_at")

    expiry = None
    if expires_at:
        expiry = datetime.fromtimestamp(int(expires_at), tz=timezone.utc)
        # Normalize to naive UTC for google-auth compatibility.
        expiry = expiry.replace(tzinfo=None)

    client_id = None
    client_secret = None
    token_uri = "https://oauth2.googleapis.com/token"

    creds_path = CONFIG_DIR / "credentials.json"
    if creds_path.exists():
        try:
            import json as _json

            raw = _json.loads(creds_path.read_text(encoding="utf-8"))
            installed = raw.get("installed") or raw.get("web") or {}
            client_id = installed.get("client_id")
            client_secret = installed.get("client_secret")
            token_uri = installed.get("token_uri", token_uri)
        except Exception:
            pass

    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
        expiry=expiry,
    )


def _refresh_if_expired(creds: Credentials) -> Credentials:
    """Refresh credentials if expired or within 5 minutes of expiry.

    Attempts a silent token refresh using google-auth's request transport.
    On success, persists the new access token and updated expiry to storage.
    On failure, raises GmailAuthError so the caller can surface a clean
    re-authentication prompt.

    Args:
        creds (Credentials): Google OAuth2 credentials to check and refresh.

    Returns:
        Credentials: Refreshed (or still-valid) credentials.

    Raises:
        GmailAuthError: If refresh fails or credentials have no refresh token.
    """
    # Use naive UTC to match google-auth's internal comparisons.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expiry = getattr(creds, "expiry", None)
    is_expired = (expiry is None) or (expiry - now < timedelta(minutes=5))

    if not is_expired:
        return creds

    if not creds.refresh_token:
        raise GmailAuthError(
            "Access token expired and no refresh token is stored. "
            "Run `otpilot setup` to re-authenticate."
        )

    try:
        import google.auth.transport.requests as google_requests

        request = google_requests.Request()
        creds.refresh(request)
    except Exception as exc:
        raise GmailAuthError(
            f"Token refresh failed: {exc}. Run `otpilot setup` to re-authenticate."
        ) from exc

    token_payload = load_token() or {}
    token_payload["access_token"] = creds.token
    if creds.expiry:
        expiry = creds.expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        token_payload["expires_at"] = int(expiry.timestamp())
    save_token(token_payload)

    return creds


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
        refresh_token = payload.get("provider_refresh_token") or payload.get("refresh_token")
        expires_in = payload.get("expires_in")
        expires_at = payload.get("expires_at")
        if not provider_token:
            raise GmailAuthError("No provider token returned from auth session.")

        token_data = {
            "access_token": provider_token,
            "retrieved_at": int(time.time()),
        }
        if refresh_token:
            token_data["refresh_token"] = refresh_token
        if expires_at:
            token_data["expires_at"] = int(expires_at)
        elif expires_in:
            token_data["expires_at"] = int(time.time()) + int(expires_in)

        save_token(token_data)
        return _build_credentials(token_data)

    raise GmailAuthError("Authentication timed out. Please try again.")


def run_oauth_flow_firebase(firebase_web_url: str = "") -> Credentials:
    """Run Firebase-hosted OAuth redirect flow and persist returned tokens.

    Args:
        firebase_web_url (str): URL of user-hosted Firebase auth page.

    Returns:
        Credentials: Google OAuth credentials built from the saved token.

    Raises:
        GmailAuthError: If the flow times out or token data is missing.
    """
    config = get_config()
    if not firebase_web_url:
        firebase_web_url = str(config.get("firebase_web_url", "")).strip()
    if not firebase_web_url:
        raise GmailAuthError(
            "Firebase auth URL is not configured. Run `otpilot setup` and provide `firebase_web_url`."
        )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    redirect_event = threading.Event()
    token_data: Dict[str, Any] = {}

    class _CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return

            query = parse_qs(parsed.query)
            access_token = query.get("access_token", [""])[0]
            refresh_token = query.get("refresh_token", [""])[0]
            expires_at_raw = query.get("expires_at", [""])[0]

            if access_token:
                token_data["access_token"] = access_token
                token_data["retrieved_at"] = int(time.time())
                if refresh_token:
                    token_data["refresh_token"] = refresh_token
                if expires_at_raw:
                    try:
                        token_data["expires_at"] = int(expires_at_raw)
                    except ValueError:
                        pass
                save_token(token_data)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Authentication successful. You can close this window.")
                redirect_event.set()
                return

            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Missing access token in callback.")

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = HTTPServer(("127.0.0.1", port), _CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    redirect_uri = f"http://localhost:{port}/callback"
    parsed_base = urlparse(firebase_web_url)
    existing_query = parse_qs(parsed_base.query, keep_blank_values=True)
    existing_query["redirect_uri"] = [redirect_uri]
    auth_url = parsed_base._replace(query=urlencode(existing_query, doseq=True)).geturl()
    webbrowser.open(auth_url)

    try:
        if not redirect_event.wait(timeout=180):
            raise GmailAuthError("Authentication timed out. Please try again.")
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)

    saved_payload = load_token()
    if not saved_payload:
        raise GmailAuthError("Authentication failed. No token was saved from Firebase redirect.")
    return _build_credentials(saved_payload)


def run_oauth_flow_credentials() -> Credentials:
    """Run Google Installed App OAuth flow using local credentials.json.

    Returns:
        Credentials: Google OAuth credentials built from authorized user data.

    Raises:
        GmailAuthError: If credentials.json is missing or OAuth flow fails.
    """
    creds_path = CONFIG_DIR / "credentials.json"
    if not creds_path.exists():
        raise GmailAuthError(
            "Missing credentials file at ~/.otpilot/credentials.json. "
            "Download it from Google Cloud Console and run setup again."
        )

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), scopes=SCOPES)
        creds = flow.run_local_server(port=0)
    except Exception as exc:
        raise GmailAuthError(f"OAuth flow failed: {exc}") from exc

    token_data: Dict[str, Any] = {
        "access_token": creds.token,
        "retrieved_at": int(time.time()),
    }
    if creds.refresh_token:
        token_data["refresh_token"] = creds.refresh_token
    if creds.expiry:
        expiry = creds.expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        token_data["expires_at"] = int(expiry.timestamp())
    save_token(token_data)
    return creds


def run_oauth_flow_for_mode(mode: str, **kwargs: Any) -> Optional[Credentials]:
    """Run the configured auth flow implementation for the selected mode.

    Args:
        mode (str): Authentication mode value from configuration.
        **kwargs (Any): Optional parameters forwarded to flow functions.

    Returns:
        Optional[Credentials]: Credentials for OAuth modes, or ``None`` for IMAP mode.

    Raises:
        GmailAuthError: If mode is unsupported or flow fails.
    """
    normalized = (mode or "").strip().lower()
    if normalized == "firebase":
        firebase_web_url = str(kwargs.get("firebase_web_url", ""))
        return run_oauth_flow_firebase(firebase_web_url=firebase_web_url)
    if normalized == "credentials":
        return run_oauth_flow_credentials()
    if normalized == "imap":
        return None
    raise GmailAuthError(f"Unsupported auth mode: {mode}")


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


def _with_retry(fn: Callable[[], T], max_attempts: int = 3, base_delay: float = 1.0) -> T:
    """Run ``fn`` with retry and exponential backoff.

    Args:
        fn: Callable to execute.
        max_attempts (int): Maximum number of attempts before giving up.
        base_delay (float): Base delay in seconds for backoff calculation.

    Returns:
        T: The return value of ``fn`` when successful.

    Raises:
        Exception: Re-raises the last encountered exception.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            logger.debug("Gmail fetch attempt %s/%s", attempt, max_attempts)
            return fn()
        except HttpError as exc:
            status = getattr(getattr(exc, "resp", None), "status", None)
            if status in (401, 403):
                logger.error("Gmail auth error (status %s).", status, exc_info=exc)
                raise
            retryable_statuses = {429, 500, 502, 503, 504}
            if status in retryable_statuses and attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning("Gmail fetch failed (%s). Retrying in %.1fs.", status, delay)
                time.sleep(delay)
                continue
            logger.error("Gmail fetch failed (status %s).", status, exc_info=exc)
            raise
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning("Network error during Gmail fetch. Retrying in %.1fs.", delay)
                time.sleep(delay)
                continue
            logger.error("Network error during Gmail fetch.", exc_info=exc)
            raise


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

    def _fetch() -> List[Dict[str, Any]]:
        creds = _load_credentials()
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)

        # Query the most recent inbox messages from the Gmail REST API.
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

    logger.debug("Fetching recent emails (limit=%s).", n)
    try:
        return _with_retry(_fetch)
    except Exception:
        logger.exception("Failed to fetch recent emails.")
        raise


def fetch_recent_emails_imap(n: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetch recent inbox emails via IMAP formatted for OTP extraction.

    Args:
        n (Optional[int]): Maximum number of messages to fetch. When ``None``,
            the value from configuration ``email_fetch_count`` is used.

    Returns:
        List[Dict[str, Any]]: List of normalized email dictionaries containing
            ``subject``, ``body``, ``timestamp``, and ``sender`` keys.

    Raises:
        NotAuthenticatedError: If no App Password is available for IMAP login.
        GmailAuthError: If IMAP login or fetch operations fail.
    """
    config = get_config()
    if n is None:
        n = config.get("email_fetch_count", 10)

    max_age_minutes: int = config.get("otp_max_age_minutes", 10)
    imap_user = str(config.get("imap_user", "")).strip()
    imap_host = str(config.get("imap_host", "imap.gmail.com")).strip()
    imap_port = int(config.get("imap_port", 993))
    app_password = load_app_password()
    if not app_password:
        raise NotAuthenticatedError("No Gmail App Password found. Run `otpilot setup` to configure IMAP auth.")

    mail: Optional[imaplib.IMAP4_SSL] = None
    logger.debug("Fetching recent emails via IMAP (limit=%s).", n)
    try:
        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        mail.login(imap_user, app_password)
        mail.select("INBOX")
        status, data = mail.search(None, "ALL")
        if status != "OK" or not data:
            return []

        ids = data[0].split()
        recent_ids = ids[-n:]
        now = datetime.now(timezone.utc)
        emails: List[Dict[str, Any]] = []

        for msg_id in reversed(recent_ids):
            fetch_status, fetch_data = mail.fetch(msg_id, "(RFC822)")
            if fetch_status != "OK" or not fetch_data:
                continue

            raw_bytes = b""
            for part in fetch_data:
                if isinstance(part, tuple) and len(part) >= 2 and isinstance(part[1], bytes):
                    raw_bytes = part[1]
                    break
            if not raw_bytes:
                continue

            msg = message_from_bytes(raw_bytes)
            subject = str(msg.get("Subject", ""))
            sender = str(msg.get("From", ""))

            timestamp = None
            date_header = msg.get("Date")
            if date_header:
                try:
                    timestamp = parsedate_to_datetime(date_header)
                    if timestamp and timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                except Exception:
                    timestamp = None

            if timestamp:
                age_minutes = (now - timestamp).total_seconds() / 60
                if age_minutes > max_age_minutes:
                    continue

            body_parts: List[str] = []
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() != "text/plain":
                        continue
                    if part.get_content_disposition() == "attachment":
                        continue
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        body_parts.append(payload.decode(charset, errors="replace"))
                    except Exception:
                        body_parts.append(payload.decode("utf-8", errors="replace"))
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    try:
                        body_parts.append(payload.decode(charset, errors="replace"))
                    except Exception:
                        body_parts.append(payload.decode("utf-8", errors="replace"))

            body = _strip_html("\n".join(body_parts).strip())
            emails.append(
                {
                    "subject": subject,
                    "body": body,
                    "timestamp": timestamp.isoformat() if timestamp else "",
                    "sender": sender,
                }
            )

        return emails
    except NotAuthenticatedError:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch recent emails via IMAP.")
        raise GmailAuthError(f"IMAP fetch failed: {exc}") from exc
    finally:
        if mail is not None:
            try:
                mail.close()
            except Exception:
                pass
            try:
                mail.logout()
            except Exception:
                pass


def get_fetch_function() -> Callable[..., List[Dict[str, Any]]]:
    """Select the active email fetch implementation based on auth mode.

    Returns:
        Callable[..., List[Dict[str, Any]]]: Fetch function for current auth mode.
    """
    mode = str(get_config().get("auth_mode", "firebase")).strip().lower()
    if mode == "imap":
        return fetch_recent_emails_imap
    return fetch_recent_emails
