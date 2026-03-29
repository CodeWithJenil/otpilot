import Footer from "@/components/Footer";
import GrainOverlay from "@/components/GrainOverlay";
import LogoMark from "@/components/LogoMark";
import CustomCursor from "@/components/CustomCursor";
import { Link, useParams } from "react-router-dom";

const Installation = () => {
  const { version } = useParams();
  const normalizedVersion = (version?.trim() || "2.0.0").toLowerCase();

  return (
    <main className="min-h-screen bg-background text-foreground">
      <CustomCursor />
      <GrainOverlay />

      <section className="border-b border-border">
        <div className="container mx-auto px-6 py-10 md:py-14 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <LogoMark compact />
          <p className="font-mono text-sm text-muted-foreground">
            Version: <span className="text-primary">{normalizedVersion}</span>
          </p>
        </div>
      </section>

      <section className="container mx-auto px-6 py-10 md:py-14 space-y-12">
        {/* Step 1: Install */}
        <div className="rounded-xl border border-border bg-card/70 p-6 md:p-8 space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold">Step 1 — Install via pip</h1>
            <p className="text-muted-foreground">
              OTPilot is distributed as a Python package. Make sure you have Python 3.8+ installed.
            </p>
          </div>
          
          <pre className="rounded-md border border-border bg-background/40 p-4 font-mono text-sm text-foreground whitespace-pre-wrap leading-relaxed overflow-x-auto">
            pip install otpilot
          </pre>
          
          <div className="flex flex-wrap gap-2 text-xs font-mono text-muted-foreground">
            <span className="px-2 py-1 border border-border rounded">macOS</span>
            <span className="px-2 py-1 border border-border rounded">Windows</span>
            <span className="px-2 py-1 border border-border rounded">Linux</span>
          </div>
        </div>

        {/* Step 2: Credentials */}
        <div className="rounded-xl border border-border bg-card/70 p-6 md:p-8 space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">Step 2 — Get Google Credentials</h2>
            <p className="text-muted-foreground">
              To use OTPilot, you need your own <code className="text-primary">Supabase Google OAuth</code> file from the Google Cloud Console.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <ul className="space-y-3 text-sm text-muted-foreground list-decimal list-inside">
                <li>Go to <a href="https://console.cloud.google.com" target="_blank" className="text-primary hover:underline">Google Cloud Console</a></li>
                <li>Create a project and enable the <strong>Gmail API</strong></li>
                <li>Create <strong>OAuth 2.0 Client ID</strong> (Desktop app)</li>
                <li>Download the JSON file</li>
              </ul>
            </div>
            <div className="p-4 rounded border border-border bg-background/20">
              <p className="text-xs text-muted-foreground italic leading-relaxed">
                "Wait, why do I need this?" <br /><br />
                Version 2.0 uses a decentralized model. By providing your own keys, your emails never touch third-party servers, and your usage is private to your own Google Cloud project.
              </p>
            </div>
          </div>
        </div>

        {/* Step 3: Run Setup */}
        <div className="rounded-xl border border-border bg-card/70 p-6 md:p-8 space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">Step 3 — Initialize</h2>
            <p className="text-muted-foreground">
              Run the setup wizard to import your credentials and set your hotkey.
            </p>
          </div>

          <pre className="rounded-md border border-border bg-background/40 p-4 font-mono text-sm text-foreground">
            otpilot setup
          </pre>

          <p className="text-sm text-muted-foreground">
            When prompted, provide the path to the <code className="text-primary">Supabase Google OAuth</code> you downloaded in Step 2.
          </p>
        </div>

        {/* Step 4: Start Service */}
        <div className="rounded-xl border border-border bg-card/70 p-6 md:p-8 space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">Step 4 — Launch</h2>
            <p className="text-muted-foreground">
              Start the background listener.
            </p>
          </div>

          <pre className="rounded-md border border-border bg-background/40 p-4 font-mono text-sm text-foreground">
            otpilot start
          </pre>

          <p className="text-sm text-muted-foreground">
            OTPilot will appear in your system tray. Press <kbd className="px-1.5 py-0.5 rounded bg-muted text-foreground border border-border">Ctrl+Shift+O</kbd> (default) to copy your latest OTP.
          </p>
        </div>

        <div className="flex justify-center pt-8">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-md bg-zinc-900 text-white font-mono text-sm hover:bg-zinc-800 transition-colors"
          >
            Back to homepage
          </Link>
        </div>
      </section>

      <Footer />
    </main>
  );
};

export default Installation;
