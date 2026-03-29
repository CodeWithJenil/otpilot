# Supabase Auth Setup Guide

This guide explains how OTPilot authentication works with **Supabase Auth + Google**.

## 1) Choose Your Auth Mode

### Hosted mode (default)

Most users can skip backend setup. OTPilot defaults to:

- `OTPILOT_AUTH_BASE_URL=https://jenil-otpilot.vercel.app`

In this mode, you only need to run:

```bash
otpilot setup
```

### Self-hosted mode

If you run your own auth API, continue with steps 2–4.

## 2) Configure Google Provider in Supabase

1. Open your Supabase project dashboard.
2. Go to **Authentication → Providers → Google**.
3. Enable Google provider.
4. Set Google OAuth scopes to include:
   - `https://www.googleapis.com/auth/gmail.readonly`
5. In Google Cloud Console, configure the OAuth app requested by Supabase and add the redirect URL shown in Supabase.

## 3) Configure OTPilot Web API Environment Variables

Set these in your deployment (for example Vercel) and local env for testing:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

See `web/api/.env.example` for placeholders.

## 4) Point OTPilot CLI to Your Deployment

Set:

- `OTPILOT_AUTH_BASE_URL=https://<your-auth-domain>`

OTPilot normalizes this value and calls:

- `/api/auth/start`
- `/api/auth/session`

## 5) Run OTPilot setup

```bash
otpilot setup
```

The CLI will:

1. Open your browser to Supabase Google OAuth.
2. Request `gmail.readonly` access.
3. Poll `/api/auth/session` with a temporary `session_key`.
4. Store the returned provider token locally.

After setup, OTPilot can run without repeating browser auth unless you re-authenticate.

## Token Storage

- Preferred: system keyring (`keyring` package support)
- Fallback: `~/.otpilot/token.json`
