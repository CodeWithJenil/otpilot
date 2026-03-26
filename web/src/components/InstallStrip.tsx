import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";

const INSTALL_COMMAND = "pip install otpilot";
const SETUP_COMMAND = "otpilot setup";

const InstallStrip = () => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("visible");
        });
      },
      { threshold: 0.15 }
    );
    const els = ref.current?.querySelectorAll(".reveal");
    els?.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section id="how-to-use" ref={ref} className="py-24 lg:py-32 border-t border-border">
      <div className="container mx-auto px-6">
        <div className="reveal mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold">How to Use</h2>
            <p className="mt-2 text-muted-foreground">The new v2.0 installation process is simple and decentralized.</p>
          </div>
          <Link
            to="/installation/latest"
            className="inline-flex items-center justify-center rounded-md border border-primary/40 px-4 py-2 text-sm font-mono text-primary hover:bg-primary/10 transition-colors"
          >
            Open Installation Guide
          </Link>
        </div>

        <div className="reveal max-w-4xl mx-auto rounded-lg border border-border bg-card p-8 space-y-8">
          <div className="space-y-4">
            <h3 className="text-lg font-bold font-mono text-primary flex items-center gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full border border-primary/30 text-[10px]">01</span>
              Install Package
            </h3>
            <pre className="rounded-md border border-border bg-background/50 p-4 font-mono text-sm text-foreground overflow-x-auto">
              {INSTALL_COMMAND}
            </pre>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-bold font-mono text-primary flex items-center gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full border border-primary/30 text-[10px]">02</span>
              Configure OTPilot
            </h3>
            <pre className="rounded-md border border-border bg-background/50 p-4 font-mono text-sm text-foreground overflow-x-auto">
              {SETUP_COMMAND}
            </pre>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Run the setup wizard to import your <code className="text-foreground border-b border-border/30">credentials.json</code> and authorize your Gmail account securely.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default InstallStrip;
