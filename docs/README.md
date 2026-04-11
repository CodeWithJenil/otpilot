# OTPilot

> Press a hotkey. Your OTP is already copied.

```bash
pip install otpilot
```

---

<p align="center">
  <strong>✈ OTPilot v2.3</strong>
</p>

<p align="center">
  <em>Background utility that fetches OTPs from Gmail and copies them to your clipboard with a single hotkey press.</em>
</p>

<p align="center">
  <a href="https://github.com/codewithjenil/otpilot">GitHub</a> •
  <a href="#installation">Install</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## How It Works

1. OTPilot sits in your system tray with no background polling.
2. Press your hotkey or run `otpilot fetch` to scan recent Gmail messages.
3. OTP is copied to clipboard and optionally auto-pasted.

---

## Installation

```bash
pip install otpilot
```

**Requirements**

- Python 3.10+
- A Gmail account

Linux users must install clipboard support:

```bash
sudo apt install xclip  # Debian/Ubuntu
```

---

## Quickstart

### 1. Run Setup

```bash
otpilot setup
```

The wizard will:
- Let you choose one of 3 authentication modes (Firebase, credentials.json, or IMAP App Password)
- Let you configure hotkey, notifications, and scan preferences
- Save everything locally

### 2. Start OTPilot

```bash
otpilot start
```

OTPilot runs in the background with a system tray icon when supported.

### 3. Daily Use

1. Receive an OTP email
2. Press your hotkey (default: `Ctrl+Shift+O`)
3. Paste

---

## Authentication Modes

OTPilot supports 3 authentication modes. Choose one during `otpilot setup`.

## Setup Responsibilities (You vs End Users)

Use this quick split to know what *you* (OTPilot deployer/maintainer) must set up once, versus what each *end user* must do locally.

### If you provide Firebase hosted auth

**You (maintainer) set up once:**
- Build/deploy the web auth page (for example `https://jenil-otpilot.vercel.app/auth`)
- Configure Firebase project + Google sign-in
- Add authorized domains in Firebase Auth (`jenil-otpilot.vercel.app`, `localhost`)
- Set web env vars (`NEXT_PUBLIC_FIREBASE_API_KEY`, `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`, `NEXT_PUBLIC_FIREBASE_PROJECT_ID`)
- Ensure linked Google Cloud project has Gmail API enabled and consent screen configured for `gmail.readonly`

**Each user sets up locally:**
- Install OTPilot (`pip install otpilot`)
- Run `otpilot setup`
- Choose **[1] Firebase Auth**
- Paste your hosted auth page URL when prompted
- Complete Google sign-in in browser

### If users bring their own OAuth client (`credentials.json`)

**You (maintainer) set up:**
- Nothing required for hosted auth

**Each user sets up locally:**
- Create their own Google Cloud project + OAuth client
- Enable Gmail API on that project
- Download `credentials.json` and place at `~/.otpilot/credentials.json`
- Run `otpilot setup` and choose **[2] My own credentials.json**

### If users use Gmail App Password (IMAP)

**You (maintainer) set up:**
- Nothing required for hosted auth

**Each user sets up locally:**
- Enable 2-Step Verification on Gmail account
- Generate Gmail App Password at `https://myaccount.google.com/apppasswords`
- Run `otpilot setup` and choose **[3] Gmail App Password**
- Enter Gmail address + app password

---

### Mode 1: Firebase Auth (Recommended)

Use this when you have a hosted Firebase web auth page that performs Google sign-in and redirects back to OTPilot.

**You need:**
- A Firebase web page URL that:
  - Requests Gmail readonly scope (`https://www.googleapis.com/auth/gmail.readonly`)
  - Retrieves `accessToken` and `refreshToken`
  - Redirects to the provided local `redirect_uri` with query params:
    - `access_token`
    - `refresh_token` (if available)
    - `expires_at` (unix timestamp, if available)

**Setup flow:**
1. Run `otpilot setup`
2. Choose **[1] Firebase Auth**
3. Enter your Firebase auth page URL when prompted
4. Complete browser sign-in

### Mode 2: My own `credentials.json`

Use this when you want your own Google Cloud OAuth client.

**You need:**
- A Google Cloud project with Gmail API enabled
- OAuth client credentials downloaded as `credentials.json`
- File placed at: `~/.otpilot/credentials.json`

**Setup flow:**
1. Run `otpilot setup`
2. Choose **[2] My own credentials.json**
3. Confirm once `~/.otpilot/credentials.json` exists
4. Complete browser sign-in

### Mode 3: Gmail App Password (IMAP)

Use this when you prefer no OAuth flow inside OTPilot.

**You need:**
- A Gmail account with 2-Step Verification enabled
- A Gmail App Password from:
  - https://myaccount.google.com/apppasswords

**Setup flow:**
1. Run `otpilot setup`
2. Choose **[3] Gmail App Password**
3. Enter your Gmail address
4. Enter your App Password

---

## CLI Commands

