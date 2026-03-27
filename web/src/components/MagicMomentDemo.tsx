import { useEffect, useMemo, useRef, useState } from "react";

const OTP = "847291";
const HOTKEY = "Ctrl+Shift+O";
const OTP_DIGITS = OTP.split("");

type Phase = "idle" | "hotkey" | "toast" | "typing" | "done";

const usePrefersReducedMotion = () => {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const media = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!media) return;
    const onChange = () => setReduced(media.matches);
    onChange();
    media.addEventListener?.("change", onChange);
    return () => media.removeEventListener?.("change", onChange);
  }, []);

  return reduced;
};

const MagicMomentDemo = () => {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [phase, setPhase] = useState<Phase>("idle");
  const [typedCount, setTypedCount] = useState(0);

  const timeouts = useRef<ReturnType<typeof setTimeout>[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const digits = OTP_DIGITS;
  const shownDigits = useMemo(() => digits.slice(0, typedCount), [typedCount, digits]);

  useEffect(() => {
    if (prefersReducedMotion) {
      setPhase("done");
      setTypedCount(digits.length);
      return;
    }

    const clearAll = () => {
      timeouts.current.forEach(clearTimeout);
      timeouts.current = [];
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
    };

    const schedule = (fn: () => void, ms: number) => {
      const id = setTimeout(fn, ms);
      timeouts.current.push(id);
      return id;
    };

    const startTyping = () => {
      setPhase("typing");
      setTypedCount(0);
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        setTypedCount((prev) => {
          const next = prev + 1;
          if (next >= digits.length) {
            if (intervalRef.current) clearInterval(intervalRef.current);
            intervalRef.current = null;
            setPhase("done");
            schedule(() => {
              setPhase("idle");
              setTypedCount(0);
              schedule(() => setPhase("hotkey"), 650);
              schedule(() => setPhase("toast"), 1050);
              schedule(startTyping, 1450);
            }, 2400);
          }
          return Math.min(next, digits.length);
        });
      }, 110);
    };

    clearAll();
    setPhase("idle");
    setTypedCount(0);

    schedule(() => setPhase("hotkey"), 650);
    schedule(() => setPhase("toast"), 1050);
    schedule(startTyping, 1450);

    return clearAll;
  }, [digits.length, prefersReducedMotion]);

  const showHotkey = phase === "hotkey" || phase === "toast" || phase === "typing" || phase === "done";
  const showToast = phase === "toast" || phase === "typing" || phase === "done";
  const showFilled = phase === "typing" || phase === "done";

  return (
    <div className="relative w-full max-w-lg rounded-lg border border-border bg-card overflow-hidden shadow-2xl shadow-primary/5">
      {/* Title bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[hsl(0,70%,45%)]" />
          <div className="w-3 h-3 rounded-full bg-[hsl(45,70%,45%)]" />
          <div className="w-3 h-3 rounded-full bg-[hsl(120,50%,40%)]" />
          <span className="ml-2 text-xs text-muted-foreground font-mono">login.example.com</span>
        </div>
        <span className="text-xs text-muted-foreground font-mono">See it work</span>
      </div>

      {/* Demo body */}
      <div className="relative p-4 font-mono text-sm leading-relaxed min-h-[220px]">
        <div className="scanlines" />

        {/* Fake browser chrome */}
        <div className="relative z-10 mb-4 rounded-md border border-border bg-secondary/40 px-3 py-2 flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-primary/50" />
          <div className="flex-1 truncate text-xs text-muted-foreground">https://login.example.com/verify</div>
          <div className="text-xs text-muted-foreground">⋯</div>
        </div>

        {/* Login card */}
        <div className="relative z-10 rounded-lg border border-border bg-background/40 p-4">
          <div className="text-foreground font-semibold">Enter OTP</div>
          <div className="mt-1 text-xs text-muted-foreground">
            We emailed you a 6-digit code. Press your hotkey — then paste.
          </div>

          <div className="mt-4 flex gap-2">
            {digits.map((_, idx) => {
              const filled = showFilled && idx < shownDigits.length;
              return (
                <div
                  key={idx}
                  className={[
                    "h-10 w-10 rounded-md border flex items-center justify-center",
                    "bg-card/30",
                    filled ? "border-primary/60 text-primary shadow-[0_0_0_1px_hsl(var(--primary)/0.15)]" : "border-input text-muted-foreground",
                  ].join(" ")}
                >
                  {filled ? shownDigits[idx] : ""}
                </div>
              );
            })}
            {/* Caret */}
            {!prefersReducedMotion && (
              <div
                className={[
                  "h-10 w-1 rounded-full",
                  phase === "typing" ? "bg-primary opacity-100" : "opacity-0",
                  "transition-opacity duration-300",
                ].join(" ")}
              />
            )}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              No tab switching. No waiting. <span className="text-foreground">Just paste.</span>
            </div>
            <div className="text-xs text-muted-foreground">Sign in →</div>
          </div>
        </div>

        {/* Hotkey badge */}
        <div className="relative z-10 mt-4 flex items-center gap-2">
          <div
            className={[
              "inline-flex items-center gap-2 px-3 py-1 rounded-md border font-mono text-xs",
              "bg-card/40 border-border",
              showHotkey ? "opacity-100 translate-y-0" : "opacity-0 translate-y-1",
              "transition-all duration-300",
            ].join(" ")}
          >
            <span className="text-muted-foreground">Hotkey</span>
            <span className="text-primary font-semibold">{HOTKEY}</span>
          </div>

          <div className="text-xs text-muted-foreground">
            {showHotkey ? "Fetching OTP from Gmail…" : "Press your hotkey to fetch the OTP."}
          </div>
        </div>

        {/* Clipboard toast */}
        <div
          className={[
            "absolute top-4 right-4 z-20",
            showToast ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-1",
            "transition-all duration-300",
          ].join(" ")}
          aria-hidden={!showToast}
        >
          <div className="rounded-md border border-primary/30 bg-card/80 backdrop-blur px-3 py-2 shadow-lg shadow-primary/10">
            <div className="text-xs text-primary font-semibold">Copied to clipboard</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              {OTP}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MagicMomentDemo;
