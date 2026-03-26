# User Flow — From Install to Daily Use

This document walks through the complete OTPilot user journey, from first install to daily OTP fetching.

---

## 1. Install OTPilot

```bash
pip install otpilot
```

**What you see:**
```
Collecting otpilot
  Downloading otpilot-2.0.0-py3-none-any.whl
Installing collected packages: otpilot
Successfully installed otpilot-2.0.0
```

> **Linux users**: Also install clipboard support:
> ```bash
> sudo apt install xclip
> ```

---

## 2. Get Your Google Cloud Credentials

Before running setup, you need a `credentials.json` file from the Google Cloud Console. This is a one-time process that takes ~5 minutes.

### Quick Steps

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project → name it `OTPilot`
3. Go to **APIs & Services → Library** → search **Gmail API** → click **Enable**
4. Go to **APIs & Services → OAuth consent screen** → select **External** → create
   - Fill in app name, support email, developer email
   - Add scope: `gmail.readonly`
   - Add yourself as a test user
5. Go to **APIs & Services → Credentials** → **Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Name: `OTPilot Desktop`
6. Click **Download JSON** — save this file

> For the full walkthrough with every click, see [SETUP.md](SETUP.md).

---

## 3. Run `otpilot setup`

```bash
otpilot setup
```

### Step 3a: Welcome Banner

```
╭──────────────────────────────────────╮
│   ✈  OTPilot Setup  ✈              │
│   Background OTP copier for Gmail    │
╰──────────────────────────────────────╯

Welcome to OTPilot setup!
This wizard will help you import your Google credentials, authenticate,
and configure your hotkey.
```

### Step 3b: Import Credentials

```
Step 1: Google Cloud Credentials

  To use OTPilot, you need a credentials.json file from
  the Google Cloud Console. This takes about 5 minutes.

  Have you already downloaded your credentials.json? [y/N]: y

  Enter the path to your credentials.json file: ~/Downloads/client_secret_xxxx.json

  ✓ Credentials saved to ~/.otpilot/credentials.json
  Your credentials never leave your machine.
```

**If you don't have the file yet**, enter `N` and you'll see a quick reference guide:

```
╭─── How to get credentials.json ───╮
│                                     │
│  1. Go to console.cloud.google.com  │
│  2. Create a new project            │
│  3. Enable the Gmail API            │
│  4. Create OAuth 2.0 Client ID      │
│  5. Download the JSON file          │
│  6. Run otpilot setup again         │
│                                     │
╰─────────────────────────────────────╯
```

**If credentials already exist** (re-running setup):

```
  A credentials file was found at ~/.otpilot/credentials.json
  Replace it? [y/N]: N
  ✓ Using existing credentials.
```

### Step 3c: Google Sign-In

```
Step 2: Google Account Sign-In
  Opening your browser for Gmail authorization...
```

**What happens:**
- Your default browser opens to the Google sign-in page
- You select your Gmail account and click "Allow"
- The browser shows "The authentication flow has completed"
- Back in the terminal:

```
  ✓ Authentication successful!
```

### Step 3d: Hotkey Configuration

```
Step 3: Configure Hotkey
  Press your desired hotkey combination now...
  (Must include at least one modifier: Ctrl, Alt, Shift, or Cmd)
```

**What you do:**
- Press your desired key combination (e.g. `Ctrl+Shift+O`)
- The terminal confirms:

```
  ✓ Hotkey set to: ctrl+shift+o
```

### Step 3e: Setup Complete

```
╭─────── Summary ───────╮
│                        │
│  Setup complete!       │
│                        │
│  Hotkey:  ctrl+shift+o │
│  Credentials: ~/.otpilot/credentials.json │
│  Token:   ~/.otpilot/token.json │
│  Config:  ~/.otpilot/config.json │
│                        │
│  Run otpilot start to  │
│  launch the service.   │
╰────────────────────────╯

Start OTPilot now? [Y/n]:
```

