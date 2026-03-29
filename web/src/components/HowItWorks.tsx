import { useEffect, useRef } from "react";

const steps = [
  {
    num: "01",
    title: "Setup",
    desc: "Run `pip install otpilot` and provide your Supabase Google OAuth.",
  },
  {
    num: "02",
    title: "Press",
    desc: "Hit your configured hotkey from any app, any screen.",
  },
  {
    num: "03",
    title: "Done",
    desc: "OTP is in your clipboard. No tab switching. No waiting.",
  },
];

const HowItWorks = () => {
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
    <section ref={ref} className="py-24 lg:py-32 border-t border-border">
      <div className="container mx-auto px-6">
        <h2 className="reveal text-3xl md:text-4xl font-bold text-center mb-16">
          How it works
        </h2>

        <div className="grid md:grid-cols-3 gap-8 relative">
          {/* Dotted connector line */}
          <div className="hidden md:block absolute top-8 left-[16.67%] right-[16.67%] h-px border-t border-dashed border-muted-foreground/30" />

          {steps.map((step, i) => (
            <div
              key={step.num}
              className="reveal text-center space-y-4"
              style={{ transitionDelay: `${i * 150}ms` }}
            >
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full border-2 border-primary/30 text-primary font-mono text-xl font-bold relative bg-background">
                {step.num}
              </div>
              <h3 className="text-xl font-bold text-foreground">{step.title}</h3>
              <p className="text-muted-foreground font-body max-w-xs mx-auto leading-relaxed">
                {step.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
