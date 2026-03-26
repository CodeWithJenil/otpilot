"""Legacy setup.py for backwards compatibility with older pip versions."""

from setuptools import setup, find_packages

setup(
    name="otpilot",
    version="2.0.0",
    description="Background desktop utility that copies OTPs from Gmail to clipboard on hotkey trigger.",
    long_description=open("docs/README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="OTPilot Contributors",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(include=["otpilot*"]),
    install_requires=[
        "google-api-python-client>=2.100.0",
        "google-auth-oauthlib>=1.1.0",
        "google-auth>=2.23.0",
        "pynput>=1.7.6",
        "pystray>=0.19.5",
        "Pillow>=10.0.0",
        "pyperclip>=1.8.2",
        "plyer>=2.1.0",
        "click>=8.1.0",
        "rich>=13.0.0",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Email",
        "Topic :: Utilities",
    ],
)
