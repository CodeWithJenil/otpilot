import { useEffect, useRef } from "react";

const features = [
  { icon: "⌨", title: "Global Hotkey", desc: "Works from any app. Configure any key combo you want." },
  { icon: "⚡", title: "Instant", desc: "Fetches and copies in under a second." },
  { icon: "🔒", title: "Private", desc: "OAuth2. Your emails never leave your machine." },
  { icon: "🖥", title: "Cross-Platform", desc: "macOS (universal), Linux (static), Windows." },
  { icon: "📦", title: "Tiny", desc: "Under 8MB binary. Zero background CPU when idle." },
  { icon: "🔁", title: "Auto-Refresh", desc: "Token refresh handled silently. Set and forget." },
];

const FeaturesGrid = () => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("visible");
        });
      },
      { threshold: 0.1 }
    );
    const els = ref.current?.querySelectorAll(".reveal");
    els?.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={ref} className="py-24 lg:py-32 border-t border-border">
      <div className="container mx-auto px-6">
        <h2 className="reveal text-3xl md:text-4xl font-bold text-center mb-16">
          Features
        </h2>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <div
              key={f.title}
              className="reveal group p-6 rounded-lg border border-border/50 bg-card/30 hover:border-primary/30 hover:shadow-[0_0_30px_-10px_hsl(152_100%_50%_/_0.15)] transition-all duration-300"
              style={{ transitionDelay: `${i * 80}ms` }}
            >
              <div className="text-2xl mb-3">{f.icon}</div>
              <h3 className="text-lg font-bold text-foreground mb-2 font-mono">{f.title}</h3>
              <p className="text-sm text-muted-foreground font-body leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesGrid;
