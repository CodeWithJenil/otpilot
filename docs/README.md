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
  <a href="SETUP.md">Supabase Auth Setup</a> •
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
- **Supabase project** with Google provider enabled ([setup guide](SETUP.md))
- **OS**: macOS, Windows, or Linux

> **Linux users**: Make sure `xclip` or `xsel` is installed for clipboard support.
> ```bash
> sudo apt install xclip  # Debian/Ubuntu
> ```

## Quickstart

### 1. Configure Supabase Auth

Follow the [full guide](SETUP.md) to configure Supabase Google OAuth for OTPilot.

### 2. Run Setup

```bash
otpilot setup
```

The wizard will:
- Open your browser for Supabase Google sign-in (one-time authorization)
- Request Gmail read-only access
- Let you set your preferred hotkey
- Save your configuration and token locally

### 3. Start OTPilot

```bash
otpilot start
```

OTPilot runs in the background with a system tray icon. Press your hotkey whenever you need an OTP.

### 4. Daily Use

1. Receive an OTP email in Gmail
2. Press your hotkey (default: `Ctrl+Shift+O`)
3. Paste the OTP — done!

## Authentication Setup

OTPilot now uses Supabase Auth for Google OAuth.

1. Configure Google provider in Supabase
2. Add `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` to your web API environment
3. Run `otpilot setup` to complete browser auth

See [**SETUP.md**](SETUP.md) for full instructions.

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

- **OAuth via Supabase**: browser sign-in is handled through Supabase Auth + Google provider.
- **Read-only access**: OTPilot only reads your emails — it cannot send, delete, or modify anything.
- **Local storage only**: Your OAuth token is stored locally at `~/.otpilot/token.json`. Nothing is sent to any third-party server.
- **On-demand only**: Emails are fetched only when you press the hotkey. There is no background polling.

## Troubleshooting

| Issue                             | Solution                                                       |
| --------------------------------- | -------------------------------------------------------------- |
| "Not authenticated" error         | Run `otpilot setup` to re-authenticate                         |
| No OTP found                      | Check `otp_max_age_minutes` — the email might be too old       |
| Clipboard not working (Linux)     | Install `xclip`: `sudo apt install xclip`                      |
| Hotkey not working                | Run `otpilot setup` to reconfigure the hotkey                  |
| Tray icon not visible             | Check your system tray / menu bar settings                     |

## Contributing

Contributions are welcome! See [**CONTRIBUTING.md**](CONTRIBUTING.md) for guidelines on setting up the development environment, running tests, and submitting pull requests.

## License

[MIT](../LICENSE) — use it freely.
