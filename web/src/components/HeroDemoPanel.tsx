import { useState } from "react";
import MagicMomentDemo from "./MagicMomentDemo";
import TerminalWindow from "./TerminalWindow";

type TabKey = "demo" | "setup";

const HeroDemoPanel = () => {
  const [tab, setTab] = useState<TabKey>("demo");

  return (
    <div className="w-full max-w-lg">
      <div className="mb-3 inline-flex items-center gap-1 rounded-md border border-border bg-card/50 p-1">
        <button
          type="button"
          onClick={() => setTab("demo")}
          className={[
            "px-3 py-1.5 rounded-md font-mono text-xs transition-all duration-200",
            tab === "demo"
              ? "bg-primary/10 text-primary border border-primary/20 shadow-[0_0_0_1px_hsl(var(--primary)/0.06)]"
              : "text-muted-foreground hover:text-foreground",
          ].join(" ")}
          aria-pressed={tab === "demo"}
        >
          See it work
        </button>
        <button
          type="button"
          onClick={() => setTab("setup")}
          className={[
            "px-3 py-1.5 rounded-md font-mono text-xs transition-all duration-200",
            tab === "setup"
              ? "bg-primary/10 text-primary border border-primary/20 shadow-[0_0_0_1px_hsl(var(--primary)/0.06)]"
              : "text-muted-foreground hover:text-foreground",
          ].join(" ")}
          aria-pressed={tab === "setup"}
        >
          Set it up
        </button>
      </div>

      {tab === "demo" ? <MagicMomentDemo /> : <TerminalWindow />}
    </div>
  );
};

export default HeroDemoPanel;

