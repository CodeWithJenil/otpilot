import { ReactNode, useEffect } from "react";
import { Link } from "react-router-dom";
import Footer from "@/components/Footer";

type LegalLayoutProps = {
  title: string;
  children: ReactNode;
};

const LegalLayout = ({ title, children }: LegalLayoutProps) => {
  useEffect(() => {
    document.title = `${title} · otpilot`;
  }, [title]);

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="container mx-auto px-6 py-6 flex items-center justify-between gap-4">
          <Link to="/" className="font-mono font-bold tracking-tight hover:text-primary transition-colors">
            otpilot
          </Link>
          <Link to="/" className="text-sm text-muted-foreground hover:text-primary transition-colors">
            Back to home
          </Link>
        </div>
      </header>

      <section className="container mx-auto px-6 py-10">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
          <div className="mt-8">{children}</div>
        </div>
      </section>

      <Footer />
    </main>
  );
};

export default LegalLayout;

