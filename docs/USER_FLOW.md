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
  Downloading otpilot-2.3.2-py3-none-any.whl
Installing collected packages: otpilot
Successfully installed otpilot-2.3.2
```

> **Linux users**: Also install clipboard support:
> ```bash
> sudo apt install xclip
> ```

---

## 2. Run `otpilot setup`

```bash
otpilot setup
```

### Step 2a: Welcome Banner

```
╭──────────────────────────────────────╮
│   ✈  OTPilot Setup  ✈              │
│   Background OTP copier for Gmail    │
╰──────────────────────────────────────╯
```

### Step 2b: Google Sign-In

```
Step 1: Google Account Sign-In
  Opening your browser for Gmail authorization...
```

**What happens:**
- Your default browser opens to the Google sign-in page
- You select your Gmail account and click "Allow"
- Back in terminal:

```
  ✓ Authentication successful!
```

If a token already exists, setup lets you keep it or re-authenticate.

### Step 2c: Hotkey Configuration

```
Step 2: Configure Hotkey
  Press your desired hotkey combination now...
  (Must include at least one modifier: Ctrl, Alt, Shift, or Cmd)
```

**What you do:**
- Press your desired key combination (e.g. `Ctrl+Shift+O`)
- Setup confirms the captured hotkey
- In environments that cannot capture keys, OTPilot falls back to default `ctrl+shift+o`

### Step 2d: Preferences

```
Step 3: Preferences
```

Setup prompts for:
- Notification on copy
- Auto-paste after copy
- Max OTP email age (minutes)
- Number of recent emails to scan
- Auto-start on login

### Step 2e: Setup Complete

```
Setup complete!
Run otpilot start to launch OTPilot in the background.
```

---

## 3. Start OTPilot

```bash
otpilot start
```

**What happens:**
- OTPilot starts in the background
- A tray icon appears (if supported on your platform)
- Global hotkey listener starts
- Optional background update check runs

---

## 4. Daily Use — Fetching OTPs

### Option A: Hotkey

1. Receive an OTP email
2. Press your configured hotkey
3. OTPilot fetches recent inbox emails and extracts an OTP
4. OTP is copied to clipboard
5. Optional auto-paste and notification are triggered

### Option B: CLI Fetch

```bash
otpilot fetch
```

This runs the same fetch/extract/copy flow once without waiting for a hotkey press.

### When No OTP Is Found

Notification:

```
OTPilot
No OTP found in recent emails.
```

**Common reasons:**
- The OTP email has not arrived yet
- The email is older than `otp_max_age_minutes`
- The email does not contain OTP-related context near the code

---

## 5. System Tray

While running, OTPilot lives in your system tray / menu bar:

- **macOS**: Menu bar (top right)
- **Windows**: System tray (bottom right, near clock)
- **Linux**: Depends on your desktop environment

### Tray Menu

| Menu Item          | Action                                        |
| ------------------ | --------------------------------------------- |
| **OTPilot**        | Label (not clickable)                         |
| **Settings**       | Opens a terminal to re-run `otpilot setup`    |
| **Re-authenticate**| Re-runs the OAuth flow                         |
| **Quit**           | Stops OTPilot                                  |

### CLI Reference

| Command        | Purpose                                  |
| -------------- | ---------------------------------------- |
| `otpilot stop` | Stop the background process and clean PID |

---

## 6. Changing Settings

### Option A: Via Tray Menu

Click **Settings** in the tray menu.

### Option B: Via CLI

```bash
otpilot setup
```

### Option C: Edit Config Directly

Open `~/.otpilot/config.json` and update fields like `hotkey`, `auto_paste`, `otp_max_age_minutes`, and `email_fetch_count`.

Restart OTPilot for changes to take effect.

---

## 7. Re-authenticating

If your token expires or you want to switch accounts:

### Option A: Via Tray Menu

Click **Re-authenticate**.

### Option B: Via CLI

```bash
otpilot setup
```
