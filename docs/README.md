![OTPilot Demo](assets/demo.gif)

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

1. **OTPilot sits silently in your system tray** — no polling loop, runs only when needed.
2. **Press your hotkey** (e.g. `Ctrl+Shift+O`) or run `otpilot fetch` — OTPilot fetches recent Gmail emails and extracts an OTP.
3. **OTP is copied to your clipboard** — and optionally auto-pasted. A desktop notification confirms the action.

## Installation

```bash
pip install otpilot
```

### Requirements

- **Python 3.8+**
- **Gmail account**
- **Supabase-backed auth endpoint** (default is OTPilot hosted auth)
- **OS**: macOS, Windows, or Linux

> **Linux users**: Make sure `xclip` or `xsel` is installed for clipboard support.
> ```bash
> sudo apt install xclip  # Debian/Ubuntu
> ```

## Quickstart

### 1. Configure Auth (if self-hosting)

For most users, no extra setup is required. OTPilot uses its hosted auth endpoint by default.

If you run your own OTPilot auth API, follow [SETUP.md](SETUP.md) and set `OTPILOT_AUTH_BASE_URL`.

### 2. Run Setup

```bash
otpilot setup
```

The wizard will:
- Open your browser for Supabase Google sign-in
- Request Gmail read-only access
- Let you set your preferred hotkey
- Configure copy/paste and scan preferences
- Save your configuration and token locally

### 3. Start OTPilot

```bash
otpilot start
```

OTPilot runs in the background with a system tray icon. Press your hotkey whenever you need an OTP.

### 4. Daily Use

1. Receive an OTP email in Gmail
2. Press your hotkey (default: `Ctrl+Shift+O`) or run `otpilot fetch`
3. Paste the OTP — done!

## Authentication Setup

OTPilot uses Supabase Auth for Google OAuth.

1. Hosted mode (default): run `otpilot setup`
2. Self-hosted mode: deploy the auth API and set `OTPILOT_AUTH_BASE_URL`
3. Complete browser auth and OTPilot stores your token locally

See [**SETUP.md**](SETUP.md) for full instructions.

## CLI Commands

| Command              | Description                              |
| -------------------- | ---------------------------------------- |
| `otpilot setup`      | Run or re-run the interactive setup      |
| `otpilot start`      | Start the background service             |
| `otpilot fetch`      | Trigger one OTP fetch immediately        |
| `otpilot status`     | Show auth state, hotkey, and config path |
| `otpilot hotkey`     | View or reconfigure the global hotkey    |
| `otpilot update`     | Check PyPI and upgrade via pip           |
| `otpilot version`    | Print the version number                 |

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
  "notification_sound": false,
  "mask_otp_in_notification": true,
  "check_updates_on_start": true,
  "theme": "default",
  "setup_complete": false
}
```

| Field                      | Type    | Default          | Description                                    |
| -------------------------- | ------- | ---------------- | ---------------------------------------------- |
| `hotkey`                   | string  | `ctrl+shift+o`   | Global hotkey combination                      |
| `notify_on_copy`           | bool    | `true`           | Show desktop notification when OTP is copied   |
| `otp_max_age_minutes`      | int     | `10`             | Ignore emails older than this (minutes)        |
| `email_fetch_count`        | int     | `10`             | Number of recent emails to scan                |
| `auto_paste`               | bool    | `false`          | Auto-paste OTP after copying                   |
| `auto_start_on_boot`       | bool    | `false`          | Register OTPilot to start on login             |
| `notification_sound`       | bool    | `false`          | Reserved for future sound behavior             |
| `mask_otp_in_notification` | bool    | `true`           | Mask middle OTP digits in notifications        |
| `check_updates_on_start`   | bool    | `true`           | Check PyPI for updates on startup              |
| `theme`                    | string  | `default`        | Reserved for future UI themes                  |
| `setup_complete`           | bool    | `false`          | Indicates setup wizard completion              |

### Files Stored Locally

| File / Store                      | Purpose                              |
| --------------------------------- | ------------------------------------ |
| `~/.otpilot/config.json`          | Hotkey and runtime settings          |
| System keyring (`otpilot`)        | Preferred token storage              |
| `~/.otpilot/token.json`           | Fallback token storage               |

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
- If multiple OTPs are found, subject matches are prioritized, then body matches

## Security & Privacy

- **OAuth via Supabase**: browser sign-in is handled through Supabase Auth + Google provider.
- **Read-only access**: OTPilot only reads your emails — it cannot send, delete, or modify anything.
- **Local storage only**: OAuth token is stored in system keyring when available, otherwise `~/.otpilot/token.json`.
- **On-demand fetching**: Emails are fetched only when triggered by hotkey or `otpilot fetch`.

## Troubleshooting

| Issue                             | Solution                                                       |
| --------------------------------- | -------------------------------------------------------------- |
| "Not authenticated" error         | Run `otpilot setup` to re-authenticate                         |
| No OTP found                      | Check `otp_max_age_minutes` — the email might be too old       |
| Clipboard not working (Linux)     | Install `xclip`: `sudo apt install xclip`                      |
| Hotkey not working                | Run `otpilot hotkey` or `otpilot setup`                        |
| Tray icon not visible             | Check your system tray / menu bar settings                     |
| Update notice appears repeatedly  | Run `otpilot update` or disable `check_updates_on_start`       |

## Contributing

Contributions are welcome! See [**CONTRIBUTING.md**](CONTRIBUTING.md) for guidelines on setting up the development environment, running tests, and submitting pull requests.

## License

[MIT](../LICENSE) — use it freely.
