# Changelog

All notable changes to OTPilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] — 2026-03-28

### Added
- **Auto-paste**: OTPilot can now directly paste the OTP instead of just copying it. Configurable during setup.
- **Expanded setup wizard**: First-time setup now configures all preferences in one go:
- Auto-paste toggle
- Desktop notification preferences
- OTP masking in notifications
- Email scan count (1–50)
- OTP max age in minutes (1–60)
- Automatic update checks on startup
- Auto-start on boot (launchd on macOS, registry on Windows, systemd on Linux)
- **`otpilot update` command**: Checks PyPI for the latest version and offers to upgrade in one step.
- **Background update check**: On startup, silently checks for updates and shows a desktop notification if a newer version is available (configurable, on by default).
- **GitHub Discussions link**: Shown at the end of first-time setup only, pointing users to the feedback channel.

### Changed
- **config.json**: Added new fields — auto_paste, auto_start_on_boot, notification_sound, mask_otp_in_notification, check_updates_on_start, setup_complete. All default to safe values and are backwards compatible.
- **Setup wizard**: Now writes config once at the very end instead of incrementally. Cleaner and more reliable.

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
