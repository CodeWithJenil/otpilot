# Privacy Policy

**Project:** OTPilot  
**Scope:** Personal use  
**Last updated:** March 29, 2026

---

## Overview

`otpilot` is a local CLI utility. It does not operate a telemetry backend and does not upload email content to OTPilot-owned servers.

---

## Data Accessed

| Data | Purpose | Stored? | Sent Externally? |
|---|---|---|---|
| Gmail emails (recent inbox messages) | Search for OTP codes | No | Yes, only to Google Gmail API requests made by your client |
| OAuth access token | Authenticate Gmail API requests | Yes (local only) | Yes, to Google during API calls |
| OAuth refresh token | Renew access silently | Yes (local only) | Yes, to Google token endpoints as part of OAuth |
| OTP code | Copy to clipboard / optional auto-paste | No | No |

---

## What Is NOT Collected

- OTPilot does not persist email bodies locally for analytics
- No built-in telemetry, analytics, or crash reporting
- No OTPilot-controlled data warehouse for user mail data

---

## Google OAuth Scope

`otpilot` uses Google OAuth with:

```
https://www.googleapis.com/auth/gmail.readonly
```

This grants read-only Gmail access. OTPilot cannot send, delete, or modify your emails.

---

## Local Storage

OTPilot stores runtime state locally at:

- `~/.otpilot/config.json`
- `~/.otpilot/history.json`
- Token storage: system keyring when available (`service=otpilot`), with fallback to `~/.otpilot/token.json`

You can remove local state by deleting these files and revoking Google access.

---

## Network Calls

OTPilot may contact:

- Google Gmail API (email listing and message retrieval)
- Google OAuth/token services (through OAuth flow)
- Supabase-backed auth endpoint for setup/re-auth (`/api/auth/start`, `/api/auth/session`)
- PyPI (`pypi.org`) when update checks are enabled

---

## Revoking Access

To revoke Gmail access:

1. Go to [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
2. Find your OTPilot OAuth app
3. Click **Remove Access**

Then delete local token/config files if needed.
