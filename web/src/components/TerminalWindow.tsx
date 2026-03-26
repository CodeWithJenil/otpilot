import { useEffect, useRef, useState, useCallback } from "react";

const LINES = [
  { text: "$ otpilot setup", type: "command" as const, delay: 60 },
  { text: "✓ Credentials saved", type: "success" as const, delay: 30 },
  { text: "✓ Authentication successful!", type: "success" as const, delay: 30 },
  { text: "$ otpilot start", type: "command" as const, delay: 60 },
  { text: "Waiting...", type: "muted" as const, delay: 50 },
  { text: "", type: "blank" as const, delay: 0 },
  { text: "[Ctrl+Shift+O pressed]", type: "highlight" as const, delay: 40 },
  { text: "✓ Found OTP from Gmail", type: "success" as const, delay: 30 },
  { text: "✓ Copied: 847291", type: "success" as const, delay: 30 },
];

const TerminalWindow = () => {
  const [displayedLines, setDisplayedLines] = useState<{ text: string; type: string }[]>([]);
  const [currentLine, setCurrentLine] = useState(0);
  const [currentChar, setCurrentChar] = useState(0);
  const [showCursor, setShowCursor] = useState(true);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  const reset = useCallback(() => {
    setDisplayedLines([]);
    setCurrentLine(0);
    setCurrentChar(0);
  }, []);

  useEffect(() => {
    if (currentLine >= LINES.length) {
      timeoutRef.current = setTimeout(reset, 3000);
      return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); };
    }

    const line = LINES[currentLine];

    if (line.type === "blank") {
      timeoutRef.current = setTimeout(() => {
        setDisplayedLines(prev => [...prev, { text: "", type: "blank" }]);
        setCurrentLine(prev => prev + 1);
        setCurrentChar(0);
      }, 800);
      return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); };
    }

    if (currentChar === 0 && line.type !== "command") {
      // Non-command lines appear instantly after a short delay
      timeoutRef.current = setTimeout(() => {
        setDisplayedLines(prev => [...prev, { text: line.text, type: line.type }]);
        setCurrentLine(prev => prev + 1);
      }, 400);
      return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); };
    }

    if (currentChar < line.text.length) {
      timeoutRef.current = setTimeout(() => {
        setDisplayedLines(prev => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0 && updated[lastIdx].type === line.type && currentChar > 0) {
            updated[lastIdx] = { text: line.text.slice(0, currentChar + 1), type: line.type };
          } else {
            updated.push({ text: line.text.slice(0, currentChar + 1), type: line.type });
          }
          return updated;
        });
        setCurrentChar(prev => prev + 1);
      }, line.delay + Math.random() * 30);
      return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); };
    }

    // Line complete
    timeoutRef.current = setTimeout(() => {
      setCurrentLine(prev => prev + 1);
      setCurrentChar(0);
    }, 600);
    return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); };
  }, [currentLine, currentChar, reset]);

  // Cursor blink
  useEffect(() => {
    const interval = setInterval(() => setShowCursor(prev => !prev), 530);
    return () => clearInterval(interval);
  }, []);

  const getLineColor = (type: string) => {
    switch (type) {
      case "command": return "text-foreground";
      case "success": return "text-primary";
      case "highlight": return "text-primary font-semibold";
      case "muted": return "text-muted-foreground";
      default: return "text-foreground";
    }
  };

  return (
    <div className="relative w-full max-w-lg rounded-lg border border-border bg-card overflow-hidden shadow-2xl shadow-primary/5">
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <div className="w-3 h-3 rounded-full bg-[hsl(0,70%,45%)]" />
        <div className="w-3 h-3 rounded-full bg-[hsl(45,70%,45%)]" />
        <div className="w-3 h-3 rounded-full bg-[hsl(120,50%,40%)]" />
        <span className="ml-2 text-xs text-muted-foreground font-mono">otpilot</span>
      </div>

      {/* Terminal body */}
      <div ref={terminalRef} className="relative p-4 min-h-[220px] font-mono text-sm leading-relaxed">
        <div className="scanlines" />
        {displayedLines.map((line, i) => (
          <div key={i} className={`${getLineColor(line.type)} ${line.type === "blank" ? "h-4" : ""}`}>
            {line.text}
          </div>
        ))}
        {currentLine < LINES.length && (
          <span className={`text-primary ${showCursor ? "opacity-100" : "opacity-0"}`}>▋</span>
        )}
      </div>
    </div>
  );
};

export default TerminalWindow;
