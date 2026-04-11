# OTPilot Web Frontend

This web app hosts the browser sign-in page used by OTPilot CLI.

## Build and Deploy (Vercel)

### 1) Build locally

```bash
cd web
npm install
npm run build
```

This produces static assets in `web/dist`.

### 2) Deploy to Vercel

1. Push this repo to GitHub.
2. In Vercel, click **Add New Project** and import the repo.
3. Set **Root Directory** to `web`.
4. Framework preset: **Vite**.
5. Build command: `npm run build`.
6. Output directory: `dist`.
7. Add environment variables listed below.
8. Deploy and confirm your auth page URL, e.g.:
   - `https://jenil-otpilot.vercel.app/auth`

## Firebase Setup

1. Create a Firebase project in the Firebase Console:
   - https://console.firebase.google.com
2. Enable **Authentication → Sign-in method → Google**.
3. Add authorized domains in Firebase Auth settings:
   - `jenil-otpilot.vercel.app`
   - `localhost`
4. Configure environment variables in Vercel (or local `.env`):
   - `NEXT_PUBLIC_FIREBASE_API_KEY`
   - `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
   - `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
5. Ensure the Google Cloud project linked to Firebase has:
   - Gmail API enabled
   - OAuth consent screen configured
   - `https://www.googleapis.com/auth/gmail.readonly` included as a sensitive scope

## Configure Firebase and Google OAuth (Client ID/Secret)

Firebase Auth with Google still relies on Google OAuth credentials behind the scenes. Configure them like this:

1. Open Google Cloud Console for the project linked to Firebase.
2. Ensure **Gmail API** is enabled.
3. Configure **OAuth consent screen**:
   - App name + support email
   - Add scope: `https://www.googleapis.com/auth/gmail.readonly`
   - Add test users (while app is in testing)
4. In **Credentials**, create/verify an OAuth 2.0 **Web application** client.
5. Add authorized JavaScript origins:
   - `https://jenil-otpilot.vercel.app`
   - `http://localhost` (optional for local web testing)
6. In Firebase Console → Authentication → Sign-in method → Google:
   - Enable Google provider
   - Select the same support email/project
   - Firebase manages the Google client wiring for popup sign-in.

> Note: For this frontend, you do **not** place Google client secret in browser env vars.  
> Only Firebase public web config values are used client-side.

## Environment Variables

Set these in Vercel Project Settings → Environment Variables:

- `NEXT_PUBLIC_FIREBASE_API_KEY`
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID`

For local Vite development, you can also use:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`

## Who Sets Up What

### You (OTPilot maintainer / deployer)
- Deploy this web app (or equivalent auth page)
- Configure Firebase + Google provider
- Set Firebase env vars in hosting
- Share the final auth URL with users (example: `https://jenil-otpilot.vercel.app/auth`)

### End User (OTPilot CLI user)
- Install OTPilot locally
- Run `otpilot setup`
- Choose **Firebase Auth**
- Paste the shared auth URL
- Complete Google sign-in and return to terminal

## Auth Flow

OTPilot CLI opens:

`/auth?redirect_uri=http://localhost:{port}/callback`

The page signs in with Google via Firebase and redirects back to `redirect_uri` with:
- `access_token`
- `refresh_token` (if available)
- `expires_at`
