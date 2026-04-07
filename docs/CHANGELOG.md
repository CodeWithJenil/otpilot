# Changelog

All notable changes to OTPilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

---

## [2.3.0] — 2026-04-07

### Added
- OTP history with CLI listing and clearing
- Notification sound toggle
- Retry logic with exponential backoff for Gmail fetches
- Rotating logs at `~/.otpilot/otpilot.log`
- `otpilot stop`
- `otpilot logs`

### Changed
- Authentication now stores refresh tokens and expiry for silent refresh.
- Added `otp_history_count` config key.
- Minimum supported Python is now 3.10.

### Breaking
- Existing users must re-authenticate once to populate refresh token metadata.

## [2.1.0] — 2026-03-28

### Added
- **Auto-paste**: OTPilot can now paste the OTP automatically after copying (optional).
- **Expanded setup wizard**: Setup now collects key runtime preferences in one flow:
- Notification toggle
- Auto-paste toggle
- OTP max age (1–60 minutes)
- Email scan count (1–50)
- Auto-start preference
- **`otpilot update` command**: Checks PyPI for the latest version and offers one-step upgrade.
- **Startup update checks**: Optional background update check with desktop notification.
- **`otpilot fetch` command**: Trigger one OTP fetch immediately from CLI.

### Changed
- **config.json**: Added fields `auto_paste`, `auto_start_on_boot`, `notification_sound`, `mask_otp_in_notification`, `check_updates_on_start`, and `setup_complete`.
- **Token storage**: Keyring-first token persistence with `~/.otpilot/token.json` fallback.
- **Setup flow**: Supabase Google sign-in is the primary authentication path.

---

## [2.0.0] — 2026-03-26

### Added
- **User-Provided Credentials**: Migrated from bundled OAuth credentials to user-provided `credentials.json` for enhanced privacy and project isolation.
- **`otpilot hotkey` Command**: New standalone CLI command to view and reconfigure the global hotkey interactively or via `--set`.
- **Improved macOS Notifications**: Switched to native `osascript` (AppleScript) for macOS notifications to eliminate the heavy `pyobjus` dependency and improve reliability.
- **Enhanced Setup Wizard**: New step-by-step credential import process with validation and helpful troubleshooting guides.

### Changed
- **Setup Flow**: The setup wizard now guides users through creating a Google Cloud project as the first mandatory step.
- **Version Lifecycle**: Major version bump to 2.0.0 marking the transition to a production-ready, decentralised authentication model.

### Fixed
- **Accessibility Issues**: Improved feedback for macOS accessibility permissions.
- **Dependency Bloat**: Reduced installation size and complexity by removing strict requirements for OS-specific helper libraries.

---

## [0.1.0] — 2024-01-01

### Added

- **Core functionality**: Fetch OTPs from Gmail on hotkey trigger and copy to clipboard
- **Gmail API integration**: OAuth2 authentication with `gmail.readonly` scope
- **OTP extraction engine**: Regex-based extraction supporting 4–8 digit codes with context-word matching
- **Global hotkey listener**: Configurable keyboard shortcuts via `pynput`
- **System tray icon**: Background operation with `pystray` — includes Settings, Re-authenticate, and Quit menu items
- **Desktop notifications**: Native OS notifications via `plyer` showing masked OTP on copy
- **Interactive setup wizard**: Rich-styled terminal wizard for first-run configuration
- **CLI interface**: `otpilot setup`, `otpilot start`, `otpilot status`, `otpilot version` commands via `click`
- **Configuration management**: JSON-based config at `~/.otpilot/config.json`
- **Cross-platform support**: macOS, Windows, and Linux
- **Privacy-first design**: Read-only Gmail access, local-only token storage, on-demand fetching (no polling)

### Security

- OAuth tokens stored locally at `~/.otpilot/token.json`
- OTP digits partially masked in notification display
- No data sent to third-party servers
- Gmail API scope limited to read-only access

### Documentation

- Full README with installation, quickstart, and troubleshooting
- Step-by-step user flow guide (`USER_FLOW.md`)
- Detailed OAuth setup guide for custom credentials (`SETUP.md`)
- Contributing guide with code standards and PR process (`CONTRIBUTING.md`)
