# Supabase Auth Setup Guide

This guide explains how to configure OTPilot OAuth using **Supabase Auth + Google**.

## 1) Configure Google Provider in Supabase

1. Open your Supabase project dashboard.
2. Go to **Authentication → Providers → Google**.
3. Enable Google provider.
4. Set Google OAuth scopes to include:
   - `https://www.googleapis.com/auth/gmail.readonly`
5. In Google Cloud Console, configure the OAuth app requested by Supabase and add the redirect URL shown in Supabase.

## 2) Configure OTPilot Web API Environment Variables

Set these in your Vercel project (and local env for testing):

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

See `web/api/.env.example` for placeholders.

## 3) Run OTPilot setup

```bash
otpilot setup
```

The CLI will:

1. Open your browser to Supabase Google OAuth.
2. Request `gmail.readonly` access with offline consent prompt.
3. Poll `api/auth/session` using a temporary `session_key`.
4. Store the returned token locally (keyring when available, otherwise `~/.otpilot/token.json`).

After setup, you can run OTPilot normally without repeating browser auth unless you re-authenticate.

## Token Storage

- Preferred: system keyring (`keyring` package support)
- Fallback: `~/.otpilot/token.json`