Press `Y` or `Enter` to start immediately.

---

## 4. Daily Use — Fetching OTPs

### The Flow

1. **You receive an OTP email** — e.g. "Your verification code is 847293"
2. **Press your hotkey** — e.g. `Ctrl+Shift+O`
3. **OTPilot fetches your last 10 emails** from Gmail
4. **Extracts the OTP** (4–8 digit code near keywords like "code", "OTP", "verify")
5. **Copies it to your clipboard**
6. **Shows a notification:**

```
OTPilot
OTP copied: 84••93
```

7. **Paste it** — `Ctrl+V` / `Cmd+V` wherever you need it

### When No OTP Is Found

If there's no OTP in your recent emails:

```
OTPilot
No OTP found in recent emails.
```

**Common reasons:**
- The OTP email hasn't arrived yet — wait a few seconds and try again
- The email is older than `otp_max_age_minutes` (default: 10 minutes)
- The email doesn't contain OTP-related keywords

---

## 5. System Tray

While running, OTPilot lives in your system tray / menu bar:

- **macOS**: Menu bar (top right)
- **Windows**: System tray (bottom right, near clock)
- **Linux**: Depends on your desktop environment

### Tray Menu

Right-click (or click on macOS) the OTPilot icon to see:

| Menu Item          | Action                                        |
| ------------------ | --------------------------------------------- |
| **OTPilot**        | Label (not clickable)                         |
| **Settings**       | Opens a terminal to re-run `otpilot setup`    |
| **Re-authenticate**| Re-runs the OAuth flow without full setup     |
| **Quit**           | Stops OTPilot                                 |

---

## 6. Changing Settings

### Option A: Via Tray Menu

Click **Settings** in the tray menu — a terminal opens with `otpilot setup`.

### Option B: Edit Config Directly

Open `~/.otpilot/config.json` in any text editor:

```json
{
  "hotkey": "ctrl+shift+o",
  "notify_on_copy": true,
  "otp_max_age_minutes": 10,
  "email_fetch_count": 10
}
```

Save the file and restart OTPilot for changes to take effect.

### Option C: Re-run Setup

```bash
otpilot setup
```

---

## 7. Re-authenticating

If your Google token expires or you want to switch accounts:

### Option A: Via Tray Menu

Click **Re-authenticate** — your browser opens for sign-in.

### Option B: Via CLI

```bash
otpilot setup
```

When prompted "Re-authenticate?", select Yes.

### Option C: Delete Token

```bash
rm ~/.otpilot/token.json
otpilot setup
```

---

## 8. Checking Status

```bash
otpilot status
```

**Output:**
```
OTPilot Status
  Version:        2.0.0
  Authenticated:  Yes
  Credentials:    Yes
  Hotkey:         ctrl+shift+o
  Notifications:  On
  Max OTP age:    10 min
  Fetch count:    10 emails
  Config path:    /Users/you/.otpilot/config.json
```

---

## 9. Uninstalling

### Remove the package

```bash
pip uninstall otpilot
```

### Remove configuration, credentials, and tokens

```bash
rm -rf ~/.otpilot
```

### Revoke Google access (optional)

1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
2. Find "OTPilot"
3. Click **Remove Access**

### Delete the Google Cloud project (optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your OTPilot project
3. Go to **Settings** → **Shut down**

---

## Quick Reference

| Action                    | Command / Shortcut              |
| ------------------------- | ------------------------------- |
| Install                   | `pip install otpilot`           |
| Get credentials           | [SETUP.md](SETUP.md)           |
| First-time setup          | `otpilot setup`                 |
| Start service             | `otpilot start`                 |
| Fetch OTP                 | Press your hotkey               |
| Check status              | `otpilot status`                |
| Change settings           | `otpilot setup` or edit config  |
| Re-authenticate           | Tray menu → Re-authenticate     |
| Quit                      | Tray menu → Quit                |
| Uninstall                 | `pip uninstall otpilot`         |
