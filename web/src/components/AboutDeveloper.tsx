const AboutDeveloper = () => {
  return (
    <section className="border-t border-border py-16">
      <div className="container mx-auto px-6">
        <div className="max-w-3xl rounded-xl border border-border bg-card/70 p-6 md:p-8">
          <p className="font-mono text-xs uppercase tracking-wider text-primary mb-3">About Developer</p>
          <h3 className="text-2xl font-bold mb-3">Built by Jenil</h3>
          <p className="text-muted-foreground leading-relaxed mb-4">
            otpilot is developed and maintained by Jenil. Follow progress, experiments, and more projects on the portfolio.
          </p>
          <div className="flex flex-wrap gap-4">
            <a
              href="https://jenilbuildspace.vercel.app"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-primary/40 text-primary font-mono text-sm hover:bg-primary/10 transition-colors"
            >
              Visit Portfolio
            </a>
            <a
              href="https://github.com/codewithjenil/otpilot"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-border text-foreground font-mono text-sm hover:bg-card transition-colors"
            >
              Source on GitHub
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutDeveloper;
