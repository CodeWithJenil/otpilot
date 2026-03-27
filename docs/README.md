![OTPilot Demo](assets/demo.gif)

# OTPilot

> Press a hotkey. Your OTP is already copied.
```bash
pip install otpilot
```

---

<p align="center">
  <strong>✈ OTPilot v2.0</strong>
</p>

<p align="center">
  <em>The new era of private OTP fetching. Background utility that copies OTPs from Gmail to your clipboard with a single hotkey.</em>
</p>

<p align="center">
  <a href="https://github.com/codewithjenil/otpilot">GitHub</a> •
  <a href="#installation">Install</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="SETUP.md">OAuth Setup</a> •
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## How It Works

1. **OTPilot sits silently in your system tray** — no windows, no polling, zero CPU usage.
2. **Press your hotkey** (e.g. `Ctrl+Shift+O`) — OTPilot fetches your last 10 emails from Gmail and extracts the OTP.
3. **OTP is copied to your clipboard** — just paste it. A desktop notification confirms the action.

## Installation

```bash
pip install otpilot
```

### Requirements

- **Python 3.8+**
- **Gmail account**
- **Google Cloud project** with Gmail API enabled (free — [setup guide](SETUP.md))
- **OS**: macOS, Windows, or Linux

> **Linux users**: Make sure `xclip` or `xsel` is installed for clipboard support.
> ```bash
> sudo apt install xclip  # Debian/Ubuntu
> ```

## Quickstart

### 1. Get Your Credentials

Follow the steps above (or the [full guide](SETUP.md)) to download your `credentials.json` file.

### 2. Run Setup

```bash
otpilot setup
```

The wizard will:
- Ask for the path to your `credentials.json` file
- Open your browser for Google sign-in (one-time authorization)
- Let you set your preferred hotkey
- Save your configuration

### 3. Start OTPilot

```bash
otpilot start
```

OTPilot runs in the background with a system tray icon. Press your hotkey whenever you need an OTP.

### 4. Daily Use

1. Receive an OTP email in Gmail
2. Press your hotkey (default: `Ctrl+Shift+O`)
3. Paste the OTP — done!

## Getting Your credentials.json

Before using OTPilot, you need to download a `credentials.json` file from Google Cloud Console. This is a one-time, ~5 minute process.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Enable the **Gmail API**
4. Go to **APIs & Services → Credentials**
5. Create an **OAuth 2.0 Client ID** (Application type: **Desktop app**)
6. Click **Download JSON** to save the `credentials.json` file

> **Your credentials never leave your machine.** The file is stored locally at `~/.otpilot/credentials.json`.

For detailed, step-by-step instructions with screenshots, see [**SETUP.md**](SETUP.md).

## CLI Commands

| Command            | Description                              |
| ------------------ | ---------------------------------------- |
| `otpilot setup`    | Run or re-run the interactive setup      |
| `otpilot start`    | Start the background service             |
| `otpilot status`   | Show auth state, hotkey, and config path |
| `otpilot version`  | Print the version number                 |

## Configuration

OTPilot stores its configuration at `~/.otpilot/config.json`:

```json
{
  "hotkey": "ctrl+shift+o",
  "notify_on_copy": true,
  "otp_max_age_minutes": 10,
  "email_fetch_count": 10
}
```

| Field                 | Type   | Default          | Description                                    |
| --------------------- | ------ | ---------------- | ---------------------------------------------- |
| `hotkey`              | string | `ctrl+shift+o`   | Global hotkey combination                      |
| `notify_on_copy`      | bool   | `true`           | Show desktop notification when OTP is copied   |
| `otp_max_age_minutes` | int    | `10`             | Ignore emails older than this (minutes)        |
| `email_fetch_count`   | int    | `10`             | Number of recent emails to scan                |

### Files Stored Locally

| File                             | Purpose                              |
| -------------------------------- | ------------------------------------ |
| `~/.otpilot/config.json`        | Your hotkey and settings             |
| `~/.otpilot/credentials.json`   | Your Google OAuth credentials        |
| `~/.otpilot/token.json`         | OAuth session token (auto-generated) |

## Platform Support

| Platform | Status | Notes                                  |
| -------- | ------ | -------------------------------------- |
| macOS    | ✅     | Full support                           |
| Windows  | ✅     | Full support                           |
| Linux    | ✅     | Requires `xclip`/`xsel` for clipboard  |

## How OTP Extraction Works

OTPilot scans the subject line and body of your recent emails for:

- **4–8 digit standalone numbers** near context words like *OTP*, *code*, *verify*, *verification*, *one-time*, *passcode*, *authentication*
- Only emails within the configured time window are considered
- If multiple OTPs are found, the most recent one wins

## Security & Privacy

- **Your credentials stay local**: `credentials.json` is stored on your machine at `~/.otpilot/` and is never uploaded anywhere.
- **Read-only access**: OTPilot only reads your emails — it cannot send, delete, or modify anything.
- **Local storage only**: Your OAuth token is stored locally at `~/.otpilot/token.json`. Nothing is sent to any third-party server.
- **On-demand only**: Emails are fetched only when you press the hotkey. There is no background polling.

## Troubleshooting

| Issue                             | Solution                                                       |
| --------------------------------- | -------------------------------------------------------------- |
| "credentials.json not found"      | Run `otpilot setup` and provide your credentials file          |
| "Invalid credentials file"        | Re-download credentials.json from Google Cloud Console         |
| "Not authenticated" error         | Run `otpilot setup` to re-authenticate                         |
| No OTP found                      | Check `otp_max_age_minutes` — the email might be too old       |
| Clipboard not working (Linux)     | Install `xclip`: `sudo apt install xclip`                      |
| Hotkey not working                | Run `otpilot setup` to reconfigure the hotkey                  |
| Tray icon not visible             | Check your system tray / menu bar settings                     |

## Contributing

Contributions are welcome! See [**CONTRIBUTING.md**](CONTRIBUTING.md) for guidelines on setting up the development environment, running tests, and submitting pull requests.

## License

[MIT](../LICENSE) — use it freely.
