import { Link } from "react-router-dom";
import LogoMark from "./LogoMark";
import TerminalWindow from "./TerminalWindow";

const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      <div className="hero-glow" />
      <div className="container mx-auto px-6 py-24 lg:py-32">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Text side */}
          <div className="space-y-8">
            <div className="hero-animate hero-animate-delay-1 flex items-center gap-4">
              <LogoMark compact />
              <span className="px-2 py-0.5 rounded-full border border-primary/20 bg-primary/5 text-[10px] font-mono text-primary tracking-tighter">v2.0.0</span>
            </div>
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold leading-[1.05] tracking-tight">
              <span className="hero-animate hero-animate-delay-1 block text-foreground">Your OTP.</span>
              <span className="hero-animate hero-animate-delay-2 block text-primary">
                Already copied.<span className="cursor-blink ml-1">▋</span>
              </span>
            </h1>

            <p className="hero-animate hero-animate-delay-3 text-lg md:text-xl text-muted-foreground font-body max-w-lg leading-relaxed">
              Press a hotkey. <span className="text-foreground font-medium">otpilot</span> finds the code in your Gmail and puts it in your clipboard before you even switch tabs.
            </p>

            <div className="hero-animate hero-animate-delay-4 flex flex-wrap gap-4">
              <Link
                to="/installation/latest"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-md bg-primary text-primary-foreground font-mono font-semibold text-sm hover:brightness-110 hover:-translate-y-0.5 transition-all duration-200"
              >
                Open installation guide
              </Link>
              <a
                href="https://github.com/codewithjenil/otpilot"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-md border border-border bg-card/50 text-foreground font-mono font-semibold text-sm hover:bg-card hover:-translate-y-0.5 transition-all duration-200"
              >
                GitHub Source
              </a>
            </div>

            <div className="hero-animate hero-animate-delay-5 flex flex-wrap gap-2">
              {["macOS", "Linux", "Windows"].map((os) => (
                <span
                  key={os}
                  className="px-3 py-1 text-xs font-mono text-muted-foreground border border-border rounded-full"
                >
                  {os}
                </span>
              ))}
            </div>
          </div>

          {/* Terminal side */}
          <div className="hero-animate hero-animate-delay-4 flex justify-center lg:justify-end">
            <TerminalWindow />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
