import { useCallback, useEffect, useMemo, useState } from "react";
import { GoogleAuthProvider, getRedirectResult, signInWithPopup, signInWithRedirect } from "firebase/auth";
import { Button } from "@/components/ui/button";
import { auth, googleProvider } from "@/lib/firebase";

const Auth = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [error, setError] = useState<string>("");
  const [useRedirectFallback, setUseRedirectFallback] = useState(false);
  const [didRedirectBack, setDidRedirectBack] = useState(false);

  const redirectUri = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("redirect_uri") || "";
  }, []);

  const finalizeAuth = useCallback(
    (result: unknown) => {
      const credential = GoogleAuthProvider.credentialFromResult(result as never);
      const accessToken = credential?.accessToken || "";
      const tokenResponse = (result as { _tokenResponse?: { refreshToken?: string } })._tokenResponse;
      const refreshToken = tokenResponse?.refreshToken || "";
      const expiresAt = Math.floor(Date.now() / 1000) + 3600;

      // Firebase client SDK does not reliably expose Google refresh tokens in documented fields.
      // We log token metadata for debugging and pass an empty refresh token when unavailable.
      console.info("Firebase auth token fields", {
        hasAccessToken: Boolean(accessToken),
        hasFirebaseUserRefreshToken: Boolean((result as { user?: { refreshToken?: string } }).user?.refreshToken),
        hasTokenResponseRefreshToken: Boolean(refreshToken),
      });

      if (!accessToken) {
        setError("Google sign-in succeeded but no access token was returned. Please try again.");
        return;
      }

      const callbackUrl = new URL(redirectUri);
      callbackUrl.searchParams.set("access_token", accessToken);
      callbackUrl.searchParams.set("refresh_token", refreshToken);
      callbackUrl.searchParams.set("expires_at", String(expiresAt));

      setIsRedirecting(true);
      window.location.assign(callbackUrl.toString());
    },
    [redirectUri],
  );

  useEffect(() => {
    if (!redirectUri) {
      return;
    }

    getRedirectResult(auth)
      .then((result) => {
        if (!result) {
          return;
        }
        setDidRedirectBack(true);
        finalizeAuth(result);
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Sign-in failed.";
        setError(message);
      });
  }, [finalizeAuth, redirectUri]);

  const onSignIn = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      const result = await signInWithPopup(auth, googleProvider);
      finalizeAuth(result);
    } catch (err: unknown) {
      const code = (err as { code?: string })?.code;
      if (code === "auth/popup-blocked") {
        setUseRedirectFallback(true);
        setError("Popup was blocked by your browser. Use the redirect sign-in option below.");
      } else {
        const message = err instanceof Error ? err.message : "Sign-in failed.";
        setError(message);
      }
    } finally {
      setIsLoading(false);
    }
  }, [finalizeAuth]);

  const onSignInWithRedirect = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      await signInWithRedirect(auth, googleProvider);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Redirect sign-in failed.";
      setError(message);
      setIsLoading(false);
    }
  }, []);

  if (!redirectUri) {
    return (
      <main className="min-h-screen bg-background text-foreground flex items-center justify-center px-6">
        <div className="max-w-md w-full rounded-lg border border-border bg-card p-6 space-y-3">
          <h1 className="text-xl font-semibold">OTPilot Authentication</h1>
          <p className="text-sm text-muted-foreground">Missing redirect_uri. Please re-run otpilot setup.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="cursor-default min-h-screen bg-background text-foreground flex items-center justify-center px-6">
      <div className="max-w-md w-full rounded-lg border border-border bg-card p-6 space-y-4">
        <h1 className="text-xl font-semibold">Sign in with Google</h1>
        <p className="text-sm text-muted-foreground">
          Authorize Gmail read-only access to connect OTPilot.
        </p>

        {isRedirecting || didRedirectBack ? (
          <p className="text-sm">OTPilot is now authenticated. You can close this tab.</p>
        ) : (
          <>
            <Button onClick={onSignIn} disabled={isLoading} className="w-full">
              {isLoading ? "Signing in..." : "Sign in with Google"}
            </Button>

            {useRedirectFallback && (
              <Button onClick={onSignInWithRedirect} variant="outline" disabled={isLoading} className="w-full">
                Click here to sign in (redirect mode)
              </Button>
            )}
          </>
        )}

        {error && (
          <div className="space-y-2">
            <p className="text-sm text-red-500">{error}</p>
            <Button onClick={onSignIn} variant="secondary" disabled={isLoading} className="w-full">
              Try again
            </Button>
          </div>
        )}
      </div>
    </main>
  );
};

export default Auth;
