# Google Cloud OAuth Setup Guide

This guide walks you through creating a Google Cloud project and downloading the `credentials.json` file that OTPilot needs to access your Gmail.

> **Time required**: ~5 minutes. You only need to do this once.

---

## Prerequisites

- A Google account (the one you receive OTP emails on)
- Access to [Google Cloud Console](https://console.cloud.google.com/)

---

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top of the page
3. Click **New Project**
4. Enter a project name: `OTPilot` (or anything you prefer)
5. Click **Create**
6. Make sure the new project is selected in the project dropdown

---

## Step 2: Enable the Gmail API

1. In the left sidebar, go to **APIs & Services** → **Library**
2. Search for **Gmail API**
3. Click on **Gmail API**
4. Click **Enable**

---

## Step 3: Configure the OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type
3. Click **Create**
4. Fill in the required fields:
   - **App name**: `OTPilot`
   - **User support email**: your email
   - **Developer contact email**: your email
5. Click **Save and Continue**
6. On the **Data Access** page:
   - Click **Add or Remove Scopes**
   - Search for `gmail.readonly`
   - Check the box next to `https://www.googleapis.com/auth/gmail.readonly`
   - Click **Update**
   - Click **Save and Continue**
7. On the **Audience** page:
   - Click **Add Users**
   - Enter your Gmail address
   - Click **Add**
   - Click **Save and Continue**
8. Review and click **Back to Dashboard**

---

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. For **Application type**, select **Desktop app**
4. Enter a name: `OTPilot Desktop`
5. Click **Create**
6. A dialog shows your **Client ID** and **Client Secret**
7. Click **Download JSON** to save the file

> **Important**: Save this file somewhere you can find it (e.g. your Downloads folder). You'll need to provide the path during `otpilot setup`.

---

## Step 5: Run OTPilot Setup

```bash
otpilot setup
```

The wizard will ask you for the path to your `credentials.json` file:

```
Step 1: Google Cloud Credentials

  Have you already downloaded your credentials.json? [y/N]: y
  Enter the path to your credentials.json file: ~/Downloads/client_secret_xxxx.json

  ✓ Credentials saved to ~/.otpilot/credentials.json
  Your credentials never leave your machine.
```

OTPilot copies the file to `~/.otpilot/credentials.json`. You can delete the original after setup.

---

## Step 6: Authenticate

After providing credentials, the wizard opens your browser for Google sign-in:

```
Step 2: Google Account Sign-In
  Opening your browser for Gmail authorization...
```

- Sign in with the Gmail account you added as a test user (Step 3.7)
- Click **Allow** to grant read-only access
- The browser shows "The authentication flow has completed"

```
  ✓ Authentication successful!
```

---

## Where Are My Credentials Stored?

| File                             | Location                     | Contents                        |
| -------------------------------- | ---------------------------- | ------------------------------- |
| `credentials.json`              | `~/.otpilot/credentials.json` | Your OAuth client ID & secret   |
| `token.json`                    | `~/.otpilot/token.json`       | OAuth session token (auto-generated) |

**Your credentials never leave your machine.** OTPilot only uses them locally to authenticate with Google's servers.

---

## Publishing Your App (Optional)

If you want to use OTPilot with any Gmail account (not just test users):

1. Go to **OAuth consent screen**
2. Click **Publish App**
3. Submit for Google's verification review
4. Once verified, any Gmail user can authorize your app

> **Note**: Google's verification process requires a privacy policy and may take several weeks. For personal use, you can skip this step — just add yourself as a test user.

---

## Scopes Used

OTPilot requests only one scope:

| Scope                                                | Permission           |
| ---------------------------------------------------- | -------------------- |
| `https://www.googleapis.com/auth/gmail.readonly`     | Read-only email access |

OTPilot **cannot** send, delete, or modify your emails.

---

## Troubleshooting

### "Access blocked: This app's request is invalid"

- Make sure you added your email as a test user (Step 3.7)
- Make sure the OAuth consent screen is configured correctly

### "Error 403: access_denied"

- The user hasn't been added as a test user
- Or the app hasn't been published for general use

### "Error 400: redirect_uri_mismatch"

- Make sure you selected **Desktop app** as the application type (Step 4.3)

### "credentials.json not found"

- Run `otpilot setup` and provide the path to your downloaded credentials file
- Make sure you downloaded the JSON file from Step 4.7

### "Invalid credentials file"

- Make sure you downloaded the **OAuth 2.0 Client ID** JSON, not a service account key
- The file should contain an `"installed"` key at the top level

### Token keeps expiring

- Tokens for apps in "Testing" status expire after 7 days
- To fix: publish the app (see Publishing section above)
