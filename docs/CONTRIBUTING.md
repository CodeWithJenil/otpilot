# Contributing to OTPilot

Thank you for your interest in contributing to OTPilot! This guide will help you get set up for local development.

---

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/otpilot/otpilot.git
cd otpilot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### 3. Install in Development Mode

```bash
pip install -e ".[dev]"
# or
pip install -e .
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
otpilot version
# → OTPilot v0.1.0
```

---

## Project Structure

```
otpilot/
├── __init__.py           # Package version and metadata
├── main.py               # CLI entry point and hotkey callback
├── setup_wizard.py       # Interactive first-run setup
├── gmail_client.py       # Gmail API OAuth2 + email fetching
├── otp_extractor.py      # Regex-based OTP extraction
├── hotkey_listener.py    # Global hotkey listener (pynput)
├── tray.py               # System tray icon + menu (pystray)
├── notifier.py           # Desktop notifications (plyer)
├── clipboard.py          # Clipboard operations (pyperclip)
├── config.py             # Configuration management
└── credentials.py        # OAuth2 credential paths and validation
```

---

## Code Standards

### Type Hints

All functions must have type hints:

```python
def fetch_recent_emails(n: Optional[int] = None) -> List[Dict[str, Any]]:
    ...
```

### Docstrings

All public functions must have Google-style docstrings:

```python
def copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard.

    Args:
        text: The string to copy.

    Raises:
        ClipboardError: If the clipboard is unavailable.
    """
```

### Error Handling

- Never let exceptions crash the application silently
- Runtime errors → desktop notification
- Setup errors → rich console output
- No bare `print()` statements in production code

### Imports

- Standard library first
- Third-party packages second
- Local imports third
- Each group separated by a blank line

---

## Testing

### Running Tests

```bash
python -m pytest tests/ -v
```

### Writing Tests

- Test files go in `tests/`
- Name test files `test_<module>.py`
- Use `pytest` fixtures for common setup
- Mock external services (Gmail API, clipboard, notifications)

### Example Test

```python
from otpilot.otp_extractor import extract_otp

def test_extract_otp_from_subject():
    emails = [{"subject": "Your OTP is 123456", "body": ""}]
    assert extract_otp(emails) == "123456"

def test_no_otp_found():
    emails = [{"subject": "Meeting tomorrow", "body": "See you at 3pm"}]
    assert extract_otp(emails) is None
```

---

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the code standards above
- Add tests for new functionality
- Update documentation if needed

### 3. Test Your Changes

```bash
python -m pytest tests/ -v
otpilot version  # Verify CLI works
```

### 4. Commit

Write clear commit messages:

```
feat: add support for TOTP-style codes
fix: handle empty email body gracefully
docs: update troubleshooting section
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub with:
- A clear description of what changed and why
- Reference any related issues
- Screenshots if UI/notification changes are involved

---

## Areas for Contribution

### Good First Issues

- Add more OTP context keywords to `otp_extractor.py`
- Improve error messages
- Add support for more terminal emulators on Linux

### Feature Ideas

- Support for multiple Gmail accounts
- Custom OTP extraction patterns (user-defined regex)
- Auto-start on system boot
- OTP history (last N extracted OTPs)
- Sound notification option

### Bug Reports

When filing a bug report, please include:
- OS and version
- Python version
- Full error traceback (if applicable)
- Steps to reproduce
- Expected vs actual behavior

---

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build something useful.

---

## Questions?

Open an issue on GitHub or reach out to the maintainers. We're happy to help!
