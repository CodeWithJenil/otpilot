# Privacy Policy

**Project:** otpilot  
**Scope:** Personal use  
**Last updated:** February 2026

---

## Overview

`otpilot` is a personal-use CLI tool. It does not collect, transmit, or store any data on external servers. All data stays on your local machine.

---

## Data Accessed

| Data | Purpose | Stored? | Sent Externally? |
|---|---|---|---|
| Gmail emails | Search for OTP codes | No | No |
| OAuth access token | Authenticate Gmail API requests | Yes (local only) | No |
| OAuth refresh token | Renew access token silently | Yes (local only) | No |
| OTP code | Copy to clipboard | No | No |

---

## What Is NOT Collected

- Email content is never written to disk
- No analytics, telemetry, or crash reporting
- No personal information is logged
- No data is sent to any third-party service other than Google's Gmail API

---

## Google OAuth2

`otpilot` uses Google OAuth2 with a single scope:

```
https://www.googleapis.com/auth/gmail.readonly
```

This grants read-only access to your Gmail. The tool only searches for recent OTP emails — it never reads unrelated emails, sends emails, or modifies your mailbox.

OAuth tokens are stored locally in your OS config directory:

| OS | Token location |
|---|---|
| Linux | `~/.config/otpilot/` |
| macOS | `~/Library/Application Support/otpilot/` |
| Windows | `%APPDATA%\otpilot\` |

You can delete tokens at any time by running `otpilot logout` or manually deleting the config directory.

---

## Third-Party Services

The only external service contacted is the **Google Gmail API** (`gmail.googleapis.com`). This is governed by [Google's Privacy Policy](https://policies.google.com/privacy).

No other network requests are made.

---

## Revoking Access

To fully revoke `otpilot`'s access to your Gmail:

1. Go to [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
2. Find `otpilot` (or your app name from the consent screen)
3. Click **Remove Access**

Then run `otpilot logout` to clear local tokens.