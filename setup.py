"""Legacy setup.py for backwards compatibility with older pip versions."""

import re
from pathlib import Path

from setuptools import setup, find_packages


def _read_version() -> str:
    init_py = Path(__file__).parent / "otpilot" / "__init__.py"
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init_py.read_text(encoding="utf-8"), re.M)
    if not match:
        raise RuntimeError("Could not determine otpilot version from otpilot/__init__.py")
    return match.group(1)


setup(
    name="otpilot",
    version=_read_version(),
    description="Background CLI utility that copies OTPs from Gmail to clipboard on hotkey trigger",
    long_description=open("docs/README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Jenil",
    author_email="mail2jenil.pokar19@gmail.com",
    license="MIT",
    python_requires=">=3.10",
    packages=find_packages(include=["otpilot*"]),
    install_requires=[
        "google-api-python-client>=2.100.0",
        "google-auth>=2.23.0",
        "packaging>=23.0",
        "pynput>=1.7.6",
        "pystray>=0.19.5",
        "Pillow>=10.0.0",
        "pyperclip>=1.8.2",
        "plyer>=2.1.0",
        "click>=8.1.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
        "keyring>=24.0.0",
    ],
    entry_points={
        "console_scripts": [
            "otpilot=otpilot.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Communications :: Email",
        "Topic :: Utilities",
    ],
)