| Command                  | Description                                 |
| ------------------------ | ------------------------------------------- |
| `otpilot setup`          | Run or re-run the interactive setup wizard  |
| `otpilot start`          | Start the background service                |
| `otpilot stop`           | Stop the background service                 |
| `otpilot fetch`          | Trigger a one-time OTP fetch from the CLI   |
| `otpilot history`        | Show recent OTP history                     |
| `otpilot history --clear`| Clear OTP history                           |
| `otpilot logs`           | Tail the OTPilot log file                   |
| `otpilot status`         | Show auth state, hotkey, and config         |
| `otpilot hotkey`         | View or reconfigure the global hotkey       |
| `otpilot logout`         | Clear stored auth token                     |
| `otpilot update`         | Check PyPI for updates and upgrade          |
| `otpilot version`        | Print the installed version                 |

---

## Configuration

OTPilot stores its configuration at `~/.otpilot/config.json`:

```json
{
  "auth_mode": "firebase",
  "hotkey": "ctrl+shift+o",
  "notify_on_copy": true,
  "otp_max_age_minutes": 10,
  "email_fetch_count": 10,
  "otp_history_count": 10,
  "auto_paste": false,
  "auto_start_on_boot": false,
  "notification_sound": false,
  "mask_otp_in_notification": true,
  "check_updates_on_start": true,
  "setup_complete": true,
  "firebase_web_url": "",
  "imap_user": "",
  "imap_host": "imap.gmail.com",
  "imap_port": 993
}
```

| Field                      | Type   | Default        | Description                                       |
| -------------------------- | ------ | -------------- | ------------------------------------------------- |
| `auth_mode`                | string | `firebase`     | Auth backend: `firebase`, `credentials`, or `imap` |
| `hotkey`                   | string | `ctrl+shift+o` | Global hotkey combination                         |
| `notify_on_copy`           | bool   | `true`         | Show desktop notification when OTP is copied      |
| `otp_max_age_minutes`      | int    | `10`           | Ignore emails older than this (minutes)           |
| `email_fetch_count`        | int    | `10`           | Number of recent emails to scan (max 50)          |
| `otp_history_count`        | int    | `10`           | Number of OTP history entries to keep (max 50)    |
| `auto_paste`               | bool   | `false`        | Auto-paste OTP after copying                      |
| `auto_start_on_boot`       | bool   | `false`        | Launch OTPilot on login                           |
| `notification_sound`       | bool   | `false`        | Play a sound with notifications                   |
| `mask_otp_in_notification` | bool   | `true`         | Mask middle digits in notification (e.g. 84••93)  |
| `check_updates_on_start`   | bool   | `true`         | Check PyPI for a newer version on startup         |
| `setup_complete`           | bool   | `false`        | Indicates setup has been completed                |
| `firebase_web_url`         | string | `""`           | URL of your hosted Firebase auth page             |
| `imap_user`                | string | `""`           | Gmail address used for IMAP mode                  |
| `imap_host`                | string | `imap.gmail.com` | IMAP host for app-password mode                |
| `imap_port`                | int    | `993`          | IMAP SSL port                                     |

### Files Stored Locally

| Path                       | Purpose                               |
| -------------------------- | ------------------------------------- |
| `~/.otpilot/config.json`   | Hotkey and runtime settings           |
| `~/.otpilot/history.json`  | OTP history entries                   |
| `~/.otpilot/otpilot.log`   | Background service log                |
| `~/.otpilot/otpilot.pid`   | PID of the running background process |
| System keyring (`otpilot`) | Preferred OAuth token storage         |
| `~/.otpilot/token.json`    | Fallback token storage                |
| `~/.otpilot/app_password.txt` | Fallback IMAP app-password storage |

---

## OTP History

Show recent entries:

```bash
otpilot history
```

Show only 3 entries:

```bash
otpilot history --count 3
```

Clear history:

```bash
otpilot history --clear
```

---

## Platform Support

| Platform | Status | Notes                      |
| -------- | ------ | -------------------------- |
| macOS    | ✅     | Full support               |
| Windows  | ✅     | Full support               |
| Linux    | ✅     | Requires `xclip` or `xsel` |

---

## How OTP Extraction Works

OTPilot scans the subject line and body of your recent emails for:

- 4–8 digit standalone numbers near context words like OTP, code, verify, one-time, passcode, authentication, 2FA
- Only emails within `otp_max_age_minutes` are considered
- Subject line matches are prioritized over body matches

---

## Security & Privacy

- Read-only Gmail access
- On-demand only, no background polling
- Local storage for tokens and configuration
- No telemetry or analytics

---

## Troubleshooting

| Issue                         | Solution                                                        |
| ----------------------------- | --------------------------------------------------------------- |
| "Not authenticated" error     | Run `otpilot setup` to re-authenticate                          |
| "Access token expired..."     | Use Firebase/credentials mode with refresh token, or switch to IMAP App Password in setup |
| No OTP found                  | Check `otp_max_age_minutes` — the email might be too old        |
| Clipboard not working (Linux) | Install `xclip`: `sudo apt install xclip`                       |
| Hotkey not working            | Run `otpilot hotkey` to reconfigure                             |
| Tray icon not visible         | Check your system tray / menu bar settings                      |
| Stop doesn’t work             | Run `otpilot stop` again or delete `~/.otpilot/otpilot.pid`     |
| Log file empty                | Start OTPilot and run `otpilot logs` after a fetch              |

---

## Contributing

Contributions are welcome. See `docs/CONTRIBUTING.md` for dev setup and code standards.

---

## License

MIT License.
