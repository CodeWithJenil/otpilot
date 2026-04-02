

# OTPilot

> Press a hotkey. Your OTP is already copied.

```bash
pip install otpilot
```

---

<p align="center">
  <strong>✈ OTPilot v2.1</strong>
</p>

<p align="center">
  <em>Background utility that fetches OTPs from Gmail and copies them to your clipboard with a single hotkey press.</em>
</p>

<p align="center">
  <a href="https://github.com/codewithjenil/otpilot">GitHub</a> •
  <a href="#installation">Install</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="SETUP.md">Self-Host Auth</a> •
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## How It Works

1. **OTPilot sits silently in your system tray** — no polling, zero CPU usage at rest.
2. **Press your hotkey** (e.g. `Ctrl+Shift+O`) or run `otpilot fetch` — OTPilot scans your recent Gmail inbox and extracts the OTP.
3. **OTP is copied to your clipboard** — and optionally auto-pasted. A desktop notification confirms.

---

## Installation

```bash
pip install otpilot
```

**Requirements**

- Python 3.8+
- A Gmail account

> **Linux users**: Install clipboard support before running setup.
> ```bash
> sudo apt install xclip  # Debian/Ubuntu
> ```

---

## Quickstart

### 1. Run Setup

```bash
otpilot setup
```

The wizard will:
- Open your browser for a one-time Google sign-in (read-only Gmail access)
- Let you configure your hotkey, notifications, and scan preferences
- Save everything locally — nothing leaves your machine

### 2. Start OTPilot

```bash
otpilot start
```

OTPilot runs in the background with a system tray icon.

### 3. Daily Use

1. Receive an OTP email
2. Press your hotkey (default: `Ctrl+Shift+O`)
3. Paste — done

---

## CLI Commands

| Command             | Description                                 |
| ------------------- | ------------------------------------------- |
| `otpilot setup`     | Run or re-run the interactive setup wizard  |
| `otpilot start`     | Start the background service                |
| `otpilot fetch`     | Trigger a one-time OTP fetch from the CLI   |
| `otpilot status`    | Show auth state, hotkey, and config         |
| `otpilot hotkey`    | View or reconfigure the global hotkey       |
| `otpilot config`    | View or edit configuration interactively    |
| `otpilot logout`    | Clear stored auth token                     |
| `otpilot update`    | Check PyPI for updates and upgrade          |
| `otpilot version`   | Print the installed version                 |

---

## Configuration

OTPilot stores its configuration at `~/.otpilot/config.json`:

```json
{
  "hotkey": "ctrl+shift+o",
  "notify_on_copy": true,
  "otp_max_age_minutes": 10,
  "email_fetch_count": 10,
  "auto_paste": false,
  "auto_start_on_boot": false,
  "mask_otp_in_notification": true,
  "check_updates_on_start": true
}
```

| Field                      | Type   | Default        | Description                                       |
| -------------------------- | ------ | -------------- | ------------------------------------------------- |
| `hotkey`                   | string | `ctrl+shift+o` | Global hotkey combination                         |
| `notify_on_copy`           | bool   | `true`         | Show desktop notification when OTP is copied      |
| `otp_max_age_minutes`      | int    | `10`           | Ignore emails older than this (minutes)           |
| `email_fetch_count`        | int    | `10`           | Number of recent emails to scan (max 50)          |
| `auto_paste`               | bool   | `false`        | Auto-paste OTP after copying                      |
| `auto_start_on_boot`       | bool   | `false`        | Launch OTPilot on login                           |
| `mask_otp_in_notification` | bool   | `true`         | Mask middle digits in notification (e.g. 84••93)  |
| `check_updates_on_start`   | bool   | `true`         | Check PyPI for a newer version on startup         |

### Files Stored Locally

| Path                       | Purpose                               |
| -------------------------- | ------------------------------------- |
| `~/.otpilot/config.json`   | Hotkey and runtime settings           |
| `~/.otpilot/otpilot.log`   | Background service log                |
| `~/.otpilot/otpilot.pid`   | PID of the running background process |
| System keyring (`otpilot`) | Preferred OAuth token storage         |
| `~/.otpilot/token.json`    | Fallback token storage                |

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

- **4–8 digit standalone numbers** near context words like *OTP*, *code*, *verify*, *one-time*, *passcode*, *authentication*, *2FA*
- Only emails within `otp_max_age_minutes` are considered
- Subject line matches are prioritized over body matches

---

## Security & Privacy

- **Read-only Gmail access** — OTPilot cannot send, delete, or modify your emails
- **On-demand only** — emails are fetched only when you trigger a fetch, never polled in the background
- **Local storage** — your OAuth token is stored in your OS keyring (or `~/.otpilot/token.json` as fallback)
- **No telemetry** — no analytics, crash reporting, or data collection of any kind
- **Self-hostable auth** — advanced users can run their own auth backend (see [SETUP.md](SETUP.md))

---

## Troubleshooting

| Issue                         | Solution                                                        |
| ----------------------------- | --------------------------------------------------------------- |
| "Not authenticated" error     | Run `otpilot setup` to re-authenticate                          |
| No OTP found                  | Check `otp_max_age_minutes` — the email might be too old        |
| Clipboard not working (Linux) | Install `xclip`: `sudo apt install xclip`                       |
| Hotkey not working            | Run `otpilot hotkey` to reconfigure                             |
| Tray icon not visible         | Check your system tray / menu bar settings                      |
| Update notice repeating       | Run `otpilot update` or set `check_updates_on_start` to `false` |

---

## Contributing

Contributions are welcome! See [**CONTRIBUTING.md**](CONTRIBUTING.md) for dev setup, code standards, and the PR process.

---

## License

[MIT](LICENSE) — use it freely.
