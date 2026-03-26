import { Link } from "react-router-dom";

type LogoMarkProps = {
  compact?: boolean;
};

const LogoGlyph = ({ className = "h-10 w-10" }: { className?: string }) => (
  <svg
    viewBox="0 0 120 120"
    aria-hidden="true"
    className={className}
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect
      x="24"
      y="36"
      width="72"
      height="68"
      rx="20"
      stroke="currentColor"
      strokeWidth="8"
      strokeLinecap="round"
      strokeDasharray="12 12"
    />
    <path
      d="M36 36V24C36 10.7 46.7 0 60 0C73.3 0 84 10.7 84 24V36"
      stroke="currentColor"
      strokeWidth="8"
      strokeLinecap="round"
    />
    <circle cx="60" cy="60" r="12" fill="currentColor" />
    <path d="M60 72V86" stroke="currentColor" strokeWidth="8" strokeLinecap="round" />
  </svg>
);

const LogoMark = ({ compact = false }: LogoMarkProps) => {
  const textSize = compact ? "text-lg" : "text-2xl md:text-3xl";

  return (
    <Link
      to="/"
      className={`inline-flex items-center ${compact ? "gap-3" : "gap-4"} text-primary hover:opacity-90 transition-opacity`}
    >
      <LogoGlyph className={compact ? "h-10 w-10" : "h-14 w-14"} />
      <span className={`font-mono font-extrabold tracking-tight ${textSize} text-primary`}>OTPILOT</span>
    </Link>
  );
};

export default LogoMark;
